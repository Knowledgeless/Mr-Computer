import json
import re
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils.text import slugify

from catalog.models import (
    Attribute,
    Brand,
    Category,
    Product,
    ProductVariant,
    ProductVariantAttribute,
)
from inventory.models import Inventory


BRANDS = {
    "AMD": {
        "website": "https://www.amd.com/",
        "description": "Processor and graphics hardware manufacturer.",
    },
    "ASUS": {
        "website": "https://www.asus.com/",
        "description": "Computer manufacturer with laptops, motherboards, graphics cards, and peripherals.",
    },
    "Corsair": {
        "website": "https://www.corsair.com/",
        "description": "PC memory, cases, power supplies, cooling, and gaming peripherals manufacturer.",
    },
    "Gigabyte": {
        "website": "https://www.gigabyte.com/",
        "description": "Computer hardware manufacturer with motherboards, graphics cards, monitors, and laptops.",
    },
    "Intel": {
        "website": "https://www.intel.com/",
        "description": "Processor and computing hardware manufacturer.",
    },
    "Kingston": {
        "website": "https://www.kingston.com/",
        "description": "Memory and data storage manufacturer.",
    },
    "Logitech": {
        "website": "https://www.logitech.com/",
        "description": "Computer peripherals manufacturer, including keyboards and mice.",
    },
    "MSI": {
        "website": "https://www.msi.com/",
        "description": "Computer manufacturer with laptops, motherboards, graphics cards, and peripherals.",
    },
    "Samsung": {
        "website": "https://www.samsung.com/",
        "description": "Consumer electronics manufacturer with displays, phones, tablets, and audio products.",
    },
    "TP-Link": {
        "website": "https://www.tp-link.com/",
        "description": "Networking equipment manufacturer.",
    },
}

CATEGORY_GROUPS = {
    "Computers": ("Laptop",),
    "PC Components": (
        "Processor",
        "Motherboard",
        "Graphics Card",
        "Memory",
        "Power Supply",
        "PC Case",
        "CPU Cooler",
    ),
    "Storage": ("SSD", "Memory Card", "USB Flash Drive"),
    "Displays": ("Monitor",),
    "Networking": ("Router", "Wi-Fi Adapter"),
    "Peripherals": ("Keyboard", "Mouse"),
    "Audio": ("Headphone", "Speaker", "Earbuds"),
    "Mobile Devices": ("Mobile Phone", "Tablet"),
}

CATEGORY_DESCRIPTIONS = {
    "Laptop": "Portable computers and notebooks.",
    "Processor": "Desktop processors.",
    "Motherboard": "Desktop computer motherboards.",
    "Graphics Card": "Discrete graphics cards.",
    "Memory": "Desktop memory modules.",
    "Power Supply": "Power supplies for desktop computers.",
    "PC Case": "Computer cases and chassis.",
    "CPU Cooler": "Processor cooling hardware.",
    "SSD": "Solid-state storage drives.",
    "Memory Card": "Removable flash memory cards.",
    "USB Flash Drive": "Portable USB flash storage.",
    "Monitor": "Computer displays and monitors.",
    "Router": "Wireless networking routers.",
    "Wi-Fi Adapter": "Wireless network adapters.",
    "Keyboard": "Computer keyboards.",
    "Mouse": "Computer mice.",
    "Headphone": "Headphones and headsets.",
    "Speaker": "Speakers and audio devices.",
    "Earbuds": "Wireless and wired earbuds.",
    "Mobile Phone": "Mobile phones.",
    "Tablet": "Tablet computers.",
}

PRODUCT_TYPES = {
    "Laptop": Product.ProductType.LAPTOP,
    "Processor": Product.ProductType.COMPONENT,
    "Motherboard": Product.ProductType.COMPONENT,
    "Graphics Card": Product.ProductType.COMPONENT,
    "Memory": Product.ProductType.COMPONENT,
    "Power Supply": Product.ProductType.COMPONENT,
    "PC Case": Product.ProductType.COMPONENT,
    "CPU Cooler": Product.ProductType.COMPONENT,
    "SSD": Product.ProductType.COMPONENT,
    "Memory Card": Product.ProductType.COMPONENT,
    "USB Flash Drive": Product.ProductType.COMPONENT,
    "Monitor": Product.ProductType.OTHER,
    "Router": Product.ProductType.ROUTER,
    "Wi-Fi Adapter": Product.ProductType.ROUTER,
    "Keyboard": Product.ProductType.ACCESSORY,
    "Mouse": Product.ProductType.ACCESSORY,
    "Headphone": Product.ProductType.ACCESSORY,
    "Speaker": Product.ProductType.ACCESSORY,
    "Earbuds": Product.ProductType.ACCESSORY,
    "Mobile Phone": Product.ProductType.PHONE,
    "Tablet": Product.ProductType.PHONE,
}


