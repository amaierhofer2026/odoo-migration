import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestHelpdeskCategoryUser(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create test users
        cls.user_a = cls.env["res.users"].create(
            {
                "name": "CatUser A",
                "login": "test_catuser_a",
                "email": "catuser_a@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("base.group_user").id]),
                ],
            }
        )
        cls.user_b = cls.env["res.users"].create(
            {
                "name": "CatUser B",
                "login": "test_catuser_b",
                "email": "catuser_b@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("base.group_user").id]),
                ],
            }
        )
        cls.user_c = cls.env["res.users"].create(
            {
                "name": "CatUser C",
                "login": "test_catuser_c",
                "email": "catuser_c@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("base.group_user").id]),
                ],
            }
        )

        # Team with all users
        cls.team = cls.env["helpdesk.ticket.team"].create(
            {
                "name": "Test Team CatUsers",
                "user_ids": [
                    (6, 0, [cls.user_a.id, cls.user_b.id, cls.user_c.id])
                ],
            }
        )

        # Category with 2 users (A + B)
        cls.cat_ab = cls.env["helpdesk.ticket.category"].create(
            {
                "name": "Category AB",
                "user_ids": [(6, 0, [cls.user_a.id, cls.user_b.id])],
            }
        )

        # Category with 1 user (C)
        cls.cat_c = cls.env["helpdesk.ticket.category"].create(
            {
                "name": "Category C",
                "user_ids": [(6, 0, [cls.user_c.id])],
            }
        )

        # Category with no users
        cls.cat_none = cls.env["helpdesk.ticket.category"].create(
            {
                "name": "Category None",
            }
        )

        # Team for the assigned user to belong to
        cls.team_other = cls.env["helpdesk.ticket.team"].create(
            {
                "name": "Other Team",
                "user_ids": [
                    (6, 0, [cls.user_a.id, cls.user_b.id, cls.user_c.id])
                ],
            }
        )

        # Test partner for ticket
        cls.test_partner = cls.env["res.partner"].create(
            {"name": "Test Customer"}
        )

    # ---- CREATE TESTS ----

    def test_create_with_category_subscribes_all_users(self):
        """All category users become followers; user_id stays empty."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Subscribe All",
                "description": "<p>Test</p>",
                "category_id": self.cat_ab.id,
                "team_id": self.team.id,
            }
        )
        # Both users A and B should be followers
        self.assertIn(
            self.user_a.partner_id, ticket.message_partner_ids,
            "User A must be a follower",
        )
        self.assertIn(
            self.user_b.partner_id, ticket.message_partner_ids,
            "User B must be a follower",
        )
        # user_id must stay empty (no auto-assign)
        self.assertFalse(
            ticket.user_id,
            "user_id must NOT be auto-assigned",
        )

    def test_create_without_category_users(self):
        """Category without users — nothing happens."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "No Category Users",
                "description": "<p>Test</p>",
                "category_id": self.cat_none.id,
                "team_id": self.team.id,
            }
        )
        self.assertFalse(ticket.user_id)

    def test_create_manual_user_preserved(self):
        """Explicitly set user_id is never overridden."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Manual User",
                "description": "<p>Test</p>",
                "category_id": self.cat_ab.id,
                "team_id": self.team.id,
                "user_id": self.user_c.id,
            }
        )
        self.assertEqual(ticket.user_id, self.user_c)
        # Category users should still be followers
        self.assertIn(self.user_a.partner_id, ticket.message_partner_ids)
        self.assertIn(self.user_b.partner_id, ticket.message_partner_ids)

    # ---- WRITE TESTS ----

    def test_category_change_updates_followers(self):
        """Switching category from AB to C: A+B removed, C added."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Cat Change",
                "description": "<p>Test</p>",
                "category_id": self.cat_ab.id,
                "team_id": self.team.id,
            }
        )
        # Verify initial state
        self.assertIn(self.user_a.partner_id, ticket.message_partner_ids)
        self.assertIn(self.user_b.partner_id, ticket.message_partner_ids)

        # Switch to category C
        ticket.write({"category_id": self.cat_c.id})

        # Users A and B (from old category) should be removed
        self.assertNotIn(
            self.user_a.partner_id, ticket.message_partner_ids,
            "User A from old category must be removed",
        )
        self.assertNotIn(
            self.user_b.partner_id, ticket.message_partner_ids,
            "User B from old category must be removed",
        )
        # User C (from new category) should be added
        self.assertIn(
            self.user_c.partner_id, ticket.message_partner_ids,
            "User C from new category must be added",
        )

    def test_manual_user_survives_category_change(self):
        """Manually set user_id must never be removed on category change."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Manual Survives",
                "description": "<p>Test</p>",
                "category_id": self.cat_ab.id,
                "team_id": self.team.id,
                "user_id": self.user_c.id,
            }
        )
        # User C is both assigned user AND in new category C — test
        # that assigned user is never removed
        ticket.write({"category_id": self.cat_none.id})
        self.assertEqual(
            ticket.user_id, self.user_c,
            "Manually set user_id must survive category removal",
        )
        # Assigned user's partner should remain a follower
        self.assertIn(
            self.user_c.partner_id, ticket.message_partner_ids,
            "Assigned user must stay a follower",
        )

    def test_category_remove_does_not_delete_assigned_user(self):
        """Removing the category should not remove the assigned user."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Remove Cat",
                "description": "<p>Test</p>",
                "category_id": self.cat_ab.id,
                "team_id": self.team.id,
                "user_id": self.user_a.id,
            }
        )
        ticket.write({"category_id": False})
        self.assertEqual(ticket.user_id, self.user_a)
        # User A was both category user AND assigned user — must stay
        self.assertIn(
            self.user_a.partner_id, ticket.message_partner_ids,
            "Assigned user must remain a follower",
        )
        # User B (only a category follower) should be removed
        self.assertNotIn(
            self.user_b.partner_id, ticket.message_partner_ids,
            "Pure category follower must be removed",
        )

    def test_ticket_partner_not_removed_on_category_change(self):
        """Ticket partner should never be removed during category change."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Partner Protected",
                "description": "<p>Test</p>",
                "category_id": self.cat_ab.id,
                "team_id": self.team.id,
                "partner_id": self.user_a.partner_id.id,
            }
        )
        ticket.write({"category_id": self.cat_none.id})
        # User A is the ticket partner — must stay
        self.assertIn(
            self.user_a.partner_id, ticket.message_partner_ids,
            "Ticket partner must not be removed on category change",
        )

    def test_category_change_to_same_does_nothing(self):
        """Setting the same category is a no-op."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Same Cat",
                "description": "<p>Test</p>",
                "category_id": self.cat_ab.id,
                "team_id": self.team.id,
            }
        )
        followers_before = ticket.message_partner_ids
        ticket.write({"category_id": self.cat_ab.id})
        self.assertEqual(
            ticket.message_partner_ids, followers_before,
            "Followers must not change when category stays the same",
        )

    def test_create_with_partner_gets_both_followers(self):
        """Ticket with partner + category: partner is NOT removed."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Partner Plus Cat",
                "description": "<p>Test</p>",
                "category_id": self.cat_ab.id,
                "team_id": self.team.id,
                "partner_id": self.test_partner.id,
            }
        )
        self.assertIn(self.user_a.partner_id, ticket.message_partner_ids)
        self.assertIn(self.user_b.partner_id, ticket.message_partner_ids)
        self.assertIn(self.test_partner, ticket.message_partner_ids)

    def test_single_user_category(self):
        """Category with one user: only that user is subscribed."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Single User Cat",
                "description": "<p>Test</p>",
                "category_id": self.cat_c.id,
                "team_id": self.team.id,
            }
        )
        self.assertIn(self.user_c.partner_id, ticket.message_partner_ids)
        self.assertNotIn(self.user_a.partner_id, ticket.message_partner_ids)
        self.assertFalse(ticket.user_id)
