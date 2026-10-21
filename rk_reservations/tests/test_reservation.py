# -*- coding: utf-8 -*-
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReservation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env["rk.brand"].create({"name": "R Brand", "code": "RB"})
        cls.outlet = cls.env["rk.outlet"].create(
            {"name": "R Outlet", "code": "R-01", "brand_id": cls.brand.id, "format": "casual", "seats": 40}
        )
        cls.floor = cls.env["restaurant.floor"].create({"name": "Main"})
        cls.table = cls.env["restaurant.table"].create(
            {"table_number": 7, "seats": 4, "floor_id": cls.floor.id}
        )
        cls.start = fields.Datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)

    def _book(self, guest, start):
        return self.env["rk.reservation"].create(
            {
                "guest_name": guest,
                "outlet_id": self.outlet.id,
                "table_id": self.table.id,
                "party_size": 2,
                "start": start,
                "duration_minutes": 90,
            }
        )

    def test_no_double_booking(self):
        self._book("Ayesha", self.start)
        with self.assertRaises(ValidationError):
            self._book("Bilal", fields.Datetime.add(self.start, minutes=30))

    def test_back_to_back_allowed(self):
        self._book("Ayesha", self.start)
        second = self._book("Bilal", fields.Datetime.add(self.start, minutes=90))
        self.assertEqual(second.state, "draft")

    def test_lifecycle(self):
        reservation = self._book("Ayesha", self.start)
        self.assertTrue(reservation.name.startswith("RSV/"))
        reservation.action_confirm()
        reservation.action_no_show()
        self.assertEqual(reservation.state, "no_show")

    def test_seats_guard(self):
        with self.assertRaises(ValidationError):
            self.env["rk.reservation"].create(
                {
                    "guest_name": "Large party",
                    "outlet_id": self.outlet.id,
                    "table_id": self.table.id,
                    "party_size": 10,
                    "start": self.start,
                }
            )
