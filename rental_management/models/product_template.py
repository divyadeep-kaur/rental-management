from odoo import api, fields, models


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
    rental_day_price = fields.Monetary(
        string="Rental Price (per day)",
        compute="_compute_rental_day_price",
        currency_field="currency_id",
        help="Default per-day rental rate shown on the shop page, falling back to the sales price if none is configured.",
    )

    @api.depends("rental_pricing_ids.duration_unit", "rental_pricing_ids.pricelist_id", "rental_pricing_ids.price", "list_price")
    def _compute_rental_day_price(self):
        for product in self:
            day_rate = product.rental_pricing_ids.filtered(
                lambda p: p.duration_unit == "day" and not p.pricelist_id
            )[:1]
            product.rental_day_price = day_rate.price if day_rate else product.list_price
