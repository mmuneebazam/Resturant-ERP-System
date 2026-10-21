# -*- coding: utf-8 -*-
{
    "name": "Restaurant Kit — Food Safety",
    "version": "19.0.1.0.0",
    "summary": "HACCP checklists, temperature logs, lot traceability and recall workflow",
    "description": """
Food Safety
===========

Evidence, not good intentions.

* **HACCP checklists** with per-checkpoint temperature ranges, frequency and
  outlet scope. A check either passes or fails, and a failure needs a
  corrective action before it is verified.
* **Temperature logs** accepting manual readings or sensor feeds
  (``source = sensor``), each validated against the equipment's range.
* **Recall workflow**: quarantine a lot, see every outlet it reached, record
  the action taken and who signed it off.
""",
    "author": "Restaurant Kit",
    "license": "LGPL-3",
    "category": "Restaurant",
    "depends": ["rk_restaurant_core", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/rk_food_safety_data.xml",
        "views/rk_haccp_views.xml",
        "views/rk_temperature_views.xml",
        "views/rk_recall_views.xml",
        "views/rk_menus.xml",
    ],
    "installable": True,
    "application": False,
    "sequence": 85,
}
