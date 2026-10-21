# -*- coding: utf-8 -*-
"""The demo restaurant group.

Installed by ``rk_demo_data``'s post-init hook. Everything is created through
the ORM so every record is a normal, editable record: no raw SQL, no fixtures
you cannot open in the UI.
"""
import logging
import random
from datetime import datetime, timedelta

from odoo import SUPERUSER_ID, fields

_logger = logging.getLogger(__name__)

random.seed(20260421)

INGREDIENTS = [
    ("Beef patty 150g", "ING-BEEF", 2.40),
    ("Brioche bun", "ING-BUN", 0.55),
    ("Cheddar slice", "ING-CHED", 0.45),
    ("Lettuce", "ING-LETT", 0.12),
    ("Tomato", "ING-TOMA", 0.18),
    ("Pickles", "ING-PICK", 0.10),
    ("Burger sauce", "ING-SAUCE", 0.22),
    ("Potato fries", "ING-FRIE", 0.80),
    ("Chicken breast", "ING-CHIK", 2.10),
    ("Basmati rice", "ING-RICE", 0.65),
    ("Saffron", "ING-SAFF", 1.40),
    ("Yoghurt", "ING-YOGH", 0.30),
    ("Garam masala", "ING-MASAL", 0.15),
    ("Onion", "ING-ONIO", 0.08),
    ("Cooking oil", "ING-OIL", 0.35),
    ("Coffee beans", "ING-COFF", 0.60),
    ("Whole milk", "ING-MILK", 0.20),
    ("Sugar", "ING-SUGA", 0.05),
    ("Chocolate", "ING-CHOC", 0.50),
    ("Flour", "ING-FLOU", 0.10),
    ("Butter", "ING-BUTT", 0.25),
    ("Egg", "ING-EGG", 0.14),
    ("Cocoa powder", "ING-COCO", 0.30),
    ("Cream", "ING-CREA", 0.28),
]

MENU = [
    # (name, sku, price, brand code, category, recipe lines: (ingredient sku, qty))
    ("Smash Burger", "MNU-SMASH", 14.50, "BLZ", "Burgers",
     [("ING-BEEF", 1.0), ("ING-BUN", 1.0), ("ING-CHED", 1.0), ("ING-SAUCE", 0.04), ("ING-PICK", 0.02)]),
    ("Double Smash", "MNU-DOUBLE", 18.50, "BLZ", "Burgers",
     [("ING-BEEF", 2.0), ("ING-BUN", 1.0), ("ING-CHED", 2.0), ("ING-SAUCE", 0.06)]),
    ("Chicken Burger", "MNU-CHIKB", 13.00, "BLZ", "Burgers",
     [("ING-CHIK", 0.15), ("ING-BUN", 1.0), ("ING-LETT", 0.02), ("ING-SAUCE", 0.04)]),
    ("Loaded Fries", "MNU-FRIES", 6.50, "BLZ", "Sides",
     [("ING-FRIE", 0.25), ("ING-CHED", 1.0), ("ING-SAUCE", 0.03)]),
    ("Chicken Biryani", "MNU-BIRY", 17.00, "SAF", "Mains",
     [("ING-CHIK", 0.22), ("ING-RICE", 0.18), ("ING-SAFF", 0.001), ("ING-YOGH", 0.05), ("ING-MASAL", 0.01)]),
    ("Mutton Karahi", "MNU-KARAHI", 21.00, "SAF", "Mains",
     [("ING-CHIK", 0.20), ("ING-TOMA", 0.15), ("ING-OIL", 0.05), ("ING-MASAL", 0.02)]),
    ("Saffron Rice", "MNU-RICE", 5.00, "SAF", "Sides", [("ING-RICE", 0.20), ("ING-SAFF", 0.0005)]),
    ("Flat White", "MNU-FLAT", 4.20, "BRW", "Coffee", [("ING-COFF", 0.018), ("ING-MILK", 0.15)]),
    ("Cappuccino", "MNU-CAPP", 4.00, "BRW", "Coffee", [("ING-COFF", 0.018), ("ING-MILK", 0.12)]),
    ("Iced Latte", "MNU-ICED", 4.80, "BRW", "Coffee", [("ING-COFF", 0.02), ("ING-MILK", 0.18)]),
    ("Brownie", "MNU-BROWN", 5.50, "BRW", "Bakery",
     [("ING-CHOC", 0.05), ("ING-BUTT", 0.03), ("ING-EGG", 0.5), ("ING-FLOU", 0.04), ("ING-SUGA", 0.04)]),
    ("Croissant", "MNU-CROIS", 3.80, "BRW", "Bakery", [("ING-FLOU", 0.06), ("ING-BUTT", 0.03)]),
]

