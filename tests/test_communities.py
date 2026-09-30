from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone

from social.community import (
    CommunityCapability,
    communities_for,
    community_capability_decision,
    community_moderation_cases_for,
    community_posts_for,
    community_rules_for,
    manageable_memberships_for,
    pending_join_requests_for,
)
from social.models import (
    ModerationCase,
    Post,
    SocialProfile,
    Space,
    SpaceBan,
    SpaceJoinRequest,
    SpaceMembership,
    SpaceRule,
)


class CommunityGovernanceTests(TestCase):
    def setUp(self):
        self.owner = SocialProfile.objects.create(
            identity_subject="identity:owner",
            handle="community_owner",
            display_name="Community Owner",
        )
        self.admin = SocialProfile.objects.create(
            identity_subject="identity:admin",
            handle="community_admin",
            display_name="Community Admin",
        )
        self.moderator = SocialProfile.objects.create(
            identity_subject="identity:moderator",
            handle="community_mod",
            display_name="Community Moderator",
        )
        self.member = SocialProfile.objects.create(
            identity_subject="identity:member",
            handle="community_member",
            display_name="Community Member",
        )
        self.outsider = SocialProfile.objects.create(
            identity_subject="identity:outsider",
            handle="community_outsider",
            display_name="Community Outsider",
        )

        self.public = Space.objects.create(
            kind=Space.Kind.COMMUNITY,
            slug="public-community",
            name="Public Community",
            visibility=Space.Visibility.PUBLIC,
            owner=self.owner,
        )
        self.private = Space.objects.create(
            kind=Space.Kind.COMMUNITY,
            slug="private-community",
            name="Private Community",
            visibility=Space.Visibility.PRIVATE,
            owner=self.owner,
        )
        self.group = Space.objects.create(
            kind=Space.Kind.GROUP,
            slug="ordinary-group",
            name="Ordinary Group",
            visibility=Space.Visibility.PUBLIC,
            owner=self.owner,
        )

        SpaceMembership.objects.create(
            space=self.public,
            profile=self.admin,
            role=SpaceMembership.Role.ADMIN,
            state=SpaceMembership.State.ACCEPTED,
        )
        SpaceMembership.objects.create(
            space=self.public,
            profile=self.moderator,
            role=SpaceMembership.Role.MODERATOR,
            state=SpaceMembership.State.ACCEPTED,
        )
        SpaceMembership.objects.create(
            space=self.public,
            profile=self.member,
            role=SpaceMembership.Role.MEMBER,
            state=SpaceMembership.State.ACCEPTED,
        )
        SpaceMembership.objects.create(
            space=self.private,
            profile=self.member,
            role=SpaceMembership.Role.MEMBER,
            state=SpaceMembership.State.ACCEPTED,
        )

    def test_anonymous_discovery_contains_public_communities_only(self):
        ids = set(communities_for(None).values_list("id", flat=True))
        self.assertEqual(ids, {self.public.id})

    def test_member_discovery_includes_private_membership(self):
        ids = set(communities_for(self.member).values_list("id", flat=True))
        self.assertEqual(ids, {self.public.id, self.private.id})

    def test_group_is_not_returned_by_community_discovery(self):
        ids = set(communities_for(self.owner).values_list("id", flat=True))
        self.assertNotIn(self.group.id, ids)

    def test_active_ban_removes_community_from_scoped_discovery(self):
        SpaceBan.objects.create(
            space=self.public,
            profile=self.member,
            imposed_by_subject="identity:admin",
        )
        ids = set(communities_for(self.member).values_list("id", flat=True))
        self.assertNotIn(self.public.id, ids)

    def test_expired_ban_does_not_remove_community_from_discovery(self):
        SpaceBan.objects.create(
            space=self.public,
            profile=self.member,
            imposed_by_subject="identity:admin",
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        ids = set(communities_for(self.member).values_list("id", flat=True))
        self.assertIn(self.public.id, ids)

    def test_private_community_feed_fails_closed_for_outsider(self):
        Post.objects.create(
            author=self.owner,
            space=self.private,
            audience=Post.Audience.PUBLIC,
            body="private community public-audience post",
        )
        self.assertFalse(community_posts_for(self.private, self.outsider).exists())

    def test_public_community_anonymous_feed_returns_only_public_audience_posts(self):
        public_post = Post.objects.create(
            author=self.owner,
            space=self.public,
            audience=Post.Audience.PUBLIC,
            body="public",
        )
        Post.objects.create(
            author=self.owner,
            space=self.public,
            audience=Post.Audience.SPACE,
            body="members only",
        )
        ids = set(community_posts_for(self.public, None).values_list("id", flat=True))
        self.assertEqual(ids, {public_post.id})

    def test_accepted_member_can_read_space_audience_post(self):
        post = Post.objects.create(
            author=self.owner,
            space=self.private,
            audience=Post.Audience.SPACE,
            body="member post",
        )
        ids = set(community_posts_for(self.private, self.member).values_list("id", flat=True))
        self.assertEqual(ids, {post.id})

    def test_active_ban_hides_all_scoped_community_posts(self):
        Post.objects.create(
            author=self.owner,
            space=self.public,
            audience=Post.Audience.PUBLIC,
            body="public",
        )
        SpaceBan.objects.create(
            space=self.public,
            profile=self.member,
            imposed_by_subject="identity:admin",
        )
        self.assertFalse(community_posts_for(self.public, self.member).exists())

    def test_rules_are_visible_only_with_community_visibility(self):
        active = SpaceRule.objects.create(space=self.private, title="Be kind", position=0, active=True)
        SpaceRule.objects.create(space=self.private, title="Retired", position=1, active=False)

        member_ids = list(community_rules_for(self.private, self.member).values_list("id", flat=True))
        outsider_ids = list(community_rules_for(self.private, self.outsider).values_list("id", flat=True))

        self.assertEqual(member_ids, [active.id])
        self.assertEqual(outsider_ids, [])

    def test_owner_receives_owner_capabilities_without_membership_row(self):
        decision = community_capability_decision(
            space=self.public,
            profile=self.owner,
            capability=CommunityCapability.TRANSFER_OWNERSHIP,
            actor_subject=self.owner.identity_subject,
            identity_authoritative=True,
        )
        self.assertTrue(decision.authorized)
        self.assertEqual(decision.effective_role, SpaceMembership.Role.OWNER)
        self.assertFalse(decision.platform_wide_authority)

    def test_moderator_capability_is_space_scoped_and_bounded(self):
        moderate = community_capability_decision(
            space=self.public,
            profile=self.moderator,
            capability=CommunityCapability.MODERATE_CONTENT,
            actor_subject=self.moderator.identity_subject,
            identity_authoritative=True,
        )
        transfer = community_capability_decision(
            space=self.public,
            profile=self.moderator,
            capability=CommunityCapability.TRANSFER_OWNERSHIP,
            actor_subject=self.moderator.identity_subject,
            identity_authoritative=True,
        )
        self.assertTrue(moderate.authorized)
        self.assertFalse(transfer.authorized)
        self.assertEqual(transfer.reason, "role-does-not-permit-capability")

    def test_role_label_does_not_authorize_without_identity_authority(self):
        decision = community_capability_decision(
            space=self.public,
            profile=self.admin,
            capability=CommunityCapability.MANAGE_MEMBERS,
            actor_subject=self.admin.identity_subject,
            identity_authoritative=False,
        )
        self.assertTrue(decision.local_eligible)
        self.assertFalse(decision.authorized)
        self.assertEqual(decision.reason, "authoritative-identity-required")

    def test_identity_subject_must_match_profile(self):
        decision = community_capability_decision(
            space=self.public,
            profile=self.admin,
            capability=CommunityCapability.MANAGE_MEMBERS,
            actor_subject="identity:someone-else",
            identity_authoritative=True,
        )
        self.assertFalse(decision.authorized)
        self.assertEqual(decision.reason, "identity-subject-mismatch")

    def test_active_ban_denies_privileged_capability(self):
        SpaceBan.objects.create(
            space=self.public,
            profile=self.moderator,
            imposed_by_subject="identity:owner",
        )
        decision = community_capability_decision(
            space=self.public,
            profile=self.moderator,
            capability=CommunityCapability.MODERATE_CONTENT,
            actor_subject=self.moderator.identity_subject,
            identity_authoritative=True,
        )
        self.assertFalse(decision.authorized)
        self.assertEqual(decision.reason, "active-community-ban")

    def test_group_role_does_not_create_community_authority(self):
        SpaceMembership.objects.create(
            space=self.group,
            profile=self.admin,
            role=SpaceMembership.Role.ADMIN,
            state=SpaceMembership.State.ACCEPTED,
        )
        decision = community_capability_decision(
            space=self.group,
            profile=self.admin,
            capability=CommunityCapability.MANAGE_MEMBERS,
            actor_subject=self.admin.identity_subject,
            identity_authoritative=True,
        )
        self.assertFalse(decision.authorized)
        self.assertEqual(decision.reason, "not-a-community")

    def test_pending_join_requests_require_authorized_reviewer(self):
        pending = SpaceJoinRequest.objects.create(space=self.public, requester=self.outsider)
        resolved_profile = SocialProfile.objects.create(
            identity_subject="identity:resolved",
            handle="resolved_user",
            display_name="Resolved",
        )
        SpaceJoinRequest.objects.create(
            space=self.public,
            requester=resolved_profile,
            state=SpaceJoinRequest.State.DECLINED,
        )

        ids = list(
            pending_join_requests_for(
                space=self.public,
                actor_profile=self.admin,
                actor_subject=self.admin.identity_subject,
                identity_authoritative=True,
            ).values_list("id", flat=True)
        )
        self.assertEqual(ids, [pending.id])

        with self.assertRaises(PermissionDenied):
            pending_join_requests_for(
                space=self.public,
                actor_profile=self.moderator,
                actor_subject=self.moderator.identity_subject,
                identity_authoritative=True,
            )

    def test_manageable_memberships_require_admin_or_owner(self):
        ids = set(
            manageable_memberships_for(
                space=self.public,
                actor_profile=self.admin,
                actor_subject=self.admin.identity_subject,
                identity_authoritative=True,
            ).values_list("profile_id", flat=True)
        )
        self.assertEqual(ids, {self.admin.id, self.moderator.id, self.member.id})

        with self.assertRaises(PermissionDenied):
            manageable_memberships_for(
                space=self.public,
                actor_profile=self.member,
                actor_subject=self.member.identity_subject,
                identity_authoritative=True,
            )

    def test_moderation_queue_is_space_scoped(self):
        case = ModerationCase.objects.create(
            profile=self.outsider,
            space=self.public,
            opened_by_subject=self.moderator.identity_subject,
            reason="community review",
        )
        ModerationCase.objects.create(
            profile=self.outsider,
            space=self.private,
            opened_by_subject=self.owner.identity_subject,
            reason="other community",
        )

        ids = list(
            community_moderation_cases_for(
                space=self.public,
                actor_profile=self.moderator,
                actor_subject=self.moderator.identity_subject,
                identity_authoritative=True,
            ).values_list("id", flat=True)
        )
        self.assertEqual(ids, [case.id])
