[README.md](https://github.com/user-attachments/files/33762158/README.md)
<div align="center">

<img src="assets/banner.svg" alt="Restaurant Kit for Odoo 19" width="100%">

<br>

![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67?style=for-the-badge&logo=odoo&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-LGPL--3-34d399?style=for-the-badge)

![Modules](https://img.shields.io/badge/custom_modules-13-ff7a18?style=flat-square)
![Apps](https://img.shields.io/badge/standard_apps-13-0f172a?style=flat-square)
![Demo data](https://img.shields.io/badge/demo_dataset-included-22d3ee?style=flat-square)
![Community](https://img.shields.io/badge/edition-Community%20first-64748b?style=flat-square)

**A working, installable restaurant ERP for Odoo 19 Community — every format, one platform.**
Multi-brand outlets · recipes that behave like engineering data · a central kitchen that
dispatches · a kitchen display that measures itself · food safety that survives an audit ·
aggregator money that reconciles · franchise royalties that can be reproduced with a calculator.

[Quick start](#-quick-start) · [Modules](#-the-13-modules) · [Screens](#-what-it-looks-like) · [Architecture](#-architecture) · [Docs](docs/) · [Roadmap](#-roadmap)

</div>

---

## Why this repository exists

A restaurant group does not fail because it lacks software. It fails because twelve formats,
forty outlets, four channels and eight franchisees each ended up with their own POS, their own
spreadsheet and their own version of the truth. This repository is the **executable answer** to
the classic enterprise delivery plan: a governed Odoo 19 core plus the custom modules that a
multi-brand food-service group actually needs.

It is built as a **demo project you can install and click through in ten minutes**, and as a
**reference implementation you can read** — the logic that usually hides inside a consultant's
head (recipe roll-up, variance, royalty calculation, capacity checks) is here as code with tests.

> **Scope note.** This is a demonstration project, not a certified product. It targets
> **Odoo 19 Community**, because that is what anyone can install today. Where the original
> programme assumed Enterprise apps (Quality, Planning, Helpdesk, Studio, IoT), this kit
> implements the same *outcome* with community-safe models instead of pretending the app exists.

---

## ✨ What you get

| Area | What's inside |
|---|---|
| 🍔 **One data model for every format** | `rk.brand`, `rk.outlet`, `rk.channel`, `rk.daypart` — QSR, casual, fine dining, café, cloud kitchen, central kitchen, catering, franchise |
| 🧾 **Recipes as governed data** | Versioned recipes, sub-recipes, yield, waste allowance, labour, overhead, live cost roll-up, price simulation, margin alerts |
| 🏭 **Central kitchen** | Par levels → indents → consolidated production plan → manufacturing orders → dispatch → receipt with discrepancies |
| 👨‍🍳 **Kitchen display** | Station routing by POS category, ticket timers, bump/expedite, SLA escalation, service-speed reporting |
| 🗑️ **Wastage & variance** | Reason codes with approval thresholds, real stock scraps, theoretical vs actual usage, outlet scorecards |
| 🌡️ **Food safety** | HACCP checklists with temperature ranges, sensor-ready temperature logs, lot traceability, recall workflow, expiry labels |
| 📈 **Demand forecasting** | Weekday-seasonal forecast per item/outlet/day-part, suggested prep and purchase, manager overrides, accuracy (WAPE) tracking |
| 🛵 **Aggregator hub** | Idempotent platform order import, product matching, menu/price sync, commission-aware settlements with reconciliation |
| 📅 **Front of house** | Reservations with table conflict detection, deposits, no-show rules, waitlist, turn-time analytics |
| 🏷️ **Pricing & promotions** | Day-part and happy-hour pricing, channel price lists, promotion conflicts, margin guardrails that block bad discounts |
| 🎉 **Catering & banquets** | Event orders, headcount pricing, capacity checks, staffing estimate, deposit/balance milestone invoicing |
| 🤝 **Franchise** | Royalty + marketing fee on net sales, minimum monthly fee, supply charge-back, price compliance, invoiced settlements with a worked example |
| 📊 **Branch P&L & labour** | Outlet P&L from POS + recipes + attendance + ledger, prime cost, day-part labour, cash variance with approval |
| 🎬 **Demo dataset** | One optional module fills the whole thing with a coherent, cross-linked restaurant group |
| 📚 **Docs that match the code** | Architecture, data model, KPI dictionary, deployment notes, changelog |

---

## 🚀 Quick start

### Option A — Docker (fastest)

```bash
git clone https://github.com/restaurant-kit/odoo19-restaurant-erp.git
cd odoo19-restaurant-erp
docker compose up -d
```

Then open <http://localhost:8069>.

| | |
|---|---|
| **Database** | `restaurantkit` (created on first run) |
| **Login** | `admin` / `admin` |
| **Installed** | all 13 modules + the demo dataset |

To start empty instead, delete `--init=rk_demo_data` from `docker-compose.yml` and remove the volumes.
Full deployment notes, including the production checklist: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

### Option B — Local source install

```bash
# 1. Odoo 19 Community source + virtualenv
git clone --depth 1 -b 19.0 https://github.com/odoo/odoo.git odoo19
python3 -m venv .venv && source .venv/bin/activate
pip install -r odoo19/requirements.txt

# 2. PostgreSQL
createdb rk_demo

# 3. Install the kit (addons_path = this repository)
./odoo19/odoo-bin \
  --addons-path=./odoo19/addons,$(pwd) \
  --db_host=localhost --db_user=$USER \
  -d rk_demo -i rk_demo_data \
  --without-demo=True
```

### Option C — Add to an existing Odoo 19 database

Add this repository to `addons_path`, restart Odoo, enable developer mode, then
**Apps → Update Apps List → Restaurant Kit — Core** and install the modules you want.
Install `rk_demo_data` **only** if you want the demo dataset.

> **Demo data is destructive to a clean story.** Install it on a fresh database. It creates
> outlets, products, recipes, 45 days of POS orders, employees and a franchisee.

---

## 🧱 The 13 modules

Dependency column shows what a module builds on. `rk_restaurant_core` is the shared foundation,
so brands, channels, day-parts and outlets are defined exactly once.

| # | Module | Depends on | What it does | Key models |
|---|---|---|---|---|
| 0 | **`rk_restaurant_core`** | POS, POS Restaurant, Analytic | Brands, channels, day-parts, outlet formats, security groups, analytic plumbing, the kit's root menu | `rk.brand`, `rk.channel`, `rk.daypart`, `rk.outlet` |
| 1 | **`rk_recipe_costing`** | Core, Product, UoM, Stock | Versioned recipes, yield, waste, sub-recipes, live cost roll-up, price simulation, margin alerts | `rk.recipe`, `rk.recipe.line`, `rk.recipe.cost.alert`, `rk.recipe.price.simulation` |
| 2 | **`rk_central_kitchen`** | Core, Recipe Costing, MRP, Stock, Purchase | Par levels, indents, consolidated production plans, manufacturing orders, dispatch, receipt variance | `rk.par.level`, `rk.indent`, `rk.production.plan`, `rk.dispatch` |
| 3 | **`rk_kds_routing`** | Core, Recipe Costing, POS, POS Restaurant | Station routing by POS category, tickets, prep timers, bump/expedite, SLA risk and breach | `rk.station`, `rk.kds.ticket`, `rk.kds.ticket.line` |
| 4 | **`rk_wastage_variance`** | Core, Recipe Costing, POS, Stock | Reason-coded waste with approval thresholds, stock scrap, theoretical vs actual usage, scorecards | `rk.waste.reason`, `rk.waste`, `rk.variance.wizard`, `rk.outlet.scorecard` |
| 5 | **`rk_food_safety`** | Core, Stock | HACCP checklists with temperature ranges, sensor-ready temperature logs, lot traceability, recall workflow | `rk.haccp.checklist`, `rk.haccp.check`, `rk.temperature.log`, `rk.recall` |
| 6 | **`rk_demand_forecast`** | Core, Recipe Costing, POS | Weekday-seasonal forecasts per item/outlet/day-part, prep and purchase suggestions, overrides, WAPE accuracy | `rk.forecast` |
| 7 | **`rk_aggregator_hub`** | Core, POS, Accounting | Idempotent platform order intake, POS import, menu and price drift, commission-aware settlements | `rk.aggregator.platform`, `rk.aggregator.order`, `rk.aggregator.settlement`, `rk.menu.sync` |
| 8 | **`rk_reservations`** | Core, POS Restaurant, POS | Bookings, table conflict detection, deposits, no-show flagging, waitlist, turn-time data | `rk.reservation`, `rk.waitlist` |
| 9 | **`rk_pricing_promotions`** | Core, Recipe Costing, POS, Product | Day-part pricing, happy hour, promotion conflicts, margin guardrails, pricelist generation | `rk.pricing.rule` |
| 10 | **`rk_special_orders`** | Core, Recipe Costing, Sales, Accounting | Catering orders, capacity checks, staffing estimates, deposit and balance invoicing | `rk.event.order`, `rk.event.order.line` |
| 11 | **`rk_franchise`** | Core, POS, Accounting, Sales | Franchisee terms, royalty and marketing fees, minimum monthly fee, invoicing | `rk.franchisee`, `rk.royalty.statement`, `rk.royalty.statement.line` |
| 12 | **`rk_branch_pnl_labour`** | Core, Recipe Costing, Wastage, POS, Attendance, Accounting, Analytic | Outlet P&L, prime cost, labour by day-part, cash variance with approval | `rk.pnl.period`, `rk.pnl.labour.line`, `rk.cash.variance` |
| ✨ | **`rk_demo_data`** | all of the above | Optional: a populated, cross-linked demo group seeded through the ORM | — |

---

## 🏗 Architecture

<img src="assets/architecture.svg" alt="Restaurant Kit architecture" width="100%">

Three deliberate design decisions:

1. **`rk.outlet`, not `pos.config`, is the operational unit.** A central kitchen has stock,
   production and dispatches but never opens a POS session. Linking every module to `pos.config`
   would have excluded the kitchen from the model that everything else depends on.
2. **Transaction-derived reporting.** Branch P&L, variance, food cost and royalties are computed
   from POS orders, stock moves, attendance and recipes — not typed in, not exported, not
   "adjusted at month-end". If the number is wrong, the transaction is wrong and you can find it.
3. **Data, not code, for local variation.** Day-parts, channels, reason codes, stations, par
   levels, approval thresholds and promotion rules are records. Adding an outlet, a brand, a
   platform or a country changes data — which is what keeps twelve variants from becoming twelve
   codebases.

Full write-up: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · data model: [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) · KPI definitions: [`docs/KPI_DICTIONARY.md`](docs/KPI_DICTIONARY.md).

---

## 🖼 What it looks like

The demo dataset produces a navigable group: three brands and seven outlets
(QSR, fine dining, café, cloud kitchen, franchise, central kitchen), 24
ingredients, 12 menu items with recipes and a sub-recipe, **~830 paid POS orders**
across three weeks, **~740 kitchen tickets** with SLA breaches, HACCP checks
including a recorded cold-chain failure, forecasts with captured actuals,
reservations on real tables, a 60-cover catering job, platform orders with a
disputed settlement, pricing rules, and a franchisee with a royalty statement.
Verified: `-i rk_demo_data` on a clean Odoo 19 database completes with zero
errors, and the 12 business-logic suites stay green on the resulting database.

```bash
docker compose up -d          # then: Restaurant Kit → Forecasts / Kitchen / Outlets …
```

Screenshots are captured from that dataset and land in [`screenshots/`](screenshots/)
— see the roadmap for the current state of that batch.

---

## 🔌 Integrations, honestly

The kit runs **without** any third-party account. Where an external system is expected, the
seam is explicit:

| Seam | Implementation here | What production adds |
|---|---|---|
| Delivery platforms | `rk.aggregator.order._receive(platform_code, payload)` + POS import action | Partner API adapters in middleware, signature verification, webhook registration |
| Menu & price push | `rk.menu.sync` rows + `action_push()` and a nightly drift job | Real API calls per platform, rate limiting, dead-letter queue |
| Payment terminals | Standard Odoo POS payment methods | Terminal drivers, tokenization (no card data in Odoo) |
| Temperature sensors | `rk.temperature.log` accepts `source = sensor/iot` | MQTT/HTTP gateway into the same model |
| Tax / e-invoicing | Standard Odoo localization + fiscal positions | Country-specific certification, fiscal POS reporting |
| BI | Read from replicated PostgreSQL | Power BI model, row-level security, refresh windows |

---

## 🧪 Tests

Business logic is covered with Odoo `TransactionCase` tests, all green on
Odoo 19 Community. Per-module counts from the last full run:

```
rk_recipe_costing      8 tests   sub-recipes, waste, cycle detection, alerts, price simulation
rk_reservations        6 tests   overlap rule, back-to-back, seats, lifecycle
rk_food_safety         5 tests   HACCP pass/fail, corrective action, temperature range
rk_pricing_promotions  5 tests   happy hour window, margin guardrail, best price
rk_special_orders      5 tests   deposit maths, capacity guard, staffing
rk_franchise           5 tests   minimum fee, percentage validation, totals
rk_branch_pnl_labour   5 tests   prime cost, alert status, cash variance
rk_aggregator_hub      4 tests   idempotent intake, settlement matching
rk_demand_forecast     4 tests   WAPE, accuracy, override precedence
rk_kds_routing         4 tests   station routing, ticket lifecycle
rk_wastage_variance    4 tests   usage explosion, approval flow
                      ──
    runner output: "0 failed, 0 error(s) of 33 tests when loading database"
```

```bash
# All suites against a fresh database
python odoo19/odoo-bin --addons-path=odoo19/addons,$(pwd) -d rk_test \
  --test-tags /rk_recipe_costing,/rk_central_kitchen,/rk_kds_routing,/rk_wastage_variance,\
/rk_food_safety,/rk_demand_forecast,/rk_aggregator_hub,/rk_reservations,\
/rk_pricing_promotions,/rk_special_orders,/rk_franchise,/rk_branch_pnl_labour \
  -u rk_recipe_costing,rk_central_kitchen,rk_kds_routing,rk_wastage_variance,\
rk_food_safety,rk_demand_forecast,rk_aggregator_hub,rk_reservations,\
rk_pricing_promotions,rk_special_orders,rk_franchise,rk_branch_pnl_labour \
  --stop-after-init

make test   # same thing, shorter
```

CI runs the same suite plus a lint pass and a demo-data install
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

---

## 🗺 Roadmap

- [x] Core dimensions, recipes, central kitchen, KDS, wastage, food safety
- [x] Forecasting, aggregator hub, reservations, pricing, catering, franchise, branch P&L
- [x] Demo dataset + docs (architecture, data model, KPI dictionary, deployment)
- [ ] Screenshot batch from the demo dataset
- [ ] OWL kitchen display app (real-time bus instead of kanban refresh)
- [ ] Middleware reference implementation (FastAPI + queue) for aggregator webhooks
- [ ] Odoo 20 upgrade branch with automated regression suite
- [ ] Excel/Power BI semantic model starter
- [ ] Payroll localization integration for labour cost

---

## 📄 Licence

LGPL-3.0 — the same licence as Odoo Community. See [LICENSE](LICENSE).

## 🙏 Credits & disclaimer

Built as a demonstration of a multi-brand restaurant ERP programme on Odoo 19. Client names,
figures and outlets are fictional. Odoo field names, editions and third-party APIs change:
verify every mechanic against current official documentation and local regulations before
running anything commercially.
