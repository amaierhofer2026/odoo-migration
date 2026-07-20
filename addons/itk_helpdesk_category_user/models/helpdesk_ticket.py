import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.onchange("category_id", "team_id")
    def _onchange_category_user(self):
        """Auto-assign user from category when category or team changes."""
        self.ensure_one()
        if self.category_id and self.category_id.user_id:
            category_user = self.category_id.user_id
            team = self.team_id
            # Only auto-assign if no user is set or the current user
            # is being cleared by a team change
            if not self.user_id or (
                team and self._origin.user_id not in team.user_ids
            ):
                if team and category_user not in team.user_ids:
                    # Category user is not a team member — skip auto-assign
                    return
                self.user_id = category_user

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)
        for ticket, vals in zip(tickets, vals_list):
            if (
                "user_id" not in vals
                and ticket.category_id
                and ticket.category_id.user_id
            ):
                ticket._auto_assign_from_category()
        return tickets

    def write(self, vals):
        # Auto-assign from category: when category_id changes and user_id
        # is NOT being set explicitly, assign the category user.
        category_id_val = vals.get("category_id")
        if category_id_val and "user_id" not in vals:
            for ticket in self:
                new_category_id = (
                    category_id_val
                    if isinstance(category_id_val, int)
                    else ticket.category_id.id
                )
                if new_category_id == ticket.category_id.id:
                    continue
                category = self.env["helpdesk.ticket.category"].browse(
                    new_category_id
                )
                if category.user_id:
                    team = self.env["helpdesk.ticket.team"].browse(
                        vals.get("team_id", ticket.team_id.id)
                    )
                    if not team or category.user_id in team.user_ids:
                        vals = dict(vals)
                        vals["user_id"] = category.user_id.id
        result = super().write(vals)
        # Subscribe category user as follower when category changed
        if category_id_val and "user_id" not in vals:
            for ticket in self:
                if ticket.category_id and ticket.category_id.user_id:
                    if ticket.user_id == ticket.category_id.user_id:
                        ticket._subscribe_category_user(
                            ticket.category_id.user_id
                        )
        return result

    def _auto_assign_from_category(self):
        """Assign the category user and subscribe them as follower."""
        self.ensure_one()
        category = self.category_id
        category_user = category.user_id
        team = self.team_id
        if team and category_user not in team.user_ids:
            _logger.info(
                "Category %(cat)s user %(user)s is not a member of team %(team)s "
                "— skipping auto-assign for ticket %(ticket)s",
                {
                    "cat": category.display_name,
                    "user": category_user.display_name,
                    "team": team.display_name,
                    "ticket": self.display_name,
                },
            )
            return False
        self.write({"user_id": category_user.id})
        self._subscribe_category_user(category_user)
        return True

    def _subscribe_category_user(self, user):
        """Subscribe the user as a follower to receive email notifications."""
        self.ensure_one()
        if user.partner_id not in self.message_partner_ids:
            self.message_subscribe(partner_ids=[user.partner_id.id])
