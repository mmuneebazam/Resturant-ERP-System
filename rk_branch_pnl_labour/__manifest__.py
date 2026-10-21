# -*- coding: utf-8 -*-
{
    "name": "Restaurant Kit — Branch P&L & Labour",
    "version": "19.0.1.0.0",
    "summary": "Outlet P&L from transactions, labour cost from attendance, prime cost and cash variance",
    "description": """
Branch P&L & Labour
===================

The number the owner asks for, calculated rather than typed.

* **Outlet P&L**: revenue from paid POS orders, food cost from recipes (or the
  POS line cost where available), waste, labour and analytic expenses.
* **Prime cost** = food + labour, with the brand's target and a status flag.
* **Labour from attendance**: hours per employee × their hourly rate, with a
  breakdown you can defend in a meeting.
* **Cash variance** per POS session: expected vs counted, with approval.
* **Month-end job** that closes every outlet's period automatically.
""",
    "author": "Restaurant Kit",
    "license": "LGPL-3",
    "category": "Restaurant",
    "depends": [
        "rk_restaurant_core", "rk_recipe_costing", "rk_wastage_variance",
        "point_of_sale", "hr_attendance", "account", "analytic",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/rk_pnl_views.xml",
        "views/rk_cash_variance_views.xml",
        "views/rk_menus.xml",
    ],
    "installable": True,
    "application": False,
    "sequence": 78,
}
