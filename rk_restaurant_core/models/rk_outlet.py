# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

FORMATS = [
    ("qsr", "Quick service"),
    ("casual", "Casual dining"),
    ("fine", "Fine dining"),
    ("cafe", "Café / bakery"),
    ("cloud", "Cloud kitchen"),
    ("central_kitchen", "Central kitchen"),
    ("catering", "Catering unit"),
    ("franchise", "Franchise outlet"),
]


class RkOutlet(models.Model):
    """The operational unit of the restaurant group.

    An outlet is deliberately *not* a ``pos.config``. A central kitchen has
    stock, production and dispatches but never opens a POS session; a franchise
    outlet belongs to another company. Both still need to appear in recipes,
    indents, food-safety logs, P&L and royalty statements, so the outlet is the
    common denominator and the POS profile is optional.
    """

    _name = "rk.outlet"
    _description = "Outlet"
    _order = "brand_id, sequence, code"
    _check_company_auto = True
    _parent_store = True

    name = fields.Char(required=True, translate=False)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    brand_id = fields.Many2one("rk.brand", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    format = fields.Selection(FORMATS, required=True, default="casual")
    parent_id = fields.Many2one("rk.outlet", string="Parent outlet", ondelete="restrict")
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many("rk.outlet", "parent_id", string="Child outlets")

    partner_id = fields.Many2one("res.partner", string="Franchisee / operator", ondelete="restrict")
    pos_config_id = fields.Many2one("pos.config", string="POS profile", ondelete="set null", copy=False)
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", ondelete="restrict")
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic account",
        ondelete="set null",
        copy=False,
        help="Every cost, sales and royalty line of this outlet is tagged with this analytic account.",
    )
    channel_ids = fields.Many2many(
        "rk.channel", "rk_outlet_channel_rel", "outlet_id", "channel_id", string="Channels"
    )
    daypart_ids = fields.Many2many(
        "rk.daypart", "rk_outlet_daypart_rel", "outlet_id", "daypart_id", string="Day-parts"
    )
    seats = fields.Integer(string="Seats", help="Covers used by reservation and capacity checks.")
    is_kitchen = fields.Boolean(compute="_compute_is_kitchen", store=True)
    is_pos_outlet = fields.Boolean(compute="_compute_is_pos_outlet", store=True)
    manager_id = fields.Many2one("res.users", string="Outlet manager")
    open_hour = fields.Float(string="Opens at", default=11.0)
    close_hour = fields.Float(string="Closes at", default=23.0)
    color = fields.Integer(default=0)
    notes = fields.Text()

    _outlet_code_uniq = models.Constraint(
        "UNIQUE(code, company_id)", "The outlet code must be unique per company."
    )

    @api.depends("format")
    def _compute_is_kitchen(self):
        for outlet in self:
            outlet.is_kitchen = outlet.format in ("central_kitchen", "cloud")

    @api.depends("pos_config_id")
    def _compute_is_pos_outlet(self):
        for outlet in self:
            outlet.is_pos_outlet = bool(outlet.pos_config_id)

    @api.depends("name", "code")
    def _compute_display_name(self):
        for outlet in self:
            outlet.display_name = f"{outlet.name} [{outlet.code}]" if outlet.code else outlet.name

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_("You cannot create a loop in the outlet hierarchy."))

    # ------------------------------------------------------------------
    # Helpers used by every other module in the kit
    # ------------------------------------------------------------------
    def _rk_stock_location(self):
        """Stock location that holds this outlet's inventory."""
        self.ensure_one()
        if self.warehouse_id:
            return self.warehouse_id.lot_stock_id
        return self.env["stock.location"].search(
            [("usage", "=", "internal"), ("company_id", "in", [self.company_id.id, False])], limit=1
        )

    def _rk_open_session(self):
        """Current open POS session, if any (used by aggregators and catering)."""
        self.ensure_one()
        if not self.pos_config_id:
            return self.env["pos.session"]
        return self.env["pos.session"].search(
            [("config_id", "=", self.pos_config_id.id), ("state", "=", "opened")], limit=1
        )

    def _rk_analytic_distribution(self, percentage=100.0):
        """Analytic distribution dict for ``account.move.line`` and stock moves."""
        self.ensure_one()
        if not self.analytic_account_id:
            return {}
        return {str(self.analytic_account_id.id): percentage}

    def _rk_daypart_at(self, moment):
        """Day-part covering ``moment`` (a datetime) for this outlet."""
        self.ensure_one()
        hour = (moment.hour + moment.minute / 60.0) if moment else 0.0
        dayparts = self.daypart_ids or self.env["rk.daypart"].search([("active", "=", True)])
        for daypart in dayparts.sorted(lambda d: -d.sequence):
            if daypart._contains_hour(hour):
                return daypart
        return self.env["rk.daypart"]

    def action_open_pos(self):
        self.ensure_one()
        if not self.pos_config_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "res_model": "pos.config",
            "res_id": self.pos_config_id.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model
    def _rk_default_outlet(self):
        """First POS-capable outlet, used as a sensible default in wizards."""
        return self.search([("pos_config_id", "!=", False), ("active", "=", True)], limit=1)
