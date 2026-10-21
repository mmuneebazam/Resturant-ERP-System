# -*- coding: utf-8 -*-
import logging
from collections import defaultdict

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class RkForecast(models.Model):
    _name = "rk.forecast"
    _description = "Demand forecast"
    _order = "date, outlet_id, product_id"
    _check_company_auto = True

    date = fields.Date(required=True, index=True)
    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    product_id = fields.Many2one(
        "product.product", required=True, ondelete="cascade", domain=[("sale_ok", "=", True)]
    )
    daypart_id = fields.Many2one("rk.daypart", ondelete="set null")
    method = fields.Selection(
        [("same_weekday", "Same weekday average"), ("manual", "Manual override"), ("override", "Manager override")],
        default="same_weekday", required=True,
    )
    history_weeks = fields.Integer(default=4)
    qty_forecast = fields.Float(string="Forecast qty")
    qty_override = fields.Float(string="Override qty")
    qty_planned = fields.Float(compute="_compute_planned", store=True, string="Planned qty")
    qty_actual = fields.Float(string="Actual qty")
    accuracy = fields.Float(compute="_compute_accuracy", store=True, string="Accuracy %", digits=(6, 1))
    error_pct = fields.Float(compute="_compute_accuracy", store=True, string="Error %", digits=(6, 1))
    suggested_prep = fields.Float(compute="_compute_suggested", store=True, string="Suggested prep")
    suggested_purchase = fields.Float(compute="_compute_suggested", store=True, string="Suggested purchase")
    qty_on_hand = fields.Float(compute="_compute_suggested", store=True, string="On hand")
    state = fields.Selection(
        [("forecast", "Forecast"), ("confirmed", "Confirmed"), ("closed", "Closed")],
        default="forecast", required=True, index=True,
    )

    _forecast_uniq = models.Constraint(
        "UNIQUE(date, outlet_id, product_id, daypart_id)",
        "One forecast line per outlet, item, day-part and date.",
    )

    @api.depends("qty_forecast", "qty_override")
    def _compute_planned(self):
        for forecast in self:
            forecast.qty_planned = forecast.qty_override or forecast.qty_forecast

    @api.depends("qty_planned", "qty_actual")
    def _compute_accuracy(self):
        for forecast in self:
            if not forecast.qty_actual:
                forecast.accuracy = 0.0
                forecast.error_pct = 0.0
                continue
            forecast.error_pct = abs(forecast.qty_actual - forecast.qty_planned) / forecast.qty_actual * 100.0
            forecast.accuracy = max(0.0, 100.0 - forecast.error_pct)

    @api.depends("qty_planned", "product_id", "outlet_id")
    def _compute_suggested(self):
        for forecast in self:
            location = forecast.outlet_id._rk_stock_location()
            on_hand = forecast.product_id.with_context(location=location.id).qty_available if location else 0.0
            forecast.qty_on_hand = on_hand
            forecast.suggested_prep = max(0.0, forecast.qty_planned - on_hand)
            forecast.suggested_purchase = max(0.0, forecast.qty_planned - on_hand)

    # ------------------------------------------------------------------
    @api.model
    def _history_for(self, outlet, product, dates, daypart=None):
        """Units actually sold on each of the given dates."""
        lines = self.env["pos.order.line"].search(
            [
                ("order_id.state", "=", "paid"),
                ("order_id.config_id.rk_outlet_id", "=", outlet.id),
                ("product_id", "=", product.id),
                ("order_id.date_order", ">=", min(dates)),
                ("order_id.date_order", "<=", max(dates)),
            ]
        )
        by_date = defaultdict(float)
        for line in lines:
            order_date = line.order_id.date_order.date()
            if order_date not in dates:
                continue
            if daypart and not daypart._contains_hour(line.order_id.date_order.hour):
                continue
            by_date[order_date] += line.qty
        return by_date

    @api.model
    def _forecast_qty(self, outlet, product, day, daypart=None, weeks=4):
        history_dates = {fields.Date.subtract(day, weeks=week) for week in range(1, weeks + 1)}
        by_date = self._history_for(outlet, product, history_dates, daypart)
        if not by_date:
            return 0.0
        return round(sum(by_date.values()) / len(by_date), 2)

    @api.model
    def _generate_for(self, outlets, date_from, date_to, dayparts=None, weeks=4):
        """Create or refresh forecasts for a date range."""
        created = 0
        day = fields.Date.to_date(date_from)
        end = fields.Date.to_date(date_to)
        products = self.env["product.product"].search(
            [("sale_ok", "=", True), ("available_in_pos", "=", True)]
        )
        dayparts = dayparts or self.env["rk.daypart"].browse()
        while day <= end:
            for outlet in outlets:
                for product in products:
                    for daypart in (dayparts or [self.env["rk.daypart"]]):
                        qty = self._forecast_qty(outlet, product, day, daypart or None, weeks)
                        existing = self.search(
                            [
                                ("date", "=", day),
                                ("outlet_id", "=", outlet.id),
                                ("product_id", "=", product.id),
                                ("daypart_id", "=", daypart.id if daypart else False),
                            ],
                            limit=1,
                        )
                        if not qty and not existing:
                            continue
                        values = {
                            "date": day,
                            "outlet_id": outlet.id,
                            "product_id": product.id,
                            "daypart_id": daypart.id if daypart else False,
                            "qty_forecast": qty,
                            "history_weeks": weeks,
                        }
                        if existing:
                            if existing.method != "override":
                                existing.write(values)
                        else:
                            self.create(dict(values, method="same_weekday"))
                            created += 1
            day = fields.Date.add(day, days=1)
        return created

    @api.model
    def _cron_generate_tomorrow(self):
        tomorrow = fields.Date.add(fields.Date.context_today(self), days=1)
        outlets = self.env["rk.outlet"].search([("pos_config_id", "!=", False)])
        created = self._generate_for(outlets, tomorrow, tomorrow)
        _logger.info("rk_demand_forecast: %s lines generated for %s", created, tomorrow)
        return created

    @api.model
    def _cron_capture_actuals(self):
        yesterday = fields.Date.subtract(fields.Date.context_today(self), days=1)
        forecasts = self.search([("date", "=", yesterday), ("state", "!=", "closed")])
        for forecast in forecasts:
            lines = self.env["pos.order.line"].search(
                [
                    ("order_id.state", "=", "paid"),
                    ("order_id.config_id.rk_outlet_id", "=", forecast.outlet_id.id),
                    ("product_id", "=", forecast.product_id.id),
                    ("order_id.date_order", ">=", yesterday),
                    ("order_id.date_order", "<", fields.Date.add(yesterday, days=1)),
                ]
            )
            qty = 0.0
            for line in lines:
                if forecast.daypart_id and not forecast.daypart_id._contains_hour(line.order_id.date_order.hour):
                    continue
                qty += line.qty
            forecast.write({"qty_actual": qty, "state": "closed"})
        return True

    def action_confirm(self):
        self.write({"state": "confirmed"})
        return True

    def action_apply_override(self):
        self.write({"method": "override"})
        return True

    @api.model
    def _wape(self, forecasts):
        """Weighted absolute percentage error, in percent."""
        total_actual = sum(forecasts.mapped("qty_actual"))
        if not total_actual:
            return 0.0
        total_error = sum(abs(f.qty_actual - f.qty_planned) for f in forecasts)
        return total_error / total_actual * 100.0