MENU_BRAND = [(row[1], row[3], row[4]) for row in MENU]

OUTLETS = [
    # (code, name, brand, format, seats, city)
    ("BLZ-01", "Blaze Burger — Gulberg", "BLZ", "qsr", 40),
    ("BLZ-02", "Blaze Burger — DHA", "BLZ", "qsr", 36),
    ("SAF-01", "Saffron Table — Mall Road", "SAF", "fine", 80),
    ("BRW-01", "Brew & Bean — Liberty", "BRW", "cafe", 30),
    ("CLD-01", "Blaze Cloud — Johar Town", "BLZ", "cloud", 0),
]

CHANNELS_BY_FORMAT = {
    "qsr": ["DINE", "TAKE", "DELV", "TALABAT", "DELIVEROO"],
    "fine": ["DINE", "TAKE", "DELV"],
    "cafe": ["DINE", "TAKE", "DELV", "TALABAT"],
    "cloud": ["TALABAT", "DELIVEROO", "DELV"],
    "central_kitchen": ["DELV"],
    "franchise": ["DINE", "TAKE", "DELV"],
    "catering": ["CATER"],
}


def _product(env, name, sku, price, categ, brand=None, is_ingredient=False, pos_categ=None):
    template = env["product.template"].create(
        {
            "name": name,
            "default_code": sku,
            "type": "consu",
            "is_storable": is_ingredient,
            "sale_ok": not is_ingredient,
            "purchase_ok": is_ingredient,
            "available_in_pos": not is_ingredient,
            "list_price": price,
            "standard_price": price if is_ingredient else 0.0,
            "categ_id": categ.id,
            "pos_categ_ids": [(6, 0, [pos_categ.id])] if pos_categ else [(5, 0, 0)],
        }
    )
    return template.product_variant_id


def _get_categories(env):
    categ_all = env["product.category"].create({"name": "Restaurant Kit"})
    categ_ing = env["product.category"].create({"name": "Ingredients", "parent_id": categ_all.id})
    categ_menu = env["product.category"].create({"name": "Menu", "parent_id": categ_all.id})
    return categ_ing, categ_menu


def _payment_method(env, name, journal_type="cash"):
    journal = env["account.journal"].search([("type", "=", journal_type)], limit=1)
    method = env["pos.payment.method"].search([("name", "=", name)], limit=1)
    if not method:
        method = env["pos.payment.method"].create(
            {"name": name, "journal_id": journal.id if journal else False, "is_cash_count": True}
        )
    return method


def _open_session(env, config):
    session = env["pos.session"].search(
        [("config_id", "=", config.id), ("state", "=", "opened")], limit=1
    )
    if session:
        return session
    session = env["pos.session"].create({"config_id": config.id, "user_id": env.uid})
    session.action_pos_session_open()
    return session


