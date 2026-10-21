# -*- coding: utf-8 -*-
{
    "name": "Restaurant Kit — Reservations",
    "version": "19.0.1.0.0",
    "summary": "Bookings, table conflict detection, deposits, no-shows and a walk-in waitlist",
    "description": """
Reservations
============

The revenue you can plan for.

* Bookings with guest details, party size, turn time, channel and table.
* **Conflict detection**: a table cannot be double-booked inside its turn time.
* **Deposits** for large parties, tracked against the booking.
* **No-show rules**: flagged automatically once the grace period passes.
* **Waitlist** for walk-ins, with quoted vs actual wait.
""",
    "author": "Restaurant Kit",
    "license": "LGPL-3",
    "category": "Restaurant",
    "depends": ["rk_restaurant_core", "pos_restaurant", "point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/rk_reservation_data.xml",
        "views/rk_reservation_views.xml",
        "views/rk_waitlist_views.xml",
        "views/rk_menus.xml",
    ],
    "installable": True,
    "application": False,
    "sequence": 82,
}
