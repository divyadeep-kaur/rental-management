# Rental Management

An Odoo 17 addon that turns any product into a rentable item and manages
the full rental lifecycle: quotation, confirmation, pickup, return, and
invoicing.

Built for the Odoo Hackathon 2025 "Rental Management" problem statement.

## Features (current)

- **Rental product management** — mark products as rentable, configure
  minimum rental duration, and set per-unit rental pricing (hour, day,
  week, month, year), optionally scoped to a pricelist.
- **Quotations → Orders** — build a rental quotation with one or more
  lines, confirm it into a rental order.
- **Pickup / Return tracking** — move a confirmed order through
  Reserved → Picked Up → Returned, recording actual pickup/return times.
- **Flexible invoicing** — invoice the full amount upfront or a partial
  deposit, and automatically compute late-return fees based on how long
  a product comes back after its planned return time.

Not yet implemented from the full problem statement: customer self-service
portal/online booking, notifications, payment gateway integration, and
reporting dashboards.

## Running it locally

This repo ships a `docker-compose.yml` that runs Odoo 17 with Postgres
and mounts `rental_management/` as an addon.

```bash
docker compose up
```

Then open http://localhost:8069, create a database, and install the
**Rental Management** app from Apps (enable developer mode / "Update Apps
List" first since this is a local addon).

## Running the tests

With the stack running:

```bash
docker compose run --rm odoo odoo -i rental_management --test-enable --stop-after-init -d rental_test
```

## Module layout

```
rental_management/
├── models/         # product.template, rental.order(.line), rental.pricing, account.move
├── views/          # form/list/search views and menus
├── security/       # access rights
├── data/           # sequences
└── tests/          # TransactionCase tests for the order lifecycle
```
