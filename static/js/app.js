(() => {
    "use strict";

    const csrfCookie = document.cookie
        .split("; ")
        .find((entry) => entry.startsWith("csrftoken="));

    const toastTypes = {
        success: { icon: "bi-check-circle-fill" },
        info: { icon: "bi-info-circle-fill" },
        warning: { icon: "bi-exclamation-triangle-fill" },
        error: { icon: "bi-x-circle-fill" },
    };

    const dismissToast = (toast) => {
        if (toast.dataset.dismissed === "true") return;
        toast.dataset.dismissed = "true";
        toast.classList.add("is-leaving");
        window.setTimeout(() => toast.remove(), 200);
    };

    const startToast = (toast) => {
        const closeButton = toast.querySelector("[data-toast-close]");
        const duration = Number(toast.dataset.toastDuration) || 4000;
        if (closeButton) {
            closeButton.addEventListener("click", () => dismissToast(toast), { once: true });
        }
        window.setTimeout(() => dismissToast(toast), duration);
    };

    const getToastRegion = () => {
        let region = document.querySelector("[data-toast-region]");
        if (!region) {
            region = document.createElement("div");
            region.className = "toast-region";
            region.dataset.toastRegion = "";
            region.setAttribute("aria-live", "polite");
            region.setAttribute("aria-relevant", "additions");
            document.body.append(region);
        }
        return region;
    };

    const showToast = (message, type = "info") => {
        const normalizedType = Object.hasOwn(toastTypes, type) ? type : "info";
        const toast = document.createElement("div");
        const icon = document.createElement("span");
        const iconElement = document.createElement("i");
        const messageElement = document.createElement("span");
        const closeButton = document.createElement("button");
        const closeIcon = document.createElement("i");
        const progress = document.createElement("span");

        toast.className = "app-toast";
        toast.dataset.toast = "";
        toast.dataset.toastType = normalizedType;
        toast.setAttribute("role", normalizedType === "error" ? "alert" : "status");
        icon.className = "app-toast__icon";
        icon.setAttribute("aria-hidden", "true");
        iconElement.className = `bi ${toastTypes[normalizedType].icon}`;
        icon.append(iconElement);
        messageElement.className = "app-toast__message";
        messageElement.textContent = String(message);
        closeButton.className = "app-toast__close";
        closeButton.type = "button";
        closeButton.dataset.toastClose = "";
        closeButton.setAttribute("aria-label", "Dismiss notification");
        closeIcon.className = "bi bi-x-lg";
        closeIcon.setAttribute("aria-hidden", "true");
        closeButton.append(closeIcon);
        progress.className = "app-toast__progress";
        progress.setAttribute("aria-hidden", "true");
        toast.append(icon, messageElement, closeButton, progress);
        getToastRegion().append(toast);
        startToast(toast);
    };

    document.querySelectorAll("[data-toast]").forEach(startToast);
    window.MrComputers = { ...window.MrComputers, showToast };

    document.querySelectorAll("[data-cart-add]").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const button = form.querySelector('button[type="submit"]');
            const originalContent = button?.innerHTML;
            if (button) {
                button.disabled = true;
                button.setAttribute("aria-busy", "true");
            }
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        Accept: "application/json",
                        ...(csrfCookie ? { "X-CSRFToken": csrfCookie.split("=")[1] } : {}),
                    },
                    credentials: "same-origin",
                });
                const payload = await response.json();
                if (!response.ok) {
                    throw new Error(payload.error || "We couldn't add that product to your cart.");
                }
                document.querySelectorAll("[data-cart-count]").forEach((badge) => {
                    badge.textContent = String(payload.cart_count);
                });
                document.querySelectorAll(".header-cart").forEach((link) => {
                    link.setAttribute("aria-label", `Cart, ${payload.cart_count} product types`);
                });
                showToast(payload.message, "success");
            } catch (error) {
                showToast(error instanceof Error ? error.message : "We couldn't add that product to your cart.", "error");
            } finally {
                if (button) {
                    button.disabled = false;
                    button.removeAttribute("aria-busy");
                    if (originalContent !== undefined) button.innerHTML = originalContent;
                }
            }
        });
    });

    document.querySelectorAll("[data-cart-quantity]").forEach((form) => {
        const input = form.querySelector("[data-quantity-input]");
        const stepButtons = Array.from(form.querySelectorAll("[data-quantity-step]"));
        if (!(input instanceof HTMLInputElement)) return;

        const updateStepButtons = () => {
            const quantity = Number(input.value);
            stepButtons.forEach((button) => {
                const step = Number(button.dataset.quantityStep);
                button.disabled = step < 0
                    ? quantity <= Number(input.min)
                    : quantity >= Number(input.max);
            });
        };

        stepButtons.forEach((button) => {
            button.addEventListener("click", () => {
                const step = Number(button.dataset.quantityStep);
                const current = Number(input.value) || Number(input.min);
                input.value = String(Math.max(
                    Number(input.min),
                    Math.min(Number(input.max), current + step),
                ));
                updateStepButtons();
                if (form.reportValidity()) form.requestSubmit();
            });
        });

        input.addEventListener("change", () => {
            updateStepButtons();
            if (form.reportValidity()) form.requestSubmit();
        });
        updateStepButtons();
    });

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        const updateThemeButton = () => {
            const isDark = document.documentElement.dataset.theme !== "light";
            button.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} mode`);
            button.title = `Switch to ${isDark ? "light" : "dark"} mode`;
            button.innerHTML = `<i class="bi ${isDark ? "bi-sun-fill" : "bi-moon-stars-fill"}" aria-hidden="true"></i>`;
        };
        updateThemeButton();
        button.addEventListener("click", () => {
            const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            document.documentElement.dataset.theme = nextTheme;
            try {
                localStorage.setItem("mc-theme", nextTheme);
            } catch {
                showToast("Your theme preference could not be saved.", "warning");
            }
            updateThemeButton();
        });
    });

    document.querySelectorAll("[data-home-slider]").forEach((slider) => {
        const slides = Array.from(slider.querySelectorAll("[data-hero-slide]"));
        const dots = Array.from(slider.querySelectorAll("[data-hero-dot]"));
        if (slides.length < 2) return;
        let currentIndex = 0;
        let timer;
        const showSlide = (index) => {
            currentIndex = (index + slides.length) % slides.length;
            slides.forEach((slide, slideIndex) => {
                const isActive = slideIndex === currentIndex;
                slide.classList.toggle("is-active", isActive);
                slide.setAttribute("aria-hidden", String(!isActive));
            });
            dots.forEach((dot, dotIndex) => {
                if (dotIndex === currentIndex) dot.setAttribute("aria-current", "true");
                else dot.removeAttribute("aria-current");
            });
        };
        const stopTimer = () => window.clearInterval(timer);
        const startTimer = () => {
            stopTimer();
            if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
                timer = window.setInterval(() => showSlide(currentIndex + 1), 6000);
            }
        };
        slider.querySelector("[data-hero-previous]")?.addEventListener("click", () => {
            showSlide(currentIndex - 1);
            startTimer();
        });
        slider.querySelector("[data-hero-next]")?.addEventListener("click", () => {
            showSlide(currentIndex + 1);
            startTimer();
        });
        dots.forEach((dot) => dot.addEventListener("click", () => {
            showSlide(Number(dot.dataset.heroDot));
            startTimer();
        }));
        slider.addEventListener("mouseenter", stopTimer);
        slider.addEventListener("mouseleave", startTimer);
        slider.addEventListener("focusin", stopTimer);
        slider.addEventListener("focusout", (event) => {
            if (!slider.contains(event.relatedTarget)) startTimer();
        });
        startTimer();
    });

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
                const message = response.ok ? payload.message : payload.error || "The coupon could not be applied.";
                result.textContent = message;
                result.className = response.ok ? "small mt-2 text-success" : "small mt-2 text-danger";
                showToast(message, response.ok ? "success" : "error");
            } catch {
                const message = "We couldn't check that coupon. Please try again.";
                result.textContent = message;
                result.className = "small mt-2 text-danger";
                showToast(message, "error");
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
