from dataclasses import dataclass
from enum import Enum

from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import (
    ModerationCase,
    Post,
    SocialProfile,
    Space,
    SpaceBan,
    SpaceJoinRequest,
    SpaceMembership,
    SpaceRule,
)
from .services import visible_posts_for


class CommunityCapability(str, Enum):
    REVIEW_JOIN_REQUESTS = "review-join-requests"
    INVITE_MEMBERS = "invite-members"
    MANAGE_MEMBERS = "manage-members"
    MANAGE_RULES = "manage-rules"
    MODERATE_CONTENT = "moderate-content"
    MANAGE_BANS = "manage-bans"
    PIN_CONTENT = "pin-content"
    PUBLISH_ANNOUNCEMENTS = "publish-announcements"
    MANAGE_ROLES = "manage-roles"
    TRANSFER_OWNERSHIP = "transfer-ownership"


_ROLE_CAPABILITIES: dict[str, frozenset[CommunityCapability]] = {
    SpaceMembership.Role.MEMBER: frozenset(),
    SpaceMembership.Role.MODERATOR: frozenset(
        {
            CommunityCapability.MODERATE_CONTENT,
            CommunityCapability.MANAGE_BANS,
            CommunityCapability.PIN_CONTENT,
        }
    ),
    SpaceMembership.Role.ADMIN: frozenset(
        {
            CommunityCapability.REVIEW_JOIN_REQUESTS,
            CommunityCapability.INVITE_MEMBERS,
            CommunityCapability.MANAGE_MEMBERS,
            CommunityCapability.MANAGE_RULES,
            CommunityCapability.MODERATE_CONTENT,
            CommunityCapability.MANAGE_BANS,
            CommunityCapability.PIN_CONTENT,
            CommunityCapability.PUBLISH_ANNOUNCEMENTS,
        }
    ),
    SpaceMembership.Role.OWNER: frozenset(CommunityCapability),
}


@dataclass(frozen=True, slots=True)
class CommunityCapabilityDecision:
    community_id: int
    profile_id: int | None
    capability: CommunityCapability
    effective_role: str | None
    local_eligible: bool
    identity_authoritative: bool
    subject_matches: bool
    authorized: bool
    reason: str
    platform_wide_authority: bool = False


def _has_active_space_ban(space: Space, profile: SocialProfile) -> bool:
    return (
        SpaceBan.objects.filter(
            space=space,
            profile=profile,
            state=SpaceBan.State.ACTIVE,
        )
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
        .exists()
    )


def _accepted_membership(space: Space, profile: SocialProfile) -> SpaceMembership | None:
    return (
        SpaceMembership.objects.filter(
            space=space,
            profile=profile,
            state=SpaceMembership.State.ACCEPTED,
        )
        .order_by("id")
        .first()
    )


def _effective_role(space: Space, profile: SocialProfile) -> str | None:
    if space.owner_id == profile.id:
        return SpaceMembership.Role.OWNER
    membership = _accepted_membership(space, profile)
    return membership.role if membership is not None else None


def community_visible_to(space: Space, profile: SocialProfile | None) -> bool:
    """Return whether a community surface may be disclosed to this viewer.

    Public communities are discoverable without membership. Private and
    invitation-only communities require accepted membership or ownership.
    An active community-local ban fails closed for all scoped community reads.

    This is a Social-domain read boundary. It does not establish GoreeCloud
    Identity, Privacy Shield, Wardveil Security, legal, age, or production
    authorization acceptance.
    """

    if space.kind != Space.Kind.COMMUNITY:
        return False

    if profile is not None and _has_active_space_ban(space, profile):
        return False

    if space.visibility == Space.Visibility.PUBLIC:
        return True

    if profile is None:
        return False

    if space.owner_id == profile.id:
        return True

    return _accepted_membership(space, profile) is not None


def communities_for(profile: SocialProfile | None) -> QuerySet[Space]:
    """Return communities discoverable to the supplied viewer."""

    communities = Space.objects.filter(kind=Space.Kind.COMMUNITY)

    if profile is None:
        return communities.filter(visibility=Space.Visibility.PUBLIC).order_by("name", "id")

    accepted_space_ids = SpaceMembership.objects.filter(
        profile=profile,
        state=SpaceMembership.State.ACCEPTED,
    ).values_list("space_id", flat=True)

    banned_space_ids = (
        SpaceBan.objects.filter(
            profile=profile,
            state=SpaceBan.State.ACTIVE,
        )
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
        .values_list("space_id", flat=True)
    )

    return (
        communities.filter(
            Q(visibility=Space.Visibility.PUBLIC)
            | Q(owner=profile)
            | Q(id__in=accepted_space_ids)
        )
        .exclude(id__in=banned_space_ids)
        .order_by("name", "id")
        .distinct()
    )


def community_posts_for(space: Space, profile: SocialProfile | None) -> QuerySet[Post]:
    """Return ordinary visible posts inside one community scope."""

    if not community_visible_to(space, profile):
        return Post.objects.none()
    return visible_posts_for(profile).filter(space=space).order_by("-created_at", "-id")


