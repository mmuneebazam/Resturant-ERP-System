# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestForecast(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env["rk.brand"].create({"name": "F Brand", "code": "FB"})
        cls.outlet = cls.env["rk.outlet"].create(
            {"name": "F Outlet", "code": "F-01", "brand_id": cls.brand.id, "format": "qsr"}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Wrap", "type": "consu", "sale_ok": True, "available_in_pos": True}
        )

    def test_accuracy_and_wape(self):
        today = fields.Date.context_today(self)
        f1 = self.env["rk.forecast"].create(
            {"date": today, "outlet_id": self.outlet.id, "product_id": self.product.id,
             "qty_forecast": 100, "qty_actual": 110}
        )
        f2 = self.env["rk.forecast"].create(
            {"date": today, "outlet_id": self.outlet.id, "product_id": self.product.id,
             "daypart_id": self.env.ref("rk_restaurant_core.daypart_lunch").id,
             "qty_forecast": 50, "qty_actual": 40}
        )
        self.assertAlmostEqual(f1.error_pct, 9.09, places=1)
        self.assertAlmostEqual(f1.accuracy, 90.91, places=1)
        wape = self.env["rk.forecast"]._wape(f1 | f2)
        self.assertAlmostEqual(wape, 13.33, places=1)

    def test_override_wins(self):
        today = fields.Date.context_today(self)
        forecast = self.env["rk.forecast"].create(
            {"date": today, "outlet_id": self.outlet.id, "product_id": self.product.id,
             "qty_forecast": 100, "qty_override": 130}
        )
        self.assertEqual(forecast.qty_planned, 130)
