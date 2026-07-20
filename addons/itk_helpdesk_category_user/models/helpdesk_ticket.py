from odoo import _, api, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)
        for ticket, vals in zip(tickets, vals_list):
            if ticket.category_id and ticket.category_id.user_ids:
                ticket._subscribe_category_users()
        return tickets

    def write(self, vals):
        # Track category change for follower management
        category_changed = "category_id" in vals
        old_categories = {}
        if category_changed:
            for ticket in self:
                old_categories[ticket.id] = ticket.category_id

        result = super().write(vals)

        if category_changed:
            for ticket in self:
                old_cat = old_categories.get(ticket.id)
                new_cat = ticket.category_id
                if old_cat != new_cat:
                    ticket._update_category_followers(old_cat, new_cat)

        return result

    # ---------------------------------------------------------------
    # Follower helpers
    # ---------------------------------------------------------------

    def _subscribe_category_users(self):
        """Subscribe all category users as followers (idempotent)."""
        self.ensure_one()
        category_users = self.category_id.user_ids
        if not category_users:
            return
        partners = category_users.mapped("partner_id")
        new_partners = partners - self.message_partner_ids
        if new_partners:
            self.message_subscribe(partner_ids=new_partners.ids)

    def _update_category_followers(self, old_category, new_category):
        """Safely transition followers when category changes.

        - Remove followers that came ONLY from the old category
          (unless they are the assigned user or the ticket partner).
        - Add followers from the new category.
        - Never touch ``user_id`` (manual assignment).
        """
        self.ensure_one()

        old_users = old_category.user_ids if old_category else self.env["res.users"]
        new_users = new_category.user_ids if new_category else self.env["res.users"]

        old_partners = old_users.mapped("partner_id")
        new_partners = new_users.mapped("partner_id")

        # Keepers: assigned user and ticket partner (never auto-remove)
        keep_partners = self.env["res.partner"]
        if self.user_id:
            keep_partners |= self.user_id.partner_id
        if self.partner_id:
            keep_partners |= self.partner_id

        # Remove old-category partners that are NOT in the new category
        # AND are not protected keepers
        to_remove = old_partners - new_partners - keep_partners
        if to_remove:
            self.message_unsubscribe(partner_ids=to_remove.ids)

        # Add new-category partners not yet following
        to_add = new_partners - self.message_partner_ids
        if to_add:
            self.message_subscribe(partner_ids=to_add.ids)
