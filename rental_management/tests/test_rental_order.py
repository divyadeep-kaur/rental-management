from datetime import timedelta

from odoo.fields import Datetime
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRentalOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "Camera Kit",
                "rent_ok": True,
                "extra_hourly_late_fee": 5.0,
            }
        )
        cls.env["rental.pricing"].create(
            {
                "product_tmpl_id": cls.product_tmpl.id,
                "duration_unit": "day",
                "price": 50.0,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Rental Customer"})

    def _create_order(self):
        now = Datetime.now()
        return self.env["rental.order"].create(
            {
                "partner_id": self.partner.id,
                "rental_start_date": now,
                "rental_end_date": now + timedelta(days=3),
                "order_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_tmpl.product_variant_id.id,
                            "quantity": 2,
                            "duration_unit": "day",
                            "duration": 3,
                            "planned_pickup_date": now,
                            "planned_return_date": now + timedelta(days=3),
                        },
                    )
                ],
            }
        )

    def test_pricing_and_subtotal(self):
        order = self._create_order()
        line = order.order_line_ids
        self.assertEqual(line.price_unit, 50.0)
        self.assertEqual(line.price_subtotal, 50.0 * 2 * 3)

    def test_state_flow_and_sequence(self):
        order = self._create_order()
        self.assertTrue(order.name.startswith("RENT/"))
        self.assertEqual(order.state, "draft")

        order.action_confirm()
        self.assertEqual(order.state, "confirmed")
        self.assertEqual(order.order_line_ids.state, "reserved")

        order.action_pickup()
        self.assertEqual(order.state, "picked_up")
        self.assertTrue(order.order_line_ids.actual_pickup_date)

        order.action_return()
        self.assertEqual(order.state, "returned")
        self.assertTrue(order.order_line_ids.actual_return_date)

    def test_late_fee_computation(self):
        order = self._create_order()
        order.action_confirm()
        order.action_pickup()

        line = order.order_line_ids
        line.actual_return_date = line.planned_return_date + timedelta(hours=4)
        line._compute_late_fee()

        # 4 hours late * 5.0/hour * 2 quantity
        self.assertEqual(line.late_fee, 40.0)

    def test_create_invoice_full_payment(self):
        order = self._create_order()
        order.action_confirm()
        action = order.action_create_invoice()
        invoice = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(invoice.rental_order_id, order)
        self.assertEqual(len(order.invoice_ids), 1)
