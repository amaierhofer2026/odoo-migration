import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestHelpdeskCategoryUser(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create test users
        cls.user_assignee = cls.env["res.users"].create(
            {
                "name": "Test Assignee",
                "login": "test_assignee",
                "email": "assignee@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("base.group_user").id]),
                ],
            }
        )
        cls.user_other = cls.env["res.users"].create(
            {
                "name": "Test Other",
                "login": "test_other",
                "email": "other@example.com",
                "groups_id": [
                    (6, 0, [cls.env.ref("base.group_user").id]),
                ],
            }
        )

        # Create a helpdesk team with both users
        cls.team = cls.env["helpdesk.ticket.team"].create(
            {
                "name": "Test Team",
                "user_ids": [(6, 0, [cls.user_assignee.id, cls.user_other.id])],
            }
        )

        # Create a category with assigned user
        cls.category = cls.env["helpdesk.ticket.category"].create(
            {
                "name": "Test Category",
                "user_id": cls.user_assignee.id,
            }
        )

        # Create a category without assigned user
        cls.category_no_user = cls.env["helpdesk.ticket.category"].create(
            {
                "name": "No User Category",
            }
        )

        # Team without the assignee
        cls.team_other = cls.env["helpdesk.ticket.team"].create(
            {
                "name": "Other Team",
                "user_ids": [(6, 0, [cls.user_other.id])],
            }
        )

    # ---- CREATE TESTS ----

    def test_create_ticket_auto_assign(self):
        """Ticket created with category should auto-assign category user."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category.id,
                "team_id": self.team.id,
            }
        )
        self.assertEqual(ticket.user_id, self.user_assignee)
        self.assertIn(
            self.user_assignee.partner_id, ticket.message_partner_ids,
            "Category user should be subscribed as follower",
        )

    def test_create_ticket_no_category_user(self):
        """Ticket with category lacking a user should not auto-assign."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category_no_user.id,
                "team_id": self.team.id,
            }
        )
        self.assertFalse(ticket.user_id)

    def test_create_ticket_manual_user_preserved(self):
        """Explicitly set user_id should not be overridden by category."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category.id,
                "team_id": self.team.id,
                "user_id": self.user_other.id,
            }
        )
        self.assertEqual(ticket.user_id, self.user_other)

    def test_create_ticket_no_team(self):
        """Ticket without team: auto-assign from category should still work."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category.id,
            }
        )
        self.assertEqual(ticket.user_id, self.user_assignee)

    def test_create_ticket_user_not_in_team(self):
        """Auto-assign should skip when category user is not a team member."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category.id,
                "team_id": self.team_other.id,
            }
        )
        self.assertFalse(ticket.user_id)

    # ---- WRITE TESTS ----

    def test_write_category_change_auto_assign(self):
        """Changing category on existing ticket should auto-assign."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category_no_user.id,
                "team_id": self.team.id,
            }
        )
        self.assertFalse(ticket.user_id)

        ticket.write({"category_id": self.category.id})
        self.assertEqual(ticket.user_id, self.user_assignee)
        self.assertIn(
            self.user_assignee.partner_id, ticket.message_partner_ids,
        )

    def test_write_category_change_preserves_manual_user(self):
        """Category change should NOT override a manually set user."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category_no_user.id,
                "team_id": self.team.id,
                "user_id": self.user_other.id,
            }
        )
        ticket.write({"category_id": self.category.id})
        self.assertEqual(ticket.user_id, self.user_other)

    def test_write_user_explicitly_set(self):
        """When user_id is explicitly set together with category, no override."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category_no_user.id,
                "team_id": self.team.id,
            }
        )
        ticket.write(
            {"category_id": self.category.id, "user_id": self.user_other.id}
        )
        self.assertEqual(ticket.user_id, self.user_other)

    def test_write_category_user_not_in_team(self):
        """Category change to user not in team should skip auto-assign."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category_no_user.id,
                "team_id": self.team_other.id,
            }
        )
        ticket.write({"category_id": self.category.id})
        self.assertFalse(
            ticket.user_id,
            "Should not auto-assign when category user is not in team",
        )

    def test_write_category_remove_does_nothing(self):
        """Removing the category should not touch user_id."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category.id,
                "team_id": self.team.id,
            }
        )
        self.assertEqual(ticket.user_id, self.user_assignee)

        ticket.write({"category_id": False})
        # User should remain assigned — removing category doesn't unassign
        self.assertEqual(ticket.user_id, self.user_assignee)

    # ---- FOLLOWER TESTS ----

    def test_subscribe_category_user(self):
        """Category user should be added as follower."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category.id,
                "team_id": self.team.id,
            }
        )
        self.assertIn(
            self.user_assignee.partner_id,
            ticket.message_partner_ids,
            "Category user must be a follower for email notifications",
        )

    def test_manual_user_no_duplicate_follower(self):
        """Manually set user from category should not create duplicate follows."""
        ticket = self.env["helpdesk.ticket"].create(
            {
                "name": "Test Ticket",
                "description": "Test",
                "category_id": self.category.id,
                "team_id": self.team.id,
                "user_id": self.user_assignee.id,
            }
        )
        # Count occurrences of the partner in followers
        follower_count = ticket.message_partner_ids.filtered(
            lambda p: p == self.user_assignee.partner_id
        )
        self.assertEqual(
            len(follower_count),
            1,
            "User should only be subscribed once",
        )
