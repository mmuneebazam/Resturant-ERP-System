# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFoodSafety(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env["rk.brand"].create({"name": "FS Brand", "code": "FS"})
        cls.outlet = cls.env["rk.outlet"].create(
            {"name": "FS Outlet", "code": "FS-01", "brand_id": cls.brand.id, "format": "casual"}
        )
        cls.checklist = cls.env.ref("rk_food_safety.checklist_opening")

    # A checkpoint reads as failing until a value inside its band is recorded,
    # so a completed check needs a reading on every temperature line.
    PASSING = {
        "Walk-in chiller": 3.0,
        "Walk-in freezer": -20.0,
        "Prep fridge (line)": 4.0,
        "Hot hold cabinet": 72.0,
    }

    def _check(self, breach_on=None, breach_value=9.5):
        check = self.env["rk.haccp.check"].create(
            {"checklist_id": self.checklist.id, "outlet_id": self.outlet.id}
        )
        check.action_load_checkpoints()
        for line in check.line_ids.filtered("is_temperature"):
            line.temp_value = (
                breach_value if line.name == breach_on else self.PASSING.get(line.name, 3.0)
            )
        return check

    def test_pass(self):
        check = self._check()
        check.action_validate()
        self.assertEqual(check.state, "pass")
        self.assertEqual(check.failure_count, 0)

    def test_fail_requires_corrective_action(self):
        check = self._check(breach_on="Walk-in chiller")
        with self.assertRaises(UserError):
            check.action_validate()
        check.corrective_action = "Moved stock to the backup chiller; technician called."
        check.action_validate()
        self.assertEqual(check.state, "fail")
        self.assertGreaterEqual(check.failure_count, 1)

    def test_temperature_log_range(self):
        log = self.env["rk.temperature.log"].create(
            {"outlet_id": self.outlet.id, "value": 2.5, "temp_min": 0, "temp_max": 5}
        )
        self.assertTrue(log.is_ok)
        log.value = 8.0
        self.assertFalse(log.is_ok)
