# -*- coding: utf-8 -*-
{
    "name": "Restaurant Kit — Central Kitchen",
    "version": "19.0.1.0.0",
    "summary": "Par levels, outlet indents, consolidated production and dispatch with receipt variance",
    "description": """
Central Kitchen
===============

The kitchen that cooks for the kitchens.

* **Par levels** per outlet and item, with days-of-cover and suggested order quantity.
* **Indents**: outlets request, the kitchen approves — with requested vs approved
  quantities side by side.
* **Consolidated production plan**: all approved indents for a day collapse into
  one plan, one line per item, exploded into manufacturing orders from BOMs.
* **Dispatch**: one shipment per outlet, with temperature at loading.
* **Receipt variance**: what was sent, what arrived, what is missing — and why.
""",
    "author": "Restaurant Kit",
    "license": "LGPL-3",
    "category": "Restaurant",
    "depends": ["rk_restaurant_core", "rk_recipe_costing", "stock", "mrp", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "data/rk_ck_data.xml",
        "views/rk_par_level_views.xml",
        "views/rk_indent_views.xml",
        "views/rk_production_plan_views.xml",
        "views/rk_dispatch_views.xml",
        "views/rk_menus.xml",
    ],
    "installable": True,
    "application": False,
    "sequence": 88,
}
