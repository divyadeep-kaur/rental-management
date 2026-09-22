from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    rental_order_id = fields.Many2one("rental.order", string="Rental Order")
