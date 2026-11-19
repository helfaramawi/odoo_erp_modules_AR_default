(function () {
    "use strict";

    function insertBanner(data) {
        if (!data || data.environment !== "demo") {
            return;
        }
        if (document.getElementById("o_demo_branding_banner")) {
            return; // already inserted (asset bundle loaded more than once)
        }
        var banner = document.createElement("div");
        banner.id = "o_demo_branding_banner";
        banner.className = "o_demo_branding_banner";
        banner.textContent =
            "DEMO ENVIRONMENT — " +
            (data.application_name || "") +
            " — Sample data only, not for production use";
        document.body.prepend(banner);

        // The banner is position:fixed so it doesn't disturb Odoo's own
        // layout calculations, so push the page down by its real height
        // (measured, not hard-coded, since it wraps to two lines on
        // narrow screens) instead of letting it sit on top of Odoo's menu
        // bar. Re-measure on resize since wrapping can change the height.
        function reserveBannerSpace() {
            document.body.style.paddingTop = banner.offsetHeight + "px";
        }
        reserveBannerSpace();
        window.addEventListener("resize", reserveBannerSpace);
    }

    function loadBranding() {
        fetch("/demo_branding/info", { credentials: "same-origin" })
            .then(function (response) {
                return response.json();
            })
            .then(insertBanner)
            .catch(function () {
                // Fail silently: a missing banner must never block the app.
            });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", loadBranding);
    } else {
        loadBranding();
    }
})();
