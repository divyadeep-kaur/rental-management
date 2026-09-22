(function () {
    "use strict";

    function onReady(fn) {
        if (document.readyState !== "loading") {
            fn();
        } else {
            document.addEventListener("DOMContentLoaded", fn);
        }
    }

    function setupShopSearch() {
        var input = document.querySelector("[data-rental-search]");
        var cards = document.querySelectorAll("[data-rental-card]");
        if (!input || !cards.length) {
            return;
        }
        input.addEventListener("input", function () {
            var term = input.value.trim().toLowerCase();
            cards.forEach(function (card) {
                var name = (card.getAttribute("data-rental-name") || "").toLowerCase();
                card.style.display = !term || name.indexOf(term) !== -1 ? "" : "none";
            });
        });
    }

    function setupQtyStepper() {
        document.querySelectorAll("[data-rental-stepper]").forEach(function (stepper) {
            var input = stepper.querySelector("input");
            var min = parseInt(input.getAttribute("min") || "1", 10);
            stepper.querySelectorAll("button").forEach(function (btn) {
                btn.addEventListener("click", function (ev) {
                    ev.preventDefault();
                    var delta = parseInt(btn.getAttribute("data-delta"), 10);
                    var value = parseInt(input.value || min, 10) + delta;
                    input.value = Math.max(min, value);
                    input.dispatchEvent(new Event("change", { bubbles: true }));
                });
            });
        });
    }

    function setupPriceEstimate() {
        var form = document.querySelector("[data-rental-booking-form]");
        if (!form) {
            return;
        }
        var dataEl = document.getElementById("rental-pricing-data");
        var pricing = {};
        try {
            pricing = JSON.parse(dataEl.textContent);
        } catch (e) {
            pricing = {};
        }

        var qtyInput = form.querySelector('[name="quantity"]');
        var durationInput = form.querySelector('[name="duration"]');
        var unitSelect = form.querySelector('[name="duration_unit"]');
        var estimateEl = document.querySelector("[data-rental-estimate]");
        if (!estimateEl) {
            return;
        }

        function currentTotal() {
            var qty = parseFloat(qtyInput.value) || 0;
            var duration = parseFloat(durationInput.value) || 0;
            var unit = unitSelect.value;
            var rate = pricing[unit] || 0;
            return qty * duration * rate;
        }

        function refresh() {
            var total = currentTotal();
            estimateEl.textContent = "$" + total.toFixed(2);
            estimateEl.classList.add("o_rental_pulse");
            setTimeout(function () {
                estimateEl.classList.remove("o_rental_pulse");
            }, 150);
        }

        [qtyInput, durationInput, unitSelect].forEach(function (el) {
            if (el) {
                el.addEventListener("input", refresh);
                el.addEventListener("change", refresh);
            }
        });
        refresh();
    }

    function setupStickyNav() {
        var nav = document.querySelector(".o_rental_shop_wrap .navbar, header nav.navbar");
        if (!nav) {
            return;
        }
        var toggle = function () {
            if (window.scrollY > 12) {
                nav.classList.add("o_rental_nav_scrolled");
            } else {
                nav.classList.remove("o_rental_nav_scrolled");
            }
        };
        document.addEventListener("scroll", toggle, { passive: true });
        toggle();
    }

    onReady(function () {
        setupShopSearch();
        setupQtyStepper();
        setupPriceEstimate();
        setupStickyNav();
    });
})();
