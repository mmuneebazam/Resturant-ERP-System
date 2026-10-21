# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import _, api, fields, models


class RkPnlPeriod(models.Model):
    """One outlet, one period, every number traceable to a transaction."""

    _name = "rk.pnl.period"
    _description = "Outlet P&L period"
    _order = "date_from desc, outlet_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(compute="_compute_name", store=True)
    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    brand_id = fields.Many2one(related="outlet_id.brand_id", store=True)
    date_from = fields.Date(required=True, index=True)
    date_to = fields.Date(required=True, index=True)
    state = fields.Selection(
        [("draft", "Draft"), ("calculated", "Calculated"), ("approved", "Approved")],
        default="draft", required=True, tracking=True, index=True,
    )

    # revenue and costs
    sales = fields.Monetary(currency_field="currency_id", string="Net sales")
    order_count = fields.Integer()
    food_cost = fields.Monetary(currency_field="currency_id")
    waste_cost = fields.Monetary(currency_field="currency_id")
    labour_cost = fields.Monetary(currency_field="currency_id")
    other_cost = fields.Monetary(currency_field="currency_id", string="Other operating costs")
    total_cost = fields.Monetary(
        compute="_compute_ratios", store=True, currency_field="currency_id", string="Total cost"
    )
    gross_profit = fields.Monetary(
        compute="_compute_ratios", store=True, currency_field="currency_id", string="Gross profit"
    )
    prime_cost_pct = fields.Float(compute="_compute_ratios", store=True, string="Prime cost %", digits=(6, 2))
    food_cost_pct = fields.Float(compute="_compute_ratios", store=True, string="Food cost %", digits=(6, 2))
    labour_pct = fields.Float(compute="_compute_ratios", store=True, string="Labour %", digits=(6, 2))
    labour_hours = fields.Float(compute="_compute_ratios", store=True, string="Labour hours")
    status = fields.Selection(
        [("ok", "On target"), ("watch", "Watch"), ("alert", "Above target")],
        compute="_compute_ratios", store=True, string="Prime cost status",
    )
    target_prime_cost_pct = fields.Float(related="brand_id.target_prime_cost_pct", store=True)
    labour_line_ids = fields.One2many("rk.pnl.labour.line", "period_id", string="Labour detail", copy=False)
    note = fields.Text()

    _pnl_uniq = models.Constraint(
        "UNIQUE(outlet_id, date_from, date_to)", "One P&L period per outlet and date range."
    )

    @api.depends("outlet_id", "date_from", "date_to")
    def _compute_name(self):
        for period in self:
            period.name = "%s %s → %s" % (
                period.outlet_id.code or "",
                period.date_from or "",
                period.date_to or "",
            )

    @api.depends("sales", "food_cost", "waste_cost", "labour_cost", "other_cost", "labour_line_ids.hours",
                 "target_prime_cost_pct")
    def _compute_ratios(self):
        for period in self:
            period.total_cost = period.food_cost + period.labour_cost + period.waste_cost + period.other_cost
            period.gross_profit = period.sales - period.total_cost
            period.labour_hours = sum(period.labour_line_ids.mapped("hours"))
            if period.sales:
                period.food_cost_pct = (period.food_cost + period.waste_cost) / period.sales * 100.0
                period.labour_pct = period.labour_cost / period.sales * 100.0
                period.prime_cost_pct = period.food_cost_pct + period.labour_pct
            else:
                period.food_cost_pct = period.labour_pct = period.prime_cost_pct = 0.0
            target = period.target_prime_cost_pct or 58.0
            if period.prime_cost_pct <= target:
                period.status = "ok"
            elif period.prime_cost_pct <= target + 4:
                period.status = "watch"
            else:
                period.status = "alert"

    # ------------------------------------------------------------------
    def action_compute(self):
        """Recalculate every figure from POS, stock, waste and attendance."""
        for period in self:
            period._compute_sales()
            period._compute_food_cost()
            period._compute_waste()
            period._compute_labour()
            period._compute_other_costs()
            period.state = "calculated"
        return True

    def _period_domain(self):
        self.ensure_one()
        return (
            fields.Datetime.to_datetime(self.date_from),
            fields.Datetime.to_datetime(self.date_to).replace(hour=23, minute=59, second=59),
        )

    def _compute_sales(self):
        self.ensure_one()
        start, end = self._period_domain()
        orders = self.env["pos.order"].search(
            [
                ("state", "=", "paid"),
                ("config_id.rk_outlet_id", "=", self.outlet_id.id),
                ("date_order", ">=", start),
                ("date_order", "<=", end),
            ]
        )
        self.sales = sum(orders.mapped("amount_total"))
        self.order_count = len(orders)

    def _compute_food_cost(self):
        """Prefer the POS line cost (real COGS); fall back to recipe cost."""
        self.ensure_one()
        start, end = self._period_domain()
        lines = self.env["pos.order.line"].search(
            [
                ("order_id.state", "=", "paid"),
                ("order_id.config_id.rk_outlet_id", "=", self.outlet_id.id),
                ("order_id.date_order", ">=", start),
                ("order_id.date_order", "<=", end),
            ]
        )
        cost = 0.0
        if "total_cost" in lines._fields:
            cost = sum(lines.mapped("total_cost"))
        if not cost:
            Recipe = self.env["rk.recipe"]
            for line in lines:
                recipe = Recipe.search(
                    [("product_id", "=", line.product_id.id), ("state", "=", "approved")], limit=1
                )
                if recipe:
                    cost += recipe.cost_per_portion * line.qty
                else:
                    cost += (line.product_id.standard_price or 0.0) * line.qty
        self.food_cost = cost

    def _compute_waste(self):
        self.ensure_one()
        waste = self.env["rk.waste"].search(
            [("outlet_id", "=", self.outlet_id.id), ("state", "=", "approved"),
             ("date", ">=", self.date_from), ("date", "<=", self.date_to)]
        )
        self.waste_cost = sum(waste.mapped("value"))

    def _compute_labour(self):
        """Hours from attendance, cost from the employee's loaded rate."""
        self.ensure_one()
        start, end = self._period_domain()
        attendances = self.env["hr.attendance"].search(
            [
                ("check_in", ">=", start),
                ("check_in", "<=", end),
                ("employee_id.rk_home_outlet_id", "=", self.outlet_id.id),
            ]
        )
        self.labour_line_ids.unlink()
        by_employee = defaultdict(float)
        for attendance in attendances:
            hours = attendance.worked_hours or 0.0
            by_employee[attendance.employee_id] += hours
        commands = []
        for employee, hours in by_employee.items():
            rate = employee.rk_hourly_rate or 0.0
            commands.append(
                (0, 0, {"employee_id": employee.id, "hours": hours, "hourly_rate": rate, "cost": hours * rate})
            )
        self.write({"labour_line_ids": commands, "labour_cost": sum(c[2]["cost"] for c in commands)})

    def _compute_other_costs(self):
        self.ensure_one()
        account = self.outlet_id.analytic_account_id
        if not account:
            self.other_cost = 0.0
            return
        try:
            lines = self.env["account.move.line"].search(
                [
                    ("move_id.state", "=", "posted"),
                    ("date", ">=", self.date_from),
                    ("date", "<=", self.date_to),
                    ("account_id.account_type", "in", ("expense", "expense_direct_cost")),
                    ("analytic_distribution", "in", [account.id]),
                ]
            )
            self.other_cost = sum(lines.mapped("balance"))
        except Exception:  # noqa: BLE001 - analytics may not be installed on every analytic plan
            self.other_cost = 0.0

    def action_approve(self):
        for period in self:
            period.state = "approved"
            period.message_post(
                body=_("P&L approved: sales %(sales).2f, prime cost %(prime).1f%%.",
                       sales=period.sales, prime=period.prime_cost_pct)
            )
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True

    @api.model
    def _cron_month_close(self):
        """Close last month for every POS outlet that does not have a period yet."""
        today = fields.Date.context_today(self)
        first_this_month = today.replace(day=1)
        last_month_end = fields.Date.subtract(first_this_month, days=1)
        last_month_start = last_month_end.replace(day=1)
        created = 0
        for outlet in self.env["rk.outlet"].search([("pos_config_id", "!=", False)]):
            exists = self.search_count(
                [("outlet_id", "=", outlet.id), ("date_from", "=", last_month_start)]
            )
            if exists:
                continue
            period = self.create(
                {"outlet_id": outlet.id, "date_from": last_month_start, "date_to": last_month_end}
            )
            period.action_compute()
            created += 1
        return created


class RkPnlLabourLine(models.Model):
    _name = "rk.pnl.labour.line"
    _description = "P&L labour line"

    period_id = fields.Many2one("rk.pnl.period", required=True, ondelete="cascade", index=True)
    employee_id = fields.Many2one("hr.employee", required=True, ondelete="restrict")
    currency_id = fields.Many2one(related="period_id.currency_id")
    hours = fields.Float(default=0.0)
    hourly_rate = fields.Monetary(currency_field="currency_id")
    cost = fields.Monetary(currency_field="currency_id")
    cost_pct = fields.Float(compute="_compute_cost_pct", string="% of sales", digits=(6, 2))

    @api.depends("cost", "period_id.sales")
    def _compute_cost_pct(self):
        for line in self:
            line.cost_pct = (line.cost / line.period_id.sales * 100.0) if line.period_id.sales else 0.0
