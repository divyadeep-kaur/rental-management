{
    "name": "Rental Management",
    "version": "17.0.1.0.0",
    "summary": "Manage rentable products, quotations, pickup/return and rental invoicing",
    "description": """
Rental Management
==================
A unified platform to manage rentable products, schedule pickups and
returns, and generate rental-specific invoices.

Features
--------
* Mark any product as rentable and configure per-unit rental pricing
  (hour, day, week, month, year).
* Rental quotations that confirm into rental orders and generate
  rental contracts.
* Reservation -> Pickup -> Return flow that keeps stock in sync.
* Multiple pricelists with time-dependent pricing and discount rules.
* Flexible invoicing: full upfront payment, partial deposit, and
  automatic late-return fees.
""",
    "category": "Sales/Rental",
    "author": "Divyadeep Kaur",
    "license": "LGPL-3",
    "depends": ["sale_management", "stock", "account", "portal", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/rental_security.xml",
        "data/rental_sequence.xml",
        "data/rental_mail_data.xml",
        "data/rental_cron.xml",
        "views/product_template_views.xml",
        "views/rental_pricing_views.xml",
        "views/rental_order_views.xml",
        "views/rental_menus.xml",
        "views/portal_templates.xml",
    ],
    "demo": [
        "data/rental_demo_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "rental_management/static/src/css/rental_portal.css",
            "rental_management/static/src/js/rental_portal.js",
        ],
    },
    "installable": True,
    "application": True,
}
