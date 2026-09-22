from odoo import api, fields, models
from odoo.exceptions import UserError


class RentalOrder(models.Model):
    _name = "rental.order"
    _description = "Rental Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_order desc, id desc"

    name = fields.Char(
        string="Reference", required=True, copy=False, readonly=True, default="New"
    )
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")
    date_order = fields.Datetime(
        string="Order Date", default=fields.Datetime.now, required=True
    )
    rental_start_date = fields.Datetime(string="Rental Start", required=True)
    rental_end_date = fields.Datetime(string="Rental End", required=True)
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("confirmed", "Rental Order"),
            ("picked_up", "Picked Up"),
            ("returned", "Returned"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    order_line_ids = fields.One2many(
        "rental.order.line", "order_id", string="Rental Lines", copy=True
    )
    payment_type = fields.Selection(
        [("full", "Full Upfront Payment"), ("partial", "Partial Deposit")],
        default="full",
        required=True,
        string="Payment Terms",
    )
    deposit_percentage = fields.Float(
        string="Deposit (%)",
        default=30.0,
        help="Percentage of the total charged upfront when Payment Terms is Partial Deposit.",
    )
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company
    )
    amount_untaxed = fields.Monetary(
        string="Untaxed Amount", compute="_compute_amounts", store=True
    )
    late_fee_total = fields.Monetary(
        string="Late Fees", compute="_compute_amounts", store=True
    )
    amount_total = fields.Monetary(
        string="Total", compute="_compute_amounts", store=True
    )
    invoice_ids = fields.One2many("account.move", "rental_order_id", string="Invoices")
    invoice_count = fields.Integer(compute="_compute_invoice_count")

    @api.depends("order_line_ids.price_subtotal", "order_line_ids.late_fee")
    def _compute_amounts(self):
        for order in self:
            order.amount_untaxed = sum(order.order_line_ids.mapped("price_subtotal"))
            order.late_fee_total = sum(order.order_line_ids.mapped("late_fee"))
            order.amount_total = order.amount_untaxed + order.late_fee_total

    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = len(order.invoice_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "rental.order"
                ) or "New"
        return super().create(vals_list)

    def action_confirm(self):
        for order in self:
            if not order.order_line_ids:
                raise UserError("Add at least one rental line before confirming.")
            order.order_line_ids.write({"state": "reserved"})
            order.order_line_ids.check_availability()
            order.state = "confirmed"

    def action_pickup(self):
        for order in self:
            if order.state != "confirmed":
                raise UserError("Only confirmed rental orders can be picked up.")
            order.order_line_ids.write(
                {"state": "picked_up", "actual_pickup_date": fields.Datetime.now()}
            )
            order.state = "picked_up"

    def action_return(self):
        for order in self:
            if order.state != "picked_up":
                raise UserError("Only picked up rental orders can be returned.")
            for line in order.order_line_ids:
                line.actual_return_date = fields.Datetime.now()
                line.state = "returned"
                line._compute_late_fee()
            order.state = "returned"

    def action_cancel(self):
        for order in self:
            if order.state in ("picked_up", "returned"):
                raise UserError("Cannot cancel a rental order that has already been picked up.")
            order.order_line_ids.write({"state": "cancelled"})
            order.state = "cancelled"

    def action_draft(self):
        self.write({"state": "draft"})

    def action_view_invoices(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Invoices",
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", self.invoice_ids.ids)],
        }

    def action_create_invoice(self):
        self.ensure_one()
        if self.state not in ("confirmed", "picked_up", "returned"):
            raise UserError("Confirm the rental order before invoicing it.")

        amount = self.amount_untaxed
        if self.payment_type == "partial" and self.state == "confirmed":
            amount = self.amount_untaxed * (self.deposit_percentage / 100.0)
        else:
            amount += self.late_fee_total

        invoice_lines = [
            (
                0,
                0,
                {
                    "name": f"{self.name} - {'Deposit' if self.payment_type == 'partial' and self.state == 'confirmed' else 'Rental charges'}",
                    "quantity": 1,
                    "price_unit": amount,
                },
            )
        ]
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_id.id,
                "invoice_origin": self.name,
                "rental_order_id": self.id,
                "invoice_line_ids": invoice_lines,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "target": "current",
        }
