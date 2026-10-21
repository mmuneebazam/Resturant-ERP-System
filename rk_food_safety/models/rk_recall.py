# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class RkRecall(models.Model):
    """Trace a lot to every outlet, then prove you told them."""

    _name = "rk.recall"
    _description = "Product recall"
    _order = "date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default=lambda self: _("New"), readonly=True, copy=False, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    product_id = fields.Many2one("product.product", required=True, ondelete="restrict")
    lot_reference = fields.Char(string="Lot / batch")
    supplier_reference = fields.Char()
    reason = fields.Selection(
        [("supplier", "Supplier notice"), ("micro", "Microbiological"),
         ("foreign", "Foreign body"), ("allergen", "Undeclared allergen"),
         ("quality", "Quality complaint"), ("regulatory", "Regulatory")],
        required=True, default="supplier",
    )
    description = fields.Text()
    severity = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium", required=True
    )
    affected_outlet_ids = fields.Many2many(
        "rk.outlet", "rk_recall_outlet_rel", "recall_id", "outlet_id", string="Affected outlets"
    )
    state = fields.Selection(
        [("draft", "Draft"), ("open", "Open"), ("closed", "Closed"), ("cancelled", "Cancelled")],
        default="draft", required=True, tracking=True,
    )
    action_taken = fields.Text()
    closed_on = fields.Datetime(readonly=True, copy=False)
    recalled_qty = fields.Float(string="Recalled qty")
    response_hours = fields.Float(compute="_compute_response", string="Hours to close")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rk.recall") or _("New")
        return super().create(vals_list)

    @api.depends("closed_on", "date")
    def _compute_response(self):
        for recall in self:
            recall.response_hours = (
                (recall.closed_on - fields.Datetime.to_datetime(recall.date)).total_seconds() / 3600.0
                if recall.closed_on else 0.0
            )

    def action_trace(self):
        """Suggest every outlet that received stock of this product recently."""
        for recall in self:
            moves = self.env["stock.move"].search(
                [
                    ("product_id", "=", recall.product_id.id),
                    ("state", "=", "done"),
                    ("location_dest_id.usage", "=", "internal"),
                ],
                limit=500,
            )
            locations = moves.mapped("location_dest_id")
            outlets = self.env["rk.outlet"].search([("warehouse_id", "!=", False)])
            recall.affected_outlet_ids = outlets.filtered(
                lambda o: o._rk_stock_location() and o._rk_stock_location() in locations
            )
        return True

    def action_open(self):
        self.write({"state": "open"})
        for recall in self:
            recall.message_post(
                body=_("Recall opened for %(product)s lot %(lot)s — %(count)s outlet(s) affected.",
                       product=recall.product_id.display_name,
                       lot=recall.lot_reference or _("n/a"),
                       count=len(recall.affected_outlet_ids))
            )
        return True

    def action_close(self):
        self.write({"state": "closed", "closed_on": fields.Datetime.now()})
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})
        return True
