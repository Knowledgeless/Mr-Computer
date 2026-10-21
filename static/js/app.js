(() => {
    "use strict";

    const csrfCookie = document.cookie
        .split("; ")
        .find((entry) => entry.startsWith("csrftoken="));

    document.querySelectorAll("[data-coupon-form]").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const button = form.querySelector("button[type=submit]");
            const result = form.querySelector("[data-coupon-result]");
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = "Checking…";
            result.textContent = "";
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        ...(csrfCookie ? { "X-CSRFToken": csrfCookie.split("=")[1] } : {}),
                    },
                    credentials: "same-origin",
                });
                const payload = await response.json();
                result.textContent = response.ok ? payload.message : payload.error || "The coupon could not be applied.";
                result.className = response.ok ? "small mt-2 text-success" : "small mt-2 text-danger";
            } catch {
                result.textContent = "We couldn't check that coupon. Please try again.";
                result.className = "small mt-2 text-danger";
            } finally {
                button.disabled = false;
                button.textContent = originalText;
            }
        });
    });

    const categorySelect = document.querySelector("#component-category");
    const variantSelect = document.querySelector("#component-variant");
    if (categorySelect && variantSelect) {
        const filterVariants = () => {
            const categoryId = categorySelect.value;
            variantSelect.value = "";
            Array.from(variantSelect.options).forEach((option) => {
                if (option.value) {
                    option.hidden = Boolean(categoryId) && option.dataset.category !== categoryId;
                    option.disabled = option.hidden;
                }
            });
        };
        categorySelect.addEventListener("change", filterVariants);
        filterVariants();
    }

    const dashboardMenu = document.querySelector("[data-dashboard-menu]");
    const dashboardSidebar = document.querySelector("#dashboard-sidebar");
    if (dashboardMenu && dashboardSidebar) {
        dashboardMenu.addEventListener("click", () => {
            const isOpen = dashboardSidebar.classList.toggle("is-open");
            dashboardMenu.setAttribute("aria-expanded", String(isOpen));
        });
    }

    document.querySelectorAll("img").forEach((image) => {
        image.addEventListener("error", () => {
            image.alt = image.alt || "Image unavailable";
            image.classList.add("image-load-failed");
        }, { once: true });
    });
})();
