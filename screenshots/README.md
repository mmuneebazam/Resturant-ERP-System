# Screenshots

This folder holds screenshots of the demo dataset. They are captured from a
fresh `docker compose up` of `rk_demo_data` and are regenerated when the demo
data changes.

Planned set (one image each):

| File | Screen |
|---|---|
| `01-outlets.png` | Outlets list: seven outlets, four formats, brand colours |
| `02-recipe-cost.png` | Recipe form with sub-recipe, waste and live cost roll-up |
| `03-kds.png` | Kitchen display kanban with an SLA breach |
| `04-variance.png` | Usage variance wizard and the outlet scorecard |
| `05-forecast.png` | Forecast pivot: planned vs actual by day-part |
| `06-aggregator.png` | Platform order import and a disputed settlement |
| `07-franchise.png` | Royalty statement with the minimum-fee top-up |
| `08-pnl.png` | Outlet P&L with prime cost against the brand target |

> Status: batch not captured yet. The dataset it comes from is installed and
> verified (see `rk_demo_data`), so capturing is a `make screenshots` away once
> a headless browser is added to CI.
