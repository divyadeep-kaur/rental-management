from odoo import api, fields, models


class RentalOrderLine(models.Model):
    _name = "rental.order.line"
    _description = "Rental Order Line"

    order_id = fields.Many2one(
        "rental.order", string="Rental Order", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one(
        "product.product", string="Product", required=True, domain=[("rent_ok", "=", True)]
    )
    product_tmpl_id = fields.Many2one(
        related="product_id.product_tmpl_id", store=True
    )
    quantity = fields.Integer(string="Quantity", default=1, required=True)
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
    duration = fields.Integer(string="Duration", default=1, required=True)
    price_unit = fields.Monetary(
        string="Unit Price", compute="_compute_price_unit", store=True, readonly=False
    )
    price_subtotal = fields.Monetary(
        string="Subtotal", compute="_compute_price_subtotal", store=True
    )
    currency_id = fields.Many2one(related="order_id.currency_id", store=True)
    planned_pickup_date = fields.Datetime(string="Planned Pickup")
    planned_return_date = fields.Datetime(string="Planned Return")
    actual_pickup_date = fields.Datetime(string="Actual Pickup")
    actual_return_date = fields.Datetime(string="Actual Return")
    late_fee = fields.Monetary(string="Late Fee", default=0.0)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("reserved", "Reserved"),
            ("picked_up", "Picked Up"),
            ("returned", "Returned"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
    )

    @api.depends("product_tmpl_id", "duration_unit", "order_id.pricelist_id")
    def _compute_price_unit(self):
        pricing_model = self.env["rental.pricing"]
        for line in self:
            if not line.product_tmpl_id:
                line.price_unit = 0.0
                continue
            price, discount = pricing_model.get_best_price(
                line.product_tmpl_id.id,
                line.duration_unit,
                line.order_id.pricelist_id.id if line.order_id.pricelist_id else None,
            )
            line.price_unit = price * (1 - discount / 100.0)

    @api.depends("price_unit", "quantity", "duration")
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.quantity * line.duration

    def _compute_late_fee(self):
        for line in self:
            if not (line.actual_return_date and line.planned_return_date):
                continue
            if line.actual_return_date <= line.planned_return_date:
                line.late_fee = 0.0
                continue
            delta = line.actual_return_date - line.planned_return_date
            late_hours = delta.total_seconds() / 3600.0
            rate = line.product_tmpl_id.extra_hourly_late_fee
            line.late_fee = late_hours * rate * line.quantity
