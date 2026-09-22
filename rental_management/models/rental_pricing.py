from odoo import api, fields, models


class RentalPricing(models.Model):
    _name = "rental.pricing"
    _description = "Rental Pricing Rule"
    _order = "product_tmpl_id, duration_unit"

    product_tmpl_id = fields.Many2one(
        "product.template", string="Product", required=True, ondelete="cascade"
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Pricelist",
        help="Restrict this rate to a specific pricelist. Leave empty to use it as the default rate.",
    )
    duration_unit = fields.Selection(
        [
            ("hour", "Hour"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
            ("year", "Year"),
        ],
        string="Duration Unit",
        required=True,
        default="day",
    )
    price = fields.Monetary(string="Price", required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    discount = fields.Float(
        string="Discount (%)",
        help="Percentage discount applied on top of this rate, e.g. for seasonal promotions.",
    )

    _sql_constraints = [
        (
            "price_positive",
            "CHECK(price >= 0)",
            "Rental price must be positive.",
        ),
    ]

    @api.model
    def get_best_price(self, product_tmpl_id, duration_unit, pricelist_id=None):
        """Return the (price, discount) tuple that applies for a product/unit/pricelist."""
        domain = [
            ("product_tmpl_id", "=", product_tmpl_id),
            ("duration_unit", "=", duration_unit),
        ]
        rule = self.env["rental.pricing"]
        if pricelist_id:
            rule = self.search(domain + [("pricelist_id", "=", pricelist_id)], limit=1)
        if not rule:
            rule = self.search(domain + [("pricelist_id", "=", False)], limit=1)
        return (rule.price, rule.discount) if rule else (0.0, 0.0)
