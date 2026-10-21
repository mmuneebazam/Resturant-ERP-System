# Security

## Reporting

Open a private security advisory on the repository, or email the maintainer
listed in `__manifest__.py`. Please do not open a public issue for a
vulnerability.

## What this project protects and what it does not

* Access control is Odoo's own: `group_rk_user`, `group_rk_manager` and
  `group_rk_finance` gate every model through `ir.model.access.csv`. Finance
  can post invoices and settle royalties; users cannot.
* No secrets, API keys or partner credentials live in this repository, and no
  module calls a third-party API. Integrations are explicit seams
  (`rk.aggregator.order._receive`, `rk.menu.sync.action_push`) that middleware
  fills in.
* Temperature sensors, delivery platforms and payment terminals are *not*
  connected. If you connect them, terminate TLS at the edge, verify webhook
  signatures before calling `_receive`, and never store card data in Odoo.
* The demo dataset creates users, partners and orders. Do not install
  `rk_demo_data` on a database that holds real data.
