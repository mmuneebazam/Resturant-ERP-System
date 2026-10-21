# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RkProductionPlan(models.Model):
    """All approved indents for one day, collapsed into one production run."""

    _name = "rk.production.plan"
    _description = "Production plan"
    _order = "date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default=lambda self: _("New"), readonly=True, copy=False, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    kitchen_id = fields.Many2one(
        "rk.outlet", string="Kitchen", required=True, ondelete="restrict",
        domain=[("format", "=", "central_kitchen")],
    )
    company_id = fields.Many2one(related="kitchen_id.company_id", store=True)
    indent_ids = fields.Many2many("rk.indent", "rk_plan_indent_rel", "plan_id", "indent_id", string="Indents")
    line_ids = fields.One2many("rk.production.plan.line", "plan_id", string="Items", copy=False)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("produced", "Produced"), ("cancelled", "Cancelled")],
        default="draft", required=True, tracking=True,
    )
    total_qty = fields.Float(compute="_compute_total", string="Planned qty")
    notes = fields.Text()

    @api.depends("line_ids.qty")
    def _compute_total(self):
        for plan in self:
            plan.total_qty = sum(plan.line_ids.mapped("qty"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rk.production.plan") or _("New")
        return super().create(vals_list)

    def action_consolidate(self):
        """Collapse every approved indent of the day into one line per product."""
        self.ensure_one()
        self.line_ids.unlink()
        indents = self.indent_ids or self.env["rk.indent"].search(
            [("date_required", "=", self.date), ("state", "=", "approved")]
        )
        totals = defaultdict(float)
        for line in indents.line_ids:
            totals[line.product_id] += line.qty_approved or line.qty_requested
        commands = []
        for product, qty in totals.items():
            bom = self.env["mrp.bom"]._bom_find(product, company_id=self.company_id.id)[product]
            commands.append(
                (0, 0, {
                    "product_id": product.id,
                    "qty": qty,
                    "bom_id": bom.id if bom else False,
                })
            )
        self.write({"line_ids": commands, "indent_ids": [(6, 0, indents.ids)]})
        indents.write({"production_plan_id": self.id, "state": "planned"})
        return True

    def action_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def action_create_manufacturing_orders(self):
        """One manufacturing order per planned item that has a BOM."""
        self.ensure_one()
        if self.state == "draft":
            raise UserError(_("Confirm the plan before ordering production."))
        location = self.kitchen_id._rk_stock_location()
        warehouse = self.kitchen_id.warehouse_id
        for line in self.line_ids.filtered(lambda l: l.bom_id and not l.mo_id):
            mo = self.env["mrp.production"].create(
                {
                    "product_id": line.product_id.id,
                    "bom_id": line.bom_id.id,
                    "product_qty": line.qty,
                    "product_uom_id": line.product_id.uom_id.id,
                    "location_src_id": location.id if location else False,
                    "location_dest_id": location.id if location else False,
                    "picking_type_id": warehouse.manu_type_id.id if warehouse else False,
                    "origin": self.name,
                    "date_start": fields.Datetime.now(),
                }
            )
            line.mo_id = mo.id
        self.state = "produced"
        return True


class RkProductionPlanLine(models.Model):
    _name = "rk.production.plan.line"
    _description = "Production plan line"

    plan_id = fields.Many2one("rk.production.plan", required=True, ondelete="cascade", index=True)
    product_id = fields.Many2one("product.product", required=True, ondelete="restrict")
    uom_id = fields.Many2one(related="product_id.uom_id", string="UoM")
    qty = fields.Float(required=True, default=0.0)
    bom_id = fields.Many2one("mrp.bom", string="BOM")
    mo_id = fields.Many2one("mrp.production", string="Manufacturing order", readonly=True)
    mo_state = fields.Selection(related="mo_id.state", string="MO status")

    def action_open_mo(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "mrp.production",
            "res_id": self.mo_id.id,
            "view_mode": "form",
        }
