from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    rent_ok = fields.Boolean(
        string="Can be Rented",
        help="Allow this product to be booked on rental orders.",
    )
    rental_pricing_ids = fields.One2many(
        "rental.pricing", "product_tmpl_id", string="Rental Pricing"
    )
    min_rental_duration = fields.Integer(
        string="Minimum Rental Duration",
        default=1,
        help="Smallest amount of duration units a customer can rent this product for.",
    )
    extra_hourly_late_fee = fields.Monetary(
        string="Late Return Fee (per hour)",
        currency_field="currency_id",
        help="Fee charged per hour a rented unit of this product is returned late.",
    )