def community_rules_for(space: Space, profile: SocialProfile | None) -> QuerySet[SpaceRule]:
    """Return active ordered rules only when the community itself is visible."""

    if not community_visible_to(space, profile):
        return SpaceRule.objects.none()
    return SpaceRule.objects.filter(space=space, active=True).order_by("position", "id")


def community_capability_decision(
    *,
    space: Space,
    profile: SocialProfile | None,
    capability: CommunityCapability | str,
    actor_subject: str | None,
    identity_authoritative: bool,
) -> CommunityCapabilityDecision:
    """Evaluate a community-local privileged capability.

    Role membership supplies only Social-local eligibility. A positive
    authorization decision additionally requires an explicitly authoritative
    actor subject that exactly matches the profile's external Identity subject.

    The caller remains responsible for obtaining that authoritative Identity
    fact. This function does not authenticate a session or grant platform-wide
    authority.
    """

    try:
        requested = capability if isinstance(capability, CommunityCapability) else CommunityCapability(capability)
    except ValueError as exc:
        raise ValueError(f"Unsupported community capability: {capability}") from exc

    profile_id = profile.id if profile is not None else None

    if space.kind != Space.Kind.COMMUNITY:
        return CommunityCapabilityDecision(
            community_id=space.id,
            profile_id=profile_id,
            capability=requested,
            effective_role=None,
            local_eligible=False,
            identity_authoritative=identity_authoritative,
            subject_matches=False,
            authorized=False,
            reason="not-a-community",
        )

    if profile is None:
        return CommunityCapabilityDecision(
            community_id=space.id,
            profile_id=None,
            capability=requested,
            effective_role=None,
            local_eligible=False,
            identity_authoritative=identity_authoritative,
            subject_matches=False,
            authorized=False,
            reason="anonymous-actor",
        )

    if _has_active_space_ban(space, profile):
        return CommunityCapabilityDecision(
            community_id=space.id,
            profile_id=profile.id,
            capability=requested,
            effective_role=_effective_role(space, profile),
            local_eligible=False,
            identity_authoritative=identity_authoritative,
            subject_matches=actor_subject == profile.identity_subject,
            authorized=False,
            reason="active-community-ban",
        )

    role = _effective_role(space, profile)
    local_eligible = role is not None and requested in _ROLE_CAPABILITIES.get(role, frozenset())
    subject_matches = actor_subject == profile.identity_subject

    if role is None:
        reason = "accepted-membership-required"
    elif not local_eligible:
        reason = "role-does-not-permit-capability"
    elif not identity_authoritative:
        reason = "authoritative-identity-required"
    elif not subject_matches:
        reason = "identity-subject-mismatch"
    else:
        reason = "authorized"

    return CommunityCapabilityDecision(
        community_id=space.id,
        profile_id=profile.id,
        capability=requested,
        effective_role=role,
        local_eligible=local_eligible,
        identity_authoritative=identity_authoritative,
        subject_matches=subject_matches,
        authorized=local_eligible and identity_authoritative and subject_matches,
        reason=reason,
    )


def pending_join_requests_for(
    *,
    space: Space,
    actor_profile: SocialProfile,
    actor_subject: str | None,
    identity_authoritative: bool,
) -> QuerySet[SpaceJoinRequest]:
    """Return pending join requests only to an authorized community reviewer."""

    decision = community_capability_decision(
        space=space,
        profile=actor_profile,
        capability=CommunityCapability.REVIEW_JOIN_REQUESTS,
        actor_subject=actor_subject,
        identity_authoritative=identity_authoritative,
    )
    if not decision.authorized:
        raise PermissionDenied(decision.reason)

    return (
        SpaceJoinRequest.objects.filter(
            space=space,
            state=SpaceJoinRequest.State.PENDING,
        )
        .select_related("requester")
        .order_by("created_at", "id")
    )


def manageable_memberships_for(
    *,
    space: Space,
    actor_profile: SocialProfile,
    actor_subject: str | None,
    identity_authoritative: bool,
) -> QuerySet[SpaceMembership]:
    """Return community memberships only to an authorized member manager."""

    decision = community_capability_decision(
        space=space,
        profile=actor_profile,
        capability=CommunityCapability.MANAGE_MEMBERS,
        actor_subject=actor_subject,
        identity_authoritative=identity_authoritative,
    )
    if not decision.authorized:
        raise PermissionDenied(decision.reason)

    return SpaceMembership.objects.filter(space=space).select_related("profile").order_by("role", "profile__handle", "id")


def community_moderation_cases_for(
    *,
    space: Space,
    actor_profile: SocialProfile,
    actor_subject: str | None,
    identity_authoritative: bool,
) -> QuerySet[ModerationCase]:
    """Return active community moderation cases to an authorized moderator."""

    decision = community_capability_decision(
        space=space,
        profile=actor_profile,
        capability=CommunityCapability.MODERATE_CONTENT,
        actor_subject=actor_subject,
        identity_authoritative=identity_authoritative,
    )
    if not decision.authorized:
        raise PermissionDenied(decision.reason)

    return (
        ModerationCase.objects.filter(
            space=space,
            state__in=(ModerationCase.State.OPEN, ModerationCase.State.REVIEWING),
        )
        .select_related("post", "profile")
        .order_by("created_at", "id")
    )