def _order(env, session, products, day, count):
    """Create one paid POS order with 1–3 lines."""
    hour_pool = [(8, 10), (12, 15), (18, 21), (22, 23)]
    start_hour, end_hour = random.choice(hour_pool)
    moment = day.replace(
        hour=random.randint(start_hour, end_hour), minute=random.randint(0, 59), second=0, microsecond=0
    )
    lines = random.sample(products, k=min(len(products), random.randint(1, 3)))
    commands = []
    total = 0.0
    for product in lines:
        qty = random.randint(1, 2)
        price = product.lst_price
        subtotal = qty * price
        total += subtotal
        commands.append(
            (0, 0, {
                "product_id": product.id,
                "qty": qty,
                "price_unit": price,
                "price_subtotal": subtotal,
                "price_subtotal_incl": subtotal,
                "full_product_name": product.display_name,
            })
        )
    order = env["pos.order"].create(
        {
            "session_id": session.id,
            "date_order": moment,
            "amount_tax": 0.0,
            "amount_total": total,
            "amount_paid": total,
            "amount_return": 0.0,
            "state": "paid",
            "lines": commands,
            "pos_reference": f"{session.config_id.name[:6]}-{day:%m%d}-{count:03d}",
        }
    )
    return order


def _seed(env):
    """Build the demo group. Returns a dict of created records for later steps."""
    ctx = {}
    admin = env.ref("base.user_admin")
    ctx["company"] = env.company
    env.company.name = "Northline Restaurant Group"

    brands = {b.code: b for b in env["rk.brand"].search([])}
    channels = {c.code: c for c in env["rk.channel"].search([])}
    dayparts = {d.code: d for d in env["rk.daypart"].search([])}
    ctx["brands"], ctx["channels"], ctx["dayparts"] = brands, channels, dayparts

    # --- products -----------------------------------------------------
    categ_ing, categ_menu = _get_categories(env)
    pos_categs = {}
    for name in ("Burgers", "Sides", "Mains", "Coffee", "Bakery"):
        pos_categs[name] = env["pos.category"].create({"name": name})

    ingredients = {}
    for name, sku, cost in INGREDIENTS:
        ingredients[sku] = _product(env, name, sku, cost, categ_ing, is_ingredient=True)
    ctx["ingredients"] = ingredients

    products = {}
    for name, sku, price, brand_code, categ_name, lines in MENU:
        products[sku] = _product(
            env, name, sku, price, categ_menu, brand_code, pos_categ=pos_categs[categ_name]
        )
    ctx["products"], ctx["pos_categs"] = products, pos_categs

    # --- recipes (+ a sub-recipe to prove the roll-up) -----------------
    sauce = env["rk.recipe"].create(
        {
            "name": "Burger sauce (batch of 20)",
            "product_id": ingredients["ING-SAUCE"].id,
            "brand_id": brands["BLZ"].id,
            "yield_qty": 20.0,
            "line_ids": [
                (0, 0, {"product_id": ingredients["ING-YOGH"].id, "qty": 0.6}),
                (0, 0, {"product_id": ingredients["ING-PICK"].id, "qty": 0.2}),
                (0, 0, {"product_id": ingredients["ING-MASAL"].id, "qty": 0.05}),
            ],
        }
    )
    sauce.action_approve()

    recipes = {}
    for name, sku, price, brand_code, categ_name, lines in MENU:
        commands = [
            (0, 0, {"product_id": ingredients[ing_sku].id, "qty": qty, "waste_pct": 2.0})
            for ing_sku, qty in lines
        ]
        if sku in ("MNU-SMASH", "MNU-DOUBLE"):
            commands.append((0, 0, {"item_type": "recipe", "sub_recipe_id": sauce.id, "qty": 0.03}))
        recipe = env["rk.recipe"].create(
            {
                "name": name,
                "product_id": products[sku].id,
                "brand_id": brands[brand_code].id,
                "yield_qty": 1.0,
                "waste_allowance_pct": 3.0,
                "labor_minutes": 4.0 if categ_name in ("Burgers", "Mains") else 2.0,
                "labor_rate": 6.5,
                "overhead_pct": 6.0,
                "line_ids": commands,
            }
        )
        recipe.action_approve()
        recipes[sku] = recipe
    ctx["recipes"] = recipes

    # --- BOMs for the semi-finished sauce ------------------------------
    env["mrp.bom"].create(
        {
            "product_tmpl_id": ingredients["ING-SAUCE"].product_tmpl_id.id,
            "product_qty": 20.0,
            "product_uom_id": ingredients["ING-SAUCE"].uom_id.id,
            "type": "normal",
            "bom_line_ids": [
                (0, 0, {"product_id": ingredients["ING-YOGH"].id, "product_qty": 0.6}),
                (0, 0, {"product_id": ingredients["ING-PICK"].id, "product_qty": 0.2}),
            ],
        }
    )

    # --- outlets, POS profiles, floors ---------------------------------
    outlets = {}
    warehouse = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
    cash_method = _payment_method(env, "Cash")
    for code, name, brand_code, fmt, seats in OUTLETS:
        outlet = env["rk.outlet"].create(
            {
                "name": name,
                "code": code,
                "brand_id": brands[brand_code].id,
                "format": fmt,
                "seats": seats,
                "warehouse_id": warehouse.id if warehouse else False,
                "channel_ids": [(6, 0, [channels[c].id for c in CHANNELS_BY_FORMAT.get(fmt, ["DINE"])])],
                "daypart_ids": [(6, 0, list(dayparts.values()) and [d.id for d in dayparts.values()])],
            }
        )
        config = env["pos.config"].create(
            {
                "name": name,
                "rk_outlet_id": outlet.id,
                "module_pos_restaurant": fmt in ("qsr", "fine", "cafe", "casual"),
                "payment_method_ids": [(6, 0, [cash_method.id])],
            }
        )
        if fmt in ("qsr", "fine", "cafe"):
            floor = env["restaurant.floor"].create(
                {"name": f"{name.split('—')[-1].strip()} floor", "pos_config_ids": [(4, config.id)]}
            )
            for number in range(1, 9):
                env["restaurant.table"].create(
                    {
                        "table_number": number,
                        "seats": random.choice([2, 2, 4, 4, 6]),
                        "floor_id": floor.id,
                    }
                )
        outlets[code] = outlet
    ctx["outlets"] = outlets

    # The core install already creates a placeholder central kitchen; adopt it
    # rather than colliding with the unique outlet code.
    central = env["rk.outlet"].search([("format", "=", "central_kitchen")], limit=1)
    central_vals = {
        "name": "Northline Central Kitchen",
        "brand_id": brands["BLZ"].id,
        "format": "central_kitchen",
        "warehouse_id": warehouse.id if warehouse else False,
        "channel_ids": [(6, 0, [channels["DELV"].id])],
        "seats": 0,
    }
    if central:
        central.write(central_vals)
    else:
        central = env["rk.outlet"].create(dict(central_vals, code="CK-01"))
    ctx["central"] = central

    # --- stations ------------------------------------------------------
    for outlet_code in ("BLZ-01", "SAF-01", "BRW-01"):
        outlet = outlets[outlet_code]
        grids = [
            ("Grill", "GRL", ["Burgers"], 12.0, True),
            ("Fry", "FRY", ["Sides"], 8.0, False),
            ("Cold / salad", "COLD", ["Coffee"], 5.0, False),
            ("Pass", "PASS", ["Bakery"], 4.0, False),
        ]
        for name, code, categs, target, is_default in grids:
            env["rk.station"].create(
                {
                    "name": name,
                    "code": code,
                    "outlet_id": outlet.id,
                    "target_minutes": target,
                    "is_default": is_default,
                    "pos_categ_ids": [(6, 0, [pos_categs[c].id for c in categs])],
                }
            )

    # --- par levels ----------------------------------------------------
    for outlet_code in ("BLZ-01", "BLZ-02", "SAF-01", "BRW-01"):
        outlet = outlets[outlet_code]
        for ing_sku in ("ING-BEEF", "ING-BUN", "ING-CHED", "ING-FRIE", "ING-RICE", "ING-COFF"):
            env["rk.par.level"].create(
                {
                    "outlet_id": outlet.id,
                    "product_id": ingredients[ing_sku].id,
                    "par_qty": random.randint(40, 120),
                    "min_qty": random.randint(10, 30),
                }
            )

    # --- trading history ------------------------------------------------
    today = fields.Date.context_today(env["rk.outlet"])
    orders_created = 0
    for outlet_code, outlet in outlets.items():
        if not outlet.pos_config_id:
            continue
        session = _open_session(env, outlet.pos_config_id)
        brand_products = [
            products[sku] for sku, brand_code, _ in MENU_BRAND if brand_code == outlet.brand_id.code
        ]
        if not brand_products:
            continue
        for offset in range(21, 0, -1):
            day = datetime.combine(today - timedelta(days=offset), datetime.min.time())
            for n in range(random.randint(6, 10)):
                _order(env, session, brand_products, day, n)
                orders_created += 1
    ctx["orders_created"] = orders_created

    # --- kitchen tickets: progress the newest ones ---------------------
    tickets = env["rk.kds.ticket"].search([("state", "=", "queued")], order="fired_at desc", limit=90)
    for index, ticket in enumerate(tickets):
        if index % 3 == 0:
            ticket.action_serve()
            ticket.write({"ready_at": ticket.fired_at + timedelta(minutes=random.randint(4, 22))})
        elif index % 3 == 1:
            ticket.action_ready()
        else:
            ticket.action_start()
    ctx["tickets"] = len(tickets)

    # --- indents, plan, dispatch ---------------------------------------
    par_outlet = outlets["BLZ-01"]
    indent = env["rk.indent"].create(
        {
            "outlet_id": par_outlet.id,
            "kitchen_id": central.id,
            "date_required": today + timedelta(days=1),
        }
    )
    indent.action_fill_from_par()
    indent.action_submit()
    indent.action_approve()

    indent2 = env["rk.indent"].create(
        {"outlet_id": outlets["BLZ-02"].id, "kitchen_id": central.id, "date_required": today + timedelta(days=1)}
    )
    indent2.action_fill_from_par()
    indent2.action_submit()
    indent2.action_approve()

    plan = env["rk.production.plan"].create(
        {"date": today + timedelta(days=1), "kitchen_id": central.id,
         "indent_ids": [(6, 0, (indent | indent2).ids)]}
    )
    plan.action_consolidate()
    plan.action_confirm()
    plan.action_create_manufacturing_orders()

    dispatch = env["rk.dispatch"].create(
        {"kitchen_id": central.id, "outlet_id": par_outlet.id, "indent_id": indent.id,
         "temperature_c": 3.0, "transport_reference": "VAN-01"}
    )
    dispatch.action_fill_from_indent()
    dispatch.action_dispatch()
    for line in dispatch.line_ids[:2]:
        line.qty_received = line.qty_sent - random.choice([1, 2])
        line.reason = "short"
    dispatch.action_confirm_receipt()

    # --- waste ----------------------------------------------------------
    reasons = env["rk.waste.reason"].search([])
    for outlet_code in ("BLZ-01", "SAF-01", "BRW-01"):
        for ing_sku in ("ING-BEEF", "ING-LETT", "ING-TOMA", "ING-MILK", "ING-BUN"):
            waste = env["rk.waste"].create(
                {
                    "outlet_id": outlets[outlet_code].id,
                    "product_id": ingredients[ing_sku].id,
                    "qty": random.choice([0.5, 1.0, 2.0, 3.0]),
                    "reason_id": random.choice(reasons).id,
                    "date": today - timedelta(days=random.randint(0, 6)),
                }
            )
            waste.action_submit()
            if waste.state == "submitted":
                waste.action_approve()

    # --- food safety -----------------------------------------------------
    checklist = env.ref("rk_food_safety.checklist_opening")
    for outlet_code in ("BLZ-01", "SAF-01", "BRW-01"):
        outlet = outlets[outlet_code]
        for offset in range(3):
            check = env["rk.haccp.check"].create(
                {
                    "checklist_id": checklist.id,
                    "outlet_id": outlet.id,
                    "date": datetime.now() - timedelta(days=offset),
                }
            )
            check.action_load_checkpoints()
            for line in check.line_ids.filtered("is_temperature"):
                breach = offset == 1 and line.name.startswith("Walk-in chiller")
                line.temp_value = 8.5 if breach else round(random.uniform(line.temp_min + 0.5, line.temp_max - 0.5), 1)
            if offset == 1:
                check.corrective_action = "Stock moved to the backup chiller; maintenance called at 09:10."
            check.action_validate()
        for equipment, name, low, high in (
            ("chiller", "Walk-in chiller", 0.0, 5.0),
            ("freezer", "Walk-in freezer", -22.0, -18.0),
            ("hot_hold", "Hot hold cabinet", 63.0, 90.0),
        ):
            for offset in range(4):
                env["rk.temperature.log"].create(
                    {
                        "outlet_id": outlet.id,
                        "equipment": equipment,
                        "equipment_name": name,
                        "value": round(random.uniform(low, high), 1),
                        "temp_min": low,
                        "temp_max": high,
                        "source": "sensor" if equipment == "freezer" else "manual",
                        "date": datetime.now() - timedelta(days=offset),
                    }
                )

    # --- forecasts -------------------------------------------------------
    forecast_outlets = env["rk.outlet"].browse([outlets[c].id for c in ("BLZ-01", "SAF-01", "BRW-01")])
    env["rk.forecast"]._generate_for(
        forecast_outlets, today - timedelta(days=6), today + timedelta(days=1), weeks=3
    )
    env["rk.forecast"]._cron_capture_actuals()

    # --- reservations -----------------------------------------------------
    guest_names = ["Ayesha Khan", "Bilal Ahmed", "Sana Iqbal", "Hamza Riaz", "Fatima Noor", "Usman Ali"]
    for index, guest in enumerate(guest_names):
        party_size = random.choice([2, 2, 4, 6])
        # A table must physically seat the party; the model refuses anything else.
        tables = env["restaurant.table"].search(
            [
                ("floor_id.pos_config_ids.rk_outlet_id", "=", outlets["SAF-01"].id),
                ("seats", ">=", party_size),
            ]
        )
        reservation = env["rk.reservation"].create(
            {
                "table_id": tables[index % len(tables)].id if tables else False,
                "guest_name": guest,
                "phone": f"+92 300 12345{index:02d}",
                "outlet_id": outlets["SAF-01"].id,
                "party_size": party_size,
                "start": datetime.now() + timedelta(days=index % 3, hours=19 - datetime.now().hour),
                "channel": random.choice(["phone", "web", "platform"]),
                "deposit_required": index % 3 == 0,
                "deposit_amount": 2000.0 if index % 3 == 0 else 0.0,
            }
        )
        if index % 4 == 0:
            reservation.action_cancel()
        elif index % 3 == 1:
            reservation.action_no_show()
        else:
            reservation.action_confirm()

    env["rk.waitlist"].create(
        {
            "outlet_id": outlets["SAF-01"].id,
            "guest_name": "Walk-in party",
            "party_size": 4,
            "quoted_minutes": 20,
        }
    )

    # --- catering event -----------------------------------------------------
    customer = env["res.partner"].create({"name": "Karachi Chamber of Commerce", "is_company": True})
    event = env["rk.event.order"].create(
        {
            "partner_id": customer.id,
            "outlet_id": outlets["SAF-01"].id,
            "event_date": today + timedelta(days=10),
            "headcount": 60,
            "service_style": "buffet",
            "venue": "Pearl Continental — Hall B",
            "line_ids": [
                (0, 0, {"product_id": products["MNU-BIRY"].id, "qty": 60, "price_unit": 17.0}),
                (0, 0, {"product_id": products["MNU-KARAHI"].id, "qty": 40, "price_unit": 21.0}),
                (0, 0, {"product_id": products["MNU-RICE"].id, "qty": 60, "price_unit": 5.0}),
            ],
        }
    )
    event.action_confirm()

    # --- aggregator orders ---------------------------------------------------
    outlet = outlets["BLZ-01"]
    for index in range(6):
        payload = {
            "order_reference": f"TAL-{9000 + index}",
            "outlet_id": outlet.id,
            "customer_name": f"Platform customer {index + 1}",
            "total": round(random.uniform(25, 95), 2),
            "lines": [
                {"product_id": products["MNU-SMASH"].id, "qty": 2, "price": 14.5},
                {"product_id": products["MNU-FRIES"].id, "qty": 1, "price": 6.5},
            ],
        }
        order = env["rk.aggregator.order"]._receive("TALABAT", payload)
        if index < 4:
            try:
                order.action_import_to_pos()
            except Exception:  # noqa: BLE001 - demo data must never block installation
                order.error_message = "Demo: no open session at import time."
    settlement = env["rk.aggregator.settlement"].create(
        {
            "platform_id": env.ref("rk_aggregator_hub.platform_talabat").id,
            "period_start": today - timedelta(days=21),
            "period_end": today,
            "reported_gross": 250.0,
            "reported_commission": 45.0,
            "reported_net": 205.0,
        }
    )
    settlement.action_collect_orders()

    # --- pricing rules ---------------------------------------------------------
    env["rk.pricing.rule"].create(
        {
            "name": "Happy hour — 25% off coffee",
            "code": "HH-COFFEE",
            "brand_id": brands["BRW"].id,
            "rule_type": "percent",
            "discount_pct": 25.0,
            "pos_categ_ids": [(6, 0, [pos_categs["Coffee"].id])],
            "daypart_ids": [(6, 0, [dayparts["DIN"].id])],
            "hour_from": 17.0,
            "hour_to": 19.0,
            "min_margin_pct": 40.0,
            "date_from": today - timedelta(days=30),
        }
    ).action_activate()
    env["rk.pricing.rule"].create(
        {
            "name": "All-day coffee + pastry — 15% off",
            "code": "BUNDLE-COFFEE",
            "brand_id": brands["BRW"].id,
            "rule_type": "percent",
            "discount_pct": 15.0,
            "pos_categ_ids": [(6, 0, [pos_categs["Coffee"].id])],
            "min_margin_pct": 40.0,
            "date_from": today - timedelta(days=30),
        }
    ).action_activate()
    env["rk.pricing.rule"].create(
        {
            "name": "Lunch combo — fixed 12.00",
            "code": "LUNCH-COMBO",
            "brand_id": brands["BLZ"].id,
            "rule_type": "fixed_price",
            "fixed_price": 12.0,
            "product_tmpl_ids": [(6, 0, [products["MNU-CHIKB"].product_tmpl_id.id])],
            "daypart_ids": [(6, 0, [dayparts["LUN"].id])],
            "min_margin_pct": 20.0,
            "date_from": today - timedelta(days=30),
        }
    ).action_activate()

    # --- franchisee + royalties ---------------------------------------------
    franchise_partner = env["res.partner"].create({"name": "Northline Franchising Ltd", "is_company": True})
    franchisee = env["rk.franchisee"].create(
        {
            "name": "Northline Franchising",
            "code": "NLF",
            "partner_id": franchise_partner.id,
            "royalty_pct": 6.0,
            "marketing_pct": 2.0,
            "minimum_monthly_fee": 500.0,
        }
    )
    franchise_outlet = env["rk.outlet"].create(
        {
            "name": "Blaze Burger — Islamabad (franchise)",
            "code": "BLZ-03F",
            "brand_id": brands["BLZ"].id,
            "format": "franchise",
            "franchisee_id": franchisee.id,
            "seats": 44,
            "warehouse_id": warehouse.id if warehouse else False,
            "channel_ids": [(6, 0, [channels[c].id for c in CHANNELS_BY_FORMAT["franchise"]])],
        }
    )
    franchise_config = env["pos.config"].create(
        {"name": "Blaze Burger — Islamabad (franchise)", "rk_outlet_id": franchise_outlet.id}
    )
    franchise_session = _open_session(env, franchise_config)
    franchise_products = [
        products[sku] for sku, brand_code, _ in MENU_BRAND if brand_code == "BLZ"
    ]
    for offset in range(21, 0, -1):
        day = datetime.combine(today - timedelta(days=offset), datetime.min.time())
        for n in range(random.randint(4, 7)):
            _order(env, franchise_session, franchise_products, day, n)
    ctx["franchisee"], ctx["franchise_outlet"] = franchisee, franchise_outlet

    statement = env["rk.royalty.statement"].create(
        {
            "franchisee_id": franchisee.id,
            "period_start": (today.replace(day=1) - timedelta(days=1)).replace(day=1),
            "period_end": today.replace(day=1) - timedelta(days=1),
        }
    )
    statement.action_calculate()
    if statement.line_ids:
        statement.action_confirm()

    # --- branch P&L + cash variance ------------------------------------------
    for outlet_code in ("BLZ-01", "SAF-01", "BRW-01"):
        outlet = outlets[outlet_code]
        for months_back in (1, 0):
            start = (today.replace(day=1) - timedelta(days=1)).replace(day=1) if months_back else today.replace(day=1)
            end = today.replace(day=1) - timedelta(days=1) if months_back else today
            period = env["rk.pnl.period"].create(
                {"outlet_id": outlet.id, "date_from": start, "date_to": end}
            )
            period.action_compute()
            if months_back:
                period.action_approve()
        env["rk.cash.variance"].create(
            {
                "outlet_id": outlet.id,
                "expected_cash": 4820.0,
                "counted_cash": 4790.0,
                "tolerance": 10.0,
                "explanation": "Till float rounding at close.",
                "state": "explained",
            }
        )

    # --- pricing drift on a platform menu ------------------------------------
    for index, sku in enumerate(("MNU-SMASH", "MNU-FRIES", "MNU-CHIKB")):
        line = env["rk.menu.sync"].create(
            {
                "platform_id": env.ref("rk_aggregator_hub.platform_talabat").id,
                "product_id": products[sku].id,
                "external_sku": sku,
                "platform_price": products[sku].lst_price + (1.5 if index == 1 else 0.0),
                "is_available": index != 2,
            }
        )
        line.action_check_drift()

    _logger.info(
        "rk_demo_data: %s outlets, %s recipes, %s POS orders, %s tickets seeded",
        len(outlets) + 1, len(recipes) + 1, orders_created, ctx.get("tickets", 0),
    )
    return ctx


#: First outlet the hook creates. Its presence means the group is already there.
DEMO_MARKER_CODE = "BLZ-01"


def post_init_hook(env):
    env = env(user=SUPERUSER_ID)
    # Odoo may load the registry twice (for instance with -i and -u together),
    # so the hook must be safe to call on a database it has already seeded.
    if env["rk.outlet"].search([("code", "=", DEMO_MARKER_CODE)], limit=1):
        _logger.info("rk_demo_data: demo group already present, skipping")
        return
    # Odoo loads a chart of accounts lazily, *after* the last module installs.
    # If we build POS journals first, that late load deletes them and takes the
    # POS configuration (and its sessions) with it. Load the chart now.
    if not env.company.chart_template:
        env["account.chart.template"].try_loading("generic_coa", env.company, install_demo=False)

    _logger.info("rk_demo_data: building the demo restaurant group…")
    _seed(env)
    _logger.info("rk_demo_data: demo dataset ready")
