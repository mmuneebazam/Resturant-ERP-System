# -*- coding: utf-8 -*-
{
    "name": "Restaurant Kit — Demo Dataset",
    "version": "19.0.1.0.0",
    "summary": "A coherent restaurant group: brands, outlets, recipes, 3 weeks of trading, royalties",
    "description": """
Demo Dataset
============

Install this **on a fresh database** to get a group you can click through:

* Three brands, six outlets (QSR, casual, fine dining, café, cloud kitchen,
  central kitchen) across two companies, with floors and tables.
* 24 ingredients, 12 menu items, recipes with sub-recipes and BOMs.
* Three weeks of paid POS orders across day-parts and channels.
* Kitchen stations and 100+ tickets, with realistic prep times and SLA breaches.
* Indents, a consolidated production plan, dispatches with receipt variances.
* Waste records, HACCP checks, temperature logs, forecasts and their actuals.
* Reservations, a catering event, aggregator orders and a settlement.
* A franchisee with two royalty statements, outlet P&Ls, cash variances,
  pricing rules and recipe cost alerts.

Uninstall it to remove the transactional demo data (master configuration you
edited yourself stays).
""",
    "author": "Restaurant Kit",
    "license": "LGPL-3",
    "category": "Hidden",
    "depends": [
        "rk_restaurant_core",
        "rk_recipe_costing",
        "rk_central_kitchen",
        "rk_kds_routing",
        "rk_wastage_variance",
        "rk_food_safety",
        "rk_demand_forecast",
        "rk_aggregator_hub",
        "rk_reservations",
        "rk_pricing_promotions",
        "rk_special_orders",
        "rk_franchise",
        "rk_branch_pnl_labour",
    ],
    "data": [],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "sequence": 1,
}
