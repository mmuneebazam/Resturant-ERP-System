# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RkParLevel(models.Model):
    """How much of an item an outlet should always have."""

    _name = "rk.par.level"
    _description = "Par level"
    _order = "outlet_id, product_id"
    _check_company_auto = True

    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one(
        "product.product", required=True, ondelete="cascade", domain=[("purchase_ok", "=", True)]
    )
    uom_id = fields.Many2one(related="product_id.uom_id", string="UoM")
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    par_qty = fields.Float(string="Par (target stock)", required=True, default=0.0)
    min_qty = fields.Float(string="Minimum", default=0.0)
    # Stored together: a list view filters on `below_par` and sorts on the rest,
    # and Odoo wants one storage policy per compute method.
    qty_on_hand = fields.Float(compute="_compute_suggestion", store=True, string="On hand")
    qty_incoming = fields.Float(compute="_compute_suggestion", store=True, string="On order")
    suggested_qty = fields.Float(compute="_compute_suggestion", store=True, string="Suggested indent")
    below_par = fields.Boolean(compute="_compute_suggestion", store=True, string="Below par")
    average_daily_usage = fields.Float(compute="_compute_suggestion", store=True, string="Avg daily usage")
    days_cover = fields.Float(compute="_compute_suggestion", store=True, string="Days cover")
    active = fields.Boolean(default=True)

    _par_uniq = models.Constraint(
        "UNIQUE(outlet_id, product_id)", "One par level per outlet and product."
    )

    @api.depends("par_qty", "min_qty", "outlet_id", "product_id")
    def _compute_suggestion(self):
        Moves = self.env["stock.move"]
        since = fields.Date.subtract(fields.Date.today(), days=14)
        for par in self:
            location = par.outlet_id._rk_stock_location()
            on_hand = incoming = usage = 0.0
            if location and par.product_id:
                on_hand = par.product_id.with_context(location=location.id).qty_available
                incoming = sum(
                    Moves.search(
                        [
                            ("product_id", "=", par.product_id.id),
                            ("state", "not in", ("done", "cancel")),
                            ("location_dest_id", "child_of", location.id),
                        ]
                    ).mapped("product_uom_qty")
                )
                done = Moves.search(
                    [
                        ("product_id", "=", par.product_id.id),
                        ("state", "=", "done"),
                        ("location_dest_id", "child_of", location.id),
                        ("date", ">=", since),
                    ]
                )
                usage = sum(done.mapped("quantity")) / 14.0
            par.qty_on_hand = on_hand
            par.qty_incoming = incoming
            par.average_daily_usage = usage
            par.days_cover = (on_hand / usage) if usage else 0.0
            par.suggested_qty = max(0.0, (par.par_qty or 0.0) - on_hand - incoming)
            par.below_par = par.suggested_qty > 0
