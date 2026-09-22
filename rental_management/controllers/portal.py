from datetime import datetime

from odoo import fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


def _parse_datetime_local(value):
    """Convert an HTML <input type="datetime-local"> value ('YYYY-MM-DDTHH:MM')
    into an Odoo-compatible datetime string, or None if empty/invalid."""
    if not value:
        return None
    try:
        return fields.Datetime.to_string(datetime.strptime(value, "%Y-%m-%dT%H:%M"))
    except ValueError:
        return None


class RentalShopController(http.Controller):
    @http.route(["/rental/shop"], type="http", auth="public", website=True, sitemap=False)
    def rental_shop(self, **kwargs):
        products = (
            request.env["product.template"]
            .sudo()
            .search([("rent_ok", "=", True), ("sale_ok", "=", True)])
        )
        return request.render(
            "rental_management.rental_shop_page",
            {"products": products},
        )

    @http.route(
        ["/rental/shop/<int:product_id>"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def rental_shop_product(self, product_id, **kwargs):
        product = request.env["product.template"].sudo().browse(product_id)
        if not product.exists() or not product.rent_ok:
            return request.not_found()
        return request.render(
            "rental_management.rental_shop_product_page",
            {
                "product": product,
                "error": kwargs.get("error"),
                "is_public_user": request.env.user._is_public(),
            },
        )

    @http.route(["/rental/request"], type="http", auth="public", website=True, methods=["GET"])
    def rental_request_get(self, **kwargs):
        # A stray GET here (e.g. after a login redirect) shouldn't 405 - send
        # the visitor back to the shop instead of crashing.
        return request.redirect("/rental/shop")

    @http.route(["/rental/request"], type="http", auth="user", website=True, methods=["POST"])
    def rental_request(self, **post):
        product_id = int(post.get("product_id", 0))
        quantity = int(post.get("quantity", 1) or 1)
        duration = int(post.get("duration", 1) or 1)
        duration_unit = post.get("duration_unit", "day")
        pickup_date = _parse_datetime_local(post.get("planned_pickup_date"))
        return_date = _parse_datetime_local(post.get("planned_return_date"))

        product = request.env["product.template"].sudo().browse(product_id)
        if (
            not product.exists()
            or not product.rent_ok
            or quantity < 1
            or duration < 1
            or not pickup_date
            or not return_date
            or return_date <= pickup_date
        ):
            return request.redirect(f"/rental/shop/{product_id}?error=invalid_request")

        partner = request.env.user.partner_id
        order = (
            request.env["rental.order"]
            .sudo()
            .create(
                {
                    "partner_id": partner.id,
                    "rental_start_date": pickup_date,
                    "rental_end_date": return_date,
                    "order_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.product_variant_id.id,
                                "quantity": quantity,
                                "duration": duration,
                                "duration_unit": duration_unit,
                                "planned_pickup_date": pickup_date,
                                "planned_return_date": return_date,
                            },
                        )
                    ],
                }
            )
        )
        return request.redirect(f"/my/rentals/{order.id}")


class RentalCustomerPortal(CustomerPortal):
    def _get_rental_domain(self):
        return [("partner_id", "=", request.env.user.partner_id.id)]

    @http.route(["/my/rentals", "/my/rentals/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_rentals(self, page=1, **kwargs):
        RentalOrder = request.env["rental.order"]
        domain = self._get_rental_domain()
        order_count = RentalOrder.search_count(domain)
        pager = portal_pager(
            url="/my/rentals",
            total=order_count,
            page=page,
            step=self._items_per_page,
        )
        orders = RentalOrder.search(
            domain, order="date_order desc", limit=self._items_per_page, offset=pager["offset"]
        )
        return request.render(
            "rental_management.portal_my_rentals",
            {
                "orders": orders,
                "pager": pager,
                "page_name": "rental",
            },
        )

    @http.route(["/my/rentals/<int:order_id>"], type="http", auth="user", website=True)
    def portal_rental_detail(self, order_id, **kwargs):
        order = request.env["rental.order"].browse(order_id)
        try:
            order.check_access_rights("read")
            order.check_access_rule("read")
        except (AccessError, MissingError):
            return request.redirect("/my/rentals")
        return request.render(
            "rental_management.portal_rental_detail",
            {"order": order},
        )
