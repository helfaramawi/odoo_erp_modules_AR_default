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
