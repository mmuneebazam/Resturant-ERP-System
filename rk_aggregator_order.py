# -*- coding: utf-8 -*-
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class RkAggregatorPlatform(models.Model):
    _name = "rk.aggregator.platform"
    _description = "Aggregator platform"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    channel_id = fields.Many2one("rk.channel", string="Channel", ondelete="restrict")
    commission_pct = fields.Float(string="Commission %", default=18.0)
    settlement_cycle_days = fields.Integer(string="Settlement cycle (days)", default=7)
    active = fields.Boolean(default=True)
    color = fields.Integer(default=0)

    _platform_code_uniq = models.Constraint("UNIQUE(code)", "The platform code must be unique.")


class RkAggregatorOrder(models.Model):
    """One order as received from a platform, and its POS counterpart."""

    _name = "rk.aggregator.order"
    _description = "Aggregator order"
    _order = "received_at desc, id desc"
    _inherit = ["mail.thread"]

    name = fields.Char(related="external_ref", string="Platform reference")
    platform_id = fields.Many2one("rk.aggregator.platform", required=True, ondelete="restrict", index=True)
    channel_id = fields.Many2one(related="platform_id.channel_id", string="Channel")
    external_ref = fields.Char(string="Platform order reference", required=True, index=True)
    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    received_at = fields.Datetime(default=fields.Datetime.now, required=True)
    customer_name = fields.Char(string="Customer")
    customer_note = fields.Char()
    amount_total = fields.Monetary(currency_field="currency_id")
    commission_pct = fields.Float(related="platform_id.commission_pct", string="Commission %")
    commission_amount = fields.Monetary(
        compute="_compute_commission", store=True, currency_field="currency_id"
    )
    net_amount = fields.Monetary(compute="_compute_commission", store=True, currency_field="currency_id")
    state = fields.Selection(
        [("received", "Received"), ("imported", "Imported to POS"), ("rejected", "Rejected"),
         ("cancelled", "Cancelled")],
        default="received", required=True, index=True, tracking=True,
    )
    pos_order_id = fields.Many2one("pos.order", string="POS order", ondelete="set null", copy=False)
    payload = fields.Text(help="Raw payload, kept for replay and audit.")
    error_message = fields.Char(readonly=True, copy=False)
    settlement_id = fields.Many2one("rk.aggregator.settlement", string="Settlement", ondelete="set null")

    _aggregator_ref_uniq = models.Constraint(
        "UNIQUE(platform_id, external_ref)", "A platform order reference can only be imported once."
    )

    @api.depends("amount_total", "commission_pct")
    def _compute_commission(self):
        for order in self:
            order.commission_amount = (order.amount_total or 0.0) * (order.commission_pct or 0.0) / 100.0
            order.net_amount = (order.amount_total or 0.0) - order.commission_amount

    # ------------------------------------------------------------------
    @api.model
    def _receive(self, platform_code, payload):
        """Entry point for the middleware: ``payload`` is the platform's JSON body."""
        platform = self.env["rk.aggregator.platform"].search([("code", "=", platform_code)], limit=1)
        if not platform:
            raise UserError(_("Unknown platform code %s", platform_code))
        ref = payload.get("order_reference") or payload.get("id")
        if not ref:
            raise UserError(_("The payload has no order reference."))
        existing = self.search([("platform_id", "=", platform.id), ("external_ref", "=", ref)], limit=1)
        if existing:
            _logger.info("rk_aggregator_hub: duplicate order %s ignored", ref)
            return existing
        outlet = self.env["rk.outlet"].browse(int(payload.get("outlet_id") or 0)) or self.env[
            "rk.outlet"
        ]._rk_default_outlet()
        return self.create(
            {
                "platform_id": platform.id,
                "external_ref": str(ref),
                "outlet_id": outlet.id,
                "customer_name": payload.get("customer_name"),
                "customer_note": payload.get("note"),
                "amount_total": float(payload.get("total") or 0.0),
                "payload": json.dumps(payload, indent=2),
            }
        )

    def action_import_to_pos(self):
        """Create the paid POS order in the outlet's open session."""
        for order in self:
            session = order.outlet_id._rk_open_session()
            if not session:
                raise UserError(
                    _("Open a POS session on %s before importing platform orders.", order.outlet_id.name)
                )
            data = {}
            try:
                data = json.loads(order.payload or "{}")
            except ValueError:
                order.error_message = _("Payload is not valid JSON.")
            lines = []
            for item in data.get("lines", []):
                product = self.env["product.product"].browse(int(item.get("product_id") or 0))
                if not product:
                    product = self.env["product.product"].search(
                        [("default_code", "=", item.get("sku"))], limit=1
                    )
                if not product:
                    continue
                qty = float(item.get("qty") or 1.0)
                price = float(item.get("price") or product.lst_price)
                lines.append(
                    (0, 0, {
                        "product_id": product.id,
                        "qty": qty,
                        "price_unit": price,
                        "price_subtotal": qty * price,
                        "price_subtotal_incl": qty * price,
                    })
                )
            pos_order = self.env["pos.order"].create(
                {
                    "session_id": session.id,
                    "amount_tax": 0.0,
                    "amount_total": order.amount_total,
                    "amount_paid": order.amount_total,
                    "amount_return": 0.0,
                    "state": "paid",
                    "lines": lines,
                    "general_customer_note": order.customer_note or order.customer_name,
                }
            )
            order.write({"pos_order_id": pos_order.id, "state": "imported"})
        return True

    def action_reject(self):
        self.write({"state": "rejected"})
        return True

    def action_open_pos_order(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "pos.order",
            "res_id": self.pos_order_id.id,
            "view_mode": "form",
        }
