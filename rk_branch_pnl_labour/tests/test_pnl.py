# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBranchPnl(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env["rk.brand"].create(
            {"name": "P&L Brand", "code": "PLB", "target_prime_cost_pct": 58.0}
        )
        cls.outlet = cls.env["rk.outlet"].create(
            {"name": "P&L Outlet", "code": "PL-01", "brand_id": cls.brand.id, "format": "casual"}
        )

    def test_ratios(self):
        today = fields.Date.context_today(self)
        period = self.env["rk.pnl.period"].create(
            {
                "outlet_id": self.outlet.id,
                "date_from": today,
                "date_to": today,
                "sales": 10000.0,
                "food_cost": 3000.0,
                "labour_cost": 2500.0,
                "waste_cost": 200.0,
                "other_cost": 1000.0,
            }
        )
        period._compute_ratios()
        self.assertAlmostEqual(period.food_cost_pct, 32.0, places=2)
        self.assertAlmostEqual(period.labour_pct, 25.0, places=2)
        self.assertAlmostEqual(period.prime_cost_pct, 57.0, places=2)
        self.assertEqual(period.status, "ok")
        self.assertAlmostEqual(period.gross_profit, 3300.0, places=2)

    def test_alert_status(self):
        today = fields.Date.context_today(self)
        period = self.env["rk.pnl.period"].create(
            {
                "outlet_id": self.outlet.id,
                "date_from": today,
                "date_to": today,
                "sales": 1000.0,
                "food_cost": 400.0,
                "labour_cost": 300.0,
            }
        )
        period._compute_ratios()
        self.assertEqual(period.status, "alert")  # 70% prime cost

    def test_cash_variance(self):
        record = self.env["rk.cash.variance"].create(
            {
                "outlet_id": self.outlet.id,
                "expected_cash": 1000.0,
                "counted_cash": 970.0,
            }
        )
        self.assertAlmostEqual(record.variance, -30.0, places=2)
        self.assertAlmostEqual(record.variance_pct, -3.0, places=2)
        record.action_submit()
        record.explanation = "Paid the vegetable supplier from the drawer."
        record.action_explain()
        record.action_approve()
        self.assertEqual(record.state, "approved")
