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

        const updateQuantity = async () => {
            if (form.dataset.submitting === "true" || !form.reportValidity()) return;

            const body = new FormData(form);
            form.dataset.submitting = "true";
            form.setAttribute("aria-busy", "true");
            input.disabled = true;
            stepButtons.forEach((button) => { button.disabled = true; });
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        Accept: "application/json",
                    },
                    credentials: "same-origin",
                });
                const payload = await response.json();
                if (!response.ok) {
                    throw new Error(payload.error || "We couldn't update that quantity.");
                }

                input.value = String(payload.quantity);
                input.dataset.savedQuantity = String(payload.quantity);
                form.closest(".cart-line")?.querySelector("[data-cart-line-total]")?.replaceChildren(
                    document.createTextNode(`৳ ${new Intl.NumberFormat("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                    }).format(Number(payload.line_total))}`),
                );
                document.querySelectorAll("[data-cart-subtotal]").forEach((subtotal) => {
                    subtotal.textContent = `৳ ${new Intl.NumberFormat("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                    }).format(Number(payload.subtotal))}`;
                });
            } catch (error) {
                input.value = input.dataset.savedQuantity || input.defaultValue;
                showToast(
                    error instanceof Error ? error.message : "We couldn't update that quantity.",
                    "error",
                );
            } finally {
                form.dataset.submitting = "false";
                form.removeAttribute("aria-busy");
                input.disabled = false;
                updateStepButtons();
            }
        };

        const updateStepButtons = () => {
            const quantity = Number(input.value);
            stepButtons.forEach((button) => {
                const step = Number(button.dataset.quantityStep);
                button.disabled = form.dataset.submitting === "true" || (step < 0
                    ? quantity <= Number(input.min)
                    : quantity >= Number(input.max));
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
                form.requestSubmit();
            });
        });

        form.addEventListener("submit", (event) => {
            event.preventDefault();
            updateQuantity();
        });
        input.addEventListener("change", updateQuantity);
        input.dataset.savedQuantity = input.value;
        updateStepButtons();
    });

    const adSlots = Array.from(document.querySelectorAll("[data-ad-slot]"));
    if (adSlots.length) {
        const adStorageKey = "mc-homepage-ad-slots";
        const readSavedAds = () => {
            try {
                const ads = JSON.parse(localStorage.getItem(adStorageKey) || "{}");
                if (ads && typeof ads === "object" && !Array.isArray(ads)) return ads;
                throw new Error("Saved ad data is invalid.");
            } catch {
                showToast("Saved ads could not be loaded from this browser.", "error");
                return {};
            }
        };
        const savedAds = readSavedAds();
        const saveAds = () => {
            try {
                localStorage.setItem(adStorageKey, JSON.stringify(savedAds));
                return true;
            } catch {
                showToast("This browser could not save the ad image. Try a smaller image.", "error");
                return false;
            }
        };
        const safeAdUrl = (value) => {
            if (!value) return "";
            try {
                const url = new URL(value, window.location.origin);
                return ["http:", "https:"].includes(url.protocol) ? url.href : "";
            } catch {
                return "";
            }
        };
        const renderAd = (slot, ad) => {
            const placeholder = slot.querySelector("[data-ad-placeholder]");
            const image = slot.querySelector("[data-ad-image]");
            const link = slot.querySelector("[data-ad-link]");
            if (!(image instanceof HTMLImageElement) || !placeholder || !link) return;
            if (!ad || typeof ad.image !== "string" || !/^data:image\/(?:webp|png|jpeg);base64,/i.test(ad.image)) {
                image.hidden = true;
                link.hidden = true;
                placeholder.hidden = false;
                return;
            }
            image.src = ad.image;
            image.hidden = false;
            placeholder.hidden = true;
            const href = safeAdUrl(ad.url);
            link.hidden = !href;
            if (href) link.href = href;
            else link.removeAttribute("href");
            const deleteButton = slot.querySelector("[data-ad-delete]");
            if (deleteButton) deleteButton.hidden = false;
        };
        const createAdImage = async (file, slotType) => {
            if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
                throw new Error("Choose a JPEG, PNG, or WebP image.");
            }
            const bitmap = await createImageBitmap(file);
            const maxWidth = slotType === "horizontal" ? 1200 : 600;
            const maxHeight = slotType === "horizontal" ? 600 : 1200;
            const scale = Math.min(1, maxWidth / bitmap.width, maxHeight / bitmap.height);
            const canvas = document.createElement("canvas");
            canvas.width = Math.max(1, Math.round(bitmap.width * scale));
            canvas.height = Math.max(1, Math.round(bitmap.height * scale));
            const context = canvas.getContext("2d");
            if (!context) {
                bitmap.close();
                throw new Error("The ad image could not be processed in this browser.");
            }
            context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
            bitmap.close();
            return canvas.toDataURL("image/webp", 0.82);
        };

        adSlots.forEach((slot) => {
            const slotType = slot.dataset.adSlot;
            const editor = slot.querySelector("[data-ad-editor]");
            const deleteButton = slot.querySelector("[data-ad-delete]");
            renderAd(slot, savedAds[slotType]);
            if (!editor) return;

            editor.addEventListener("submit", async (event) => {
                event.preventDefault();
                const fileInput = editor.querySelector('input[type="file"]');
                const urlInput = editor.querySelector('input[type="url"]');
                const submitButton = editor.querySelector('button[type="submit"]');
                const file = fileInput instanceof HTMLInputElement ? fileInput.files?.[0] : null;
                if (!file) {
                    showToast("Choose an image before saving this ad.", "error");
                    return;
                }
                const url = urlInput instanceof HTMLInputElement ? urlInput.value.trim() : "";
                if (url && !safeAdUrl(url)) {
                    showToast("Use an HTTP(S) URL for the ad destination.", "error");
                    return;
                }
                if (submitButton instanceof HTMLButtonElement) submitButton.disabled = true;
                try {
                    savedAds[slotType] = { image: await createAdImage(file, slotType), url };
                    if (saveAds()) {
                        renderAd(slot, savedAds[slotType]);
                        editor.reset();
                        showToast("Ad saved in this browser.", "success");
                    }
                } catch (error) {
                    showToast(error instanceof Error ? error.message : "The ad image could not be saved.", "error");
                } finally {
                    if (submitButton instanceof HTMLButtonElement) submitButton.disabled = false;
                }
            });

            deleteButton?.addEventListener("click", () => {
                delete savedAds[slotType];
                if (saveAds()) {
                    renderAd(slot, null);
                    deleteButton.hidden = true;
                    editor.reset();
                    showToast("Ad removed from this browser.", "success");
                }
            });
        });
    }

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