class Command(BaseCommand):
    help = (
        "Seed 409 researched products into a local development database. "
        "Retail prices are captured listings; inventory quantities are simulated."
    )

    def handle(self, *args, **options):
        self._require_local_debug_database()
        fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "test_catalog_409.json"
        try:
            with fixture_path.open(encoding="utf-8") as fixture_file:
                fixture = json.load(fixture_file)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not load test catalog fixture: {exc}") from exc

        products = fixture.get("products", [])
        self._validate_fixture(fixture, products)

        with transaction.atomic():
            brands = self._get_brands()
            categories = self._get_categories()
            specification_attribute, _ = Attribute.objects.get_or_create(
                slug="test-listing-specifications",
                defaults={
                    "name": "Test listing specifications",
                    "data_type": Attribute.DataType.TEXT,
                    "is_filterable": False,
                    "is_comparable": True,
                },
            )
            for index, item in enumerate(products, start=1):
                self._save_product(
                    index,
                    item,
                    brands[item["brand"]],
                    categories[item["category"]],
                    specification_attribute,
                    fixture["captured_on"],
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(products)} products and variants for "
                f"{len(brands)} brands across {len(categories)} categories."
            )
        )

    def _require_local_debug_database(self):
        database_host = connection.settings_dict.get("HOST") or ""
        local_hosts = {"", "localhost", "127.0.0.1", "::1"}
        if not settings.DEBUG or database_host not in local_hosts:
            raise CommandError(
                "This seed command only runs with DEBUG enabled and a local database. "
                "It will not write to a production or remote database."
            )

    def _validate_fixture(self, fixture, products):
        if not isinstance(fixture, dict):
            raise CommandError("The test catalog fixture must be a JSON object.")
        if fixture.get("source") != "Star Tech Bangladesh":
            raise CommandError("Unexpected test catalog source.")
        if not isinstance(products, list):
            raise CommandError("The test catalog products must be a list.")
        if len(products) != 409:
            raise CommandError(f"Expected exactly 409 products, found {len(products)}.")
        if any(not isinstance(item, dict) for item in products):
            raise CommandError("Each product fixture record must be a JSON object.")
        if {item.get("brand") for item in products} != set(BRANDS):
            raise CommandError("The fixture must contain the configured ten brands.")
        if len({item.get("name") for item in products}) != 409:
            raise CommandError("The fixture must contain 409 distinct product names.")
        if len({item.get("url") for item in products}) != 409:
            raise CommandError("The fixture must contain 409 distinct source listings.")
        if len({item.get("category") for item in products}) != 21:
            raise CommandError("The fixture must cover exactly 21 product categories.")
        for index, item in enumerate(products, start=1):
            if (
                item.get("category") not in CATEGORY_DESCRIPTIONS
                or not isinstance(item.get("name"), str)
                or not item["name"].strip()
                or not isinstance(item.get("url"), str)
                or not item["url"].startswith("https://www.startech.com.bd/")
                or not isinstance(item.get("specs"), str)
                or not item["specs"].strip()
                or not isinstance(item.get("price"), int)
                or isinstance(item.get("price"), bool)
                or item["price"] <= 0
                or not isinstance(item.get("compare_at", 0), int)
                or item.get("compare_at", 0) < 0
            ):
                raise CommandError(f"Invalid product fixture record at index {index}.")
            if item.get("brand") not in BRANDS:
                raise CommandError(f"Unknown brand in fixture record at index {index}.")

    def _get_brands(self):
        brands = {}
        for name, details in BRANDS.items():
            brand, _ = Brand.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name, **details},
            )
            brands[name] = brand
        return brands

    def _get_categories(self):
        categories = {}
        for group_name, category_names in CATEGORY_GROUPS.items():
            parent, _ = Category.objects.get_or_create(
                slug=f"test-catalog-{slugify(group_name)}",
                defaults={
                    "name": group_name,
                    "description": f"Test catalog category for {group_name.lower()}.",
                    "display_order": len(categories),
                },
            )
            for category_name in category_names:
                category, _ = Category.objects.get_or_create(
                    slug=f"test-catalog-{slugify(category_name)}",
                    defaults={
                        "name": category_name,
                        "parent": parent,
                        "description": CATEGORY_DESCRIPTIONS[category_name],
                        "display_order": len(categories),
                    },
                )
                categories[category_name] = category
        return categories

    def _save_product(self, index, item, brand, category, specification_attribute, captured_on):
        slug_suffix = slugify(item["name"])[:200].strip("-")
        product_slug = f"test-catalog-{index:03d}-{slug_suffix}"
        sku = f"TEST-CATALOG-{index:03d}"
        selling_price = Decimal(item["price"])
        compare_at_price = Decimal(item.get("compare_at", 0))
        if compare_at_price <= selling_price:
            compare_at_price = Decimal("0.00")

        specs = item["specs"].strip()
        description = (
            f"{item['name']}. Listed specifications: {specs}\n\n"
            f"Test catalog listing sourced from Star Tech Bangladesh on {captured_on}. "
            "Local inventory quantity is simulated for development testing."
        )
        product, _ = Product.objects.update_or_create(
            slug=product_slug,
            defaults={
                "category": category,
                "brand": brand,
                "name": item["name"],
                "short_description": specs[:500],
                "description": description,
                "product_type": PRODUCT_TYPES[item["category"]],
                "condition": (
                    Product.Condition.REFURBISHED
                    if re.search(r"\brebox\b", item["name"], re.IGNORECASE)
                    else Product.Condition.NEW
                ),
                "status": Product.Status.ACTIVE,
                "is_featured": index % 11 == 0,
                "is_new_arrival": index % 7 == 0,
                "is_best_seller": index % 13 == 0,
                "is_active": True,
                "meta_title": item["name"],
                "meta_description": (
                    f"Test listing. Retail price checked at Star Tech Bangladesh on {captured_on}; "
                    "inventory is simulated."
                ),
            },
        )
        variant, _ = ProductVariant.objects.update_or_create(
            sku=sku,
            defaults={
                "product": product,
                "barcode": "",
                "variant_name": "Listed configuration",
                "cost_price": selling_price,
                "selling_price": selling_price,
                "compare_at_price": compare_at_price,
                "is_active": True,
            },
        )
        Inventory.objects.update_or_create(
            variant=variant,
            defaults={
                "quantity": 0 if index % 17 == 0 else 1 + (index * 7) % 24,
                "reserved_quantity": 0,
                "reorder_level": 2,
            },
        )
        ProductVariantAttribute.objects.update_or_create(
            variant=variant,
            attribute=specification_attribute,
            defaults={"value": None, "custom_value": specs[:240]},
        )
