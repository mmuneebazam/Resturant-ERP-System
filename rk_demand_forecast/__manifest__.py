# -*- coding: utf-8 -*-
{
    "name": "Restaurant Kit — Demand Forecasting",
    "version": "19.0.1.0.0",
    "summary": "Same-weekday forecasts per item, outlet and day-part with an honest accuracy number",
    "description": """
Demand Forecasting
==================

Forecasts you can argue with, which is the point.

* **Method**: same weekday, last *n* weeks, per item / outlet / day-part,
  blended with a short moving average.
* **Suggested prep** and **suggested purchase** derived from the forecast.
* **Actuals** written back after trading, with absolute percentage error per
  line and a weighted MAPE per outlet — so the model earns trust instead of
  demanding it.
* **Manual override** for the manager who knows it is going to rain.
""",
    "author": "Restaurant Kit",
    "license": "LGPL-3",
    "category": "Restaurant",
    "depends": ["rk_restaurant_core", "rk_recipe_costing", "point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/rk_forecast_data.xml",
        "views/rk_forecast_views.xml",
        "wizard/rk_forecast_generate_views.xml",
        "views/rk_menus.xml",
    ],
    "installable": True,
    "application": False,
    "sequence": 84,
}
