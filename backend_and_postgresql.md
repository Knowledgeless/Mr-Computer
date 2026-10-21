# Mr. Computers — Production E-Commerce Architecture & PostgreSQL Database Plan

> **Project:** Mr. Computers  
> **Backend:** Django  
> **Database:** PostgreSQL  
> **Frontend:** Django Templates + HTML + CSS + Bootstrap + JavaScript  
> **Primary goal:** A scalable, fully customized, secure, owner-manageable each and everything from the frontend e-commerce platform for computer components, custom PCs, laptops, refurbished laptops, Oraimo products, button phones, mobile accessories, routers, and related electronics.

---

# 1. Architecture Principles

This project must be designed as a **real e-commerce + inventory + CMS platform**, not as a simple product CRUD website.

Core principles:

1. PostgreSQL is the source of truth for transactional data.
2. Django ORM is used for application/database access.
3. Business logic must not live only in templates or JavaScript.
4. Historical order data must never depend on mutable product data.
5. Guest checkout must be supported.
6. Customer accounts are optional.
7. Cash on Delivery (COD) is supported from the first production version.
8. Coupon rules must be configurable from the dashboard.
9. Product variants must be supported.
10. Refurbished physical units must be individually trackable where necessary.
11. Images/media must be stored outside PostgreSQL in production; PostgreSQL stores metadata and references.
12. Product images must have a controlled cleanup/lifecycle strategy.
13. The system must be protected against brute-force attacks, fake order automation, fake cart automation, coupon abuse, and excessive API requests.
14. The owner must be able to manage products, inventory, orders, coupons, homepage content, pages, banners, and basic settings without touching code.
15. The system must be designed so that future scaling does not require replacing the database architecture.

---

# 2. Recommended Django Application Structure

```text
MrComputers/
│
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── services.py
│
├── catalog/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── services.py
│
├── inventory/
│   ├── models.py
│   ├── views.py
│   ├── services.py
│   └── tasks.py
│
├── cart/
│   ├── models.py
│   ├── views.py
│   ├── services.py
│   └── urls.py
│
├── orders/
│   ├── models.py
│   ├── views.py
│   ├── services.py
│   └── urls.py
│
├── payments/
│   ├── models.py
│   ├── services.py
│   └── views.py
│
├── promotions/
│   ├── models.py
│   ├── services.py
│   └── views.py
│
├── pc_builder/
│   ├── models.py
│   ├── views.py
│   └── services.py
│
├── reviews/
│   ├── models.py
│   ├── views.py
│   └── services.py
│
├── shipping/
│   ├── models.py
│   └── services.py
│
├── cms/
│   ├── models.py
│   ├── views.py
│   └── services.py
│
├── reports/
│   ├── views.py
│   └── services.py
│
├── audit/
│   ├── models.py
│   └── services.py
│
├── dashboard/
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── templates/
├── static/
├── media/                 # development only
├── requirements.txt
├── manage.py
└── README.md
```

---

# 3. Database Strategy

Use:

```text
PostgreSQL
```

** Do not use SQLite in production and development.


Recommended PostgreSQL characteristics:

- UTF-8
- timezone-aware timestamps
- transactions
- row-level locking
- foreign-key constraints
- CHECK constraints
- unique constraints
- partial indexes where appropriate
- composite indexes for high-frequency queries
- JSONB only where flexible/unstructured data is genuinely useful
- every field/table/column has to have a default value while creating 

Do not turn PostgreSQL into a document database. The core business entities remain relational.

---

# 4. Primary Key Strategy

Use PostgreSQL-generated UUID primary keys for major business entities where appropriate.

Recommended pattern:

```python
id = models.UUIDField(
    primary_key=True,
    default=uuid.uuid4,
    editable=False
)
```

Why UUID?

- Avoids predictable sequential public IDs.
- Safer for URLs and public references.
- Better for future distributed systems.
- Makes merging/importing data easier.
- Prevents exposing internal row counts.

However, do not expose raw UUIDs as the customer's order number.

Use a human-readable unique order number such as:

```text
MC-20261019-000123
```

The UUID remains the database primary key.

For high-volume purely internal tables, BigAutoField can also be acceptable. Consistency is more important than blindly using UUID everywhere.

---

# 5. Money / Decimal Rules

Never use floating point for money.

Use:

```python
models.DecimalField(
    max_digits=12,
    decimal_places=2
)
```

for normal monetary values.

Examples:

```text
9999999999.99
```

This provides sufficient room for this business while avoiding unnecessarily large numeric columns.

Recommended fields:

```text
cost_price
selling_price
compare_at_price
discount_amount
shipping_cost
subtotal
tax_amount
total_amount
```

All must use DecimalField.

---

# 6. Timestamp Rules

Every major mutable model should use:

```python
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

Use UTC internally through Django timezone support.

Display local Bangladesh time only at the presentation layer.

Never manually store local clock time as the system's canonical timestamp.

---

# 7. CATALOG DOMAIN

## 7.1 Category

### Table

```text
Category
```

Fields:

```text
id
parent_id
name
slug
description
image
is_active
display_order
created_at
updated_at
```

Relationships:

```text
Category 1 ──── N Category
Category 1 ──── N Product
Category 1 ──── N CouponCategory
Category 1 ──── N ProductVariant through product
```

Use a self-referencing nullable ForeignKey:

```python
parent = models.ForeignKey(
    "self",
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name="children"
)
```

Do not cascade-delete a category that contains products.

---

# 8. Brand

Fields:

```text
id
name
slug
logo
description
website
is_active
created_at
updated_at
```

Constraints:

```text
slug UNIQUE
```

Relationship:

```text
Brand 1 ──── N Product
Brand 1 ──── N CouponBrand
```

Use:

```python
on_delete=models.PROTECT
```

for Product -> Brand.

---

# 9. Product

Product represents the logical product.

Example:

```text
Kingston NV3 NVMe SSD
```

It is not necessarily one physical unit.

Fields:

```text
id
category_id
brand_id
name
slug
short_description
description
product_type
condition
status
is_featured
is_new_arrival
is_best_seller
is_active
meta_title
meta_description
created_at
updated_at
```

### Product Type Choices

```python
COMPONENT
LAPTOP
PHONE
ACCESSORY
ROUTER
CUSTOM_PC
OTHER
```

### Condition Choices

```python
NEW
REFURBISHED
USED
OPEN_BOX
```

### Status Choices

```python
DRAFT
ACTIVE
OUT_OF_STOCK
DISCONTINUED
ARCHIVED
```

Constraints:

```text
slug UNIQUE
```

Relationships:

```text
Category 1 ──── N Product
Brand 1 ──── N Product
Product 1 ──── N ProductVariant
Product 1 ──── N ProductImage
Product 1 ──── N Review
Product 1 ──── N CouponProduct
```

Use `PROTECT` for category and brand.

Do not physically delete products that have historical sales.

---

# 10. ProductVariant

Variants represent the actual sellable configuration.

Example:

```text
Kingston NV3
├── 500GB
├── 1TB
└── 2TB
```

Fields:

```text
id
product_id
sku
barcode
variant_name
cost_price
selling_price
compare_at_price
weight
is_active
created_at
updated_at
```

Constraints:

```text
sku UNIQUE
```

Use DecimalField for all prices.

Relationships:

```text
Product 1 ──── N ProductVariant
ProductVariant 1 ──── 1 Inventory
ProductVariant 1 ──── N InventoryItem
ProductVariant 1 ──── N ProductVariantAttribute
ProductVariant 1 ──── N CartItem
ProductVariant 1 ──── N OrderItem
ProductVariant 1 ──── N WishlistItem
ProductVariant 1 ──── N BuildItem
```

Use:

```python
product = models.ForeignKey(
    Product,
    on_delete=models.PROTECT,
    related_name="variants"
)
```

Do not delete a variant if it appears in historical orders.

Use `is_active=False` instead.

---

# 11. Product Attributes

The product specification system must be dynamic.

## Attribute

Fields:

```text
id
name
slug
data_type
unit
is_filterable
is_comparable
created_at
updated_at
```

Examples:

```text
RAM
Storage
Processor
GPU
Screen Size
Refresh Rate
Resolution
Battery Capacity
WiFi Standard
Router Speed
```

### Data type choices

```text
TEXT
NUMBER
BOOLEAN
SELECT
```

## AttributeValue

```text
id
attribute_id
value
```

## ProductVariantAttribute

```text
id
variant_id
attribute_id
value_id
custom_value
```

Constraints:

```text
UNIQUE(variant_id, attribute_id)
```

This prevents the same variant from having duplicate RAM attributes, for example.

Relationships:

```text
Attribute 1 ──── N AttributeValue
Attribute 1 ──── N ProductVariantAttribute
ProductVariant 1 ──── N ProductVariantAttribute
```

---

# 12. ProductImage

Do not store binary images inside PostgreSQL.

PostgreSQL should store metadata and the storage key/path.

Fields:

```text
id
product_id
variant_id nullable
storage_key
alt_text
is_primary
display_order
status
created_at
updated_at
marked_for_deletion_at
deleted_at
```

Recommended storage:

```text
Development:
Local media

Production:
Object storage / CDN
```

Examples:

```text
AWS S3
Cloudflare R2
Backblaze B2
Cloudinary
other S3-compatible object storage
```

The exact provider can be selected later.

### Important

Do NOT blindly delete product images just because stock becomes zero.

A product can be:

```text
OUT OF STOCK today
RESTOCKED next week
```

Deleting all images after two days would create unnecessary re-upload work and could damage SEO.

Instead, implement a **safe image lifecycle**.

---

# 13. Safe Product Image Cleanup Strategy

The business requirement is:

> If a product reaches 0 stock and remains at 0 for two days, images may become eligible for deletion.

Implement this as:

```text
Stock reaches 0
      ↓
record out_of_stock_since
      ↓
wait 2 full days
      ↓
background cleanup job checks eligibility
      ↓
mark images as cleanup candidates
      ↓
grace period
      ↓
verify again
      ↓
delete object-storage file
      ↓
soft-delete/retain metadata temporarily
```

Do NOT delete synchronously from the request that changes inventory.

Use a scheduled background task.

---

# 14. Recommended Cleanup Safety Rules

An image should only be deleted automatically when ALL required conditions are satisfied.

Recommended conditions:

1. Product/variant has been out of stock for at least 2 days.
2. Product/variant has not been restocked during the grace period.
3. Image is not needed by an active variant.
4. Image is not the only image for a currently active product.
5. Product is not part of a currently active campaign requiring the image.
6. Product is not currently featured on the homepage.
7. Image is not used by CMS content.
8. Image is not referenced by another object.
9. The product is not marked as `KEEP_MEDIA`.
10. The owner has not manually protected the image.
11. A final recheck confirms stock is still zero before deletion.

Recommended additional field:

```text
retain_media = BooleanField(default=False)
```

This gives the owner a manual override.

---

# 15. Out-of-stock tracking

Inventory should store:

```text
out_of_stock_since
```

When available quantity becomes zero:

```text
out_of_stock_since = timezone.now()
```

When stock becomes positive again:

```text
out_of_stock_since = NULL
```

Do not infer this solely from transaction history during every cleanup operation.

---

# 16. Image Cleanup Job

The cleanup must be idempotent.

Conceptual process:

```python
for candidate in cleanup_candidates:
    recheck_stock(candidate)

    if stock > 0:
        cancel_cleanup()

    if product.retain_media:
        cancel_cleanup()

    if image_is_referenced_elsewhere:
        cancel_cleanup()

    mark_for_deletion()

    after_grace_period:
        recheck_everything()

        delete_from_object_storage()

        mark_deleted()
```

Use a scheduled task system such as Celery + Celery Beat or another reliable scheduler.

Do not rely on a Django web request to perform scheduled cleanup.

---

# 17. Inventory

## Inventory

Fields:

```text
id
variant_id
quantity
reserved_quantity
reorder_level
out_of_stock_since
updated_at
```

Relationship:

```text
ProductVariant 1 ──── 1 Inventory
```

Constraint:

```text
UNIQUE(variant_id)
```

Stock rule:

```text
available_quantity = quantity - reserved_quantity
```

Never allow:

```text
quantity < 0
reserved_quantity < 0
reserved_quantity > quantity
```

These should be protected at the service/business-logic level and where practical by database constraints.

---

# 18. InventoryItem

This is for individually trackable physical units, especially refurbished laptops.

Fields:

```text
id
variant_id
serial_number
asset_tag
condition_grade
battery_health
purchase_price
selling_price
status
notes
received_at
sold_at
created_at
updated_at
```

Condition grade:

```text
A+
A
B+
B
C
```

Status:

```text
IN_STOCK
RESERVED
SOLD
DAMAGED
RETURNED
```

For serial-numbered devices:

```text
serial_number UNIQUE
```

when non-null.

Relationship:

```text
ProductVariant 1 ──── N InventoryItem
```

---

# 19. InventoryTransaction

Every stock-changing event must be traceable.

Fields:

```text
id
variant_id
inventory_item_id nullable
transaction_type
quantity
reference_type
reference_id
note
created_by
created_at
```

Types:

```text
PURCHASE
SALE
RETURN
ADJUSTMENT
DAMAGE
TRANSFER
RESERVATION
RELEASE
```

Relationship:

```text
ProductVariant 1 ──── N InventoryTransaction
InventoryItem 1 ──── N InventoryTransaction
User 1 ──── N InventoryTransaction
```

Never silently change inventory quantity without generating an inventory transaction.

---

# 20. Cart

Guest users must be supported.

Fields:

```text
id
user_id nullable
session_key nullable
created_at
updated_at
expires_at
```

Rules:

```text
Guest:
user_id = NULL
session_key = unique session identifier

Logged-in:
user_id = user
```

Do not allow an ambiguous cart where both ownership mechanisms are incorrectly populated.

---

# 21. CartItem

Fields:

```text
id
cart_id
variant_id
quantity
unit_price
created_at
updated_at
```

Constraint:

```text
UNIQUE(cart_id, variant_id)
```

Do not trust the browser's unit price.

The server must always recalculate the current valid price.

---

# 22. Order

Order is a historical financial record.

Fields:

```text
id
order_number
user_id nullable

customer_name
customer_email
customer_phone

subtotal
discount_amount
shipping_cost
tax_amount
total_amount

coupon_id nullable
coupon_code_snapshot nullable

payment_method
payment_status
order_status

shipping_address_snapshot
billing_address_snapshot

customer_note
admin_note

created_at
updated_at
```

`order_number` must be unique.

Example:

```text
MC-20261019-000123
```

Guest orders:

```text
user_id = NULL
```

Logged-in orders:

```text
user_id = customer
```

---

# 23. OrderItem

Never rely on the current Product name/price for historical orders.

Fields:

```text
id
order_id
variant_id nullable

product_name_snapshot
variant_name_snapshot
sku_snapshot

unit_price
quantity
discount_amount
total_amount
created_at
```

The snapshot fields are intentional.

Even if:

```text
Product.name changes
SKU changes
Price changes
Product is archived
```

the old order remains historically correct.

Relationship:

```text
Order 1 ──── N OrderItem
ProductVariant 1 ──── N OrderItem
```

The variant foreign key may be nullable because historical records must remain intact even if a product is eventually retired from active catalog management.

---

# 24. Order Status

Use choices:

```text
PENDING
CONFIRMED
PROCESSING
READY_TO_SHIP
SHIPPED
DELIVERED
CANCELLED
RETURN_REQUESTED
RETURNED
REFUNDED
```

Never allow arbitrary status strings from the frontend.

---

# 25. Payment

Fields:

```text
id
order_id
payment_method
transaction_id nullable
amount
status
paid_at nullable
created_at
updated_at
```

Payment methods:

```text
COD
BKASH
NAGAD
ROCKET
BANK
ONLINE
```

Initial production requirement:

```text
COD
```

Payment status:

```text
PENDING
AUTHORIZED
PAID
FAILED
REFUNDED
```

COD order:

```text
payment_method = COD
payment_status = PENDING
```

When the customer receives the order:

```text
payment_status = PAID
```

if the business confirms payment collection.

---

# 26. COD Anti-Fraud Design

Cash on Delivery creates a significant fake-order risk.

The system must not blindly treat every order as legitimate.

Recommended order risk checks:

```text
phone number frequency
IP frequency
session frequency
email frequency
same shipping address frequency
too many orders in short period
too many cancelled orders
too many failed deliveries
coupon abuse
suspicious quantity
rapid repeated checkout attempts
```

Potential order states:

```text
PENDING
REVIEW_REQUIRED
CONFIRMED
```

A suspicious order can be held for staff verification.

Do not automatically reject every repeated IP because multiple legitimate customers can share an IP through mobile networks, offices, schools, or NAT.

Use multiple signals.

---

# 27. Coupon System

## Coupon

Fields:

```text
id
code
name
description

discount_type
discount_value

minimum_order_amount
maximum_discount_amount

usage_limit
usage_limit_per_user
used_count

start_at
end_at
is_active

created_at
updated_at
```

Discount types:

```text
PERCENTAGE
FIXED_AMOUNT
FREE_SHIPPING
```

Coupon code:

```text UNIQUE
```

Store normalized uppercase codes.

Example:

```text
MRPC20
```

---

# 28. Coupon Applicability
coupon will be applicable on only for loggedin users. not for the guest users 
Use separate relationship tables:

```text
CouponProduct
CouponCategory
CouponBrand
```

This allows:

```text
All products
Specific products
Specific categories
Specific brands
```

Relationships:

```text
Coupon N ──── N Product
Coupon N ──── N Category
Coupon N ──── N Brand
```

Use explicit through models instead of hiding important business rules inside an opaque ManyToManyField.

---

# 29. CouponUsage

Fields:

```text
id
coupon_id
user_id nullable
order_id
discount_amount
used_at
```

Relationships:

```text
Coupon 1 ──── N CouponUsage
User 1 ──── N CouponUsage
Order 1 ──── 1 CouponUsage
```

For guest customers, coupon abuse prevention must also use order phone/email/session/IP risk signals.

---

# 30. Customer Profile

Use Django's authentication system.

Do not implement custom password hashing.

CustomerProfile:

```text
user_id
phone
profile_image
marketing_opt_in
created_at
updated_at
```

CustomerAddress:

```text
id
user_id
label
recipient_name
phone
address_line_1
address_line_2
city
area
postal_code
is_default
created_at
updated_at
```

Do not rely on the address table for historical orders.

The order stores an immutable address snapshot.

---

# 31. Wishlist

Wishlist:

```text
id
user_id
created_at
```

WishlistItem:

```text
id
wishlist_id
variant_id
created_at
```

Constraint:

```text
UNIQUE(wishlist_id, variant_id)
```

---

# 32. Reviews

Fields:

```text
id
product_id
user_id nullable
order_item_id nullable
rating
title
comment
status
created_at
updated_at
```

Rating:

```text
1 to 5
```

Status:

```text
PENDING
APPROVED
REJECTED
```

`order_item_id` allows future "Verified Purchase" functionality.

---

# 33. Custom PC Builder

Build:

```text
id
user_id nullable
name
status
total_price
created_at
updated_at
```

BuildItem:

```text
id
build_id
category_id
variant_id
quantity
unit_price
```

BuildRequest:

```text
id
customer_name
phone
email
budget
purpose
notes
status
created_at
updated_at
```

Build request statuses:

```text
NEW
CONTACTED
QUOTED
APPROVED
BUILDING
COMPLETED
CANCELLED
```

---

# 34. Shipping

ShippingZone:

```text
id
name
description
is_active
```

ShippingRate:

```text
id
zone_id
minimum_order_amount
maximum_order_amount
rate
```

Example:

```text
Dhaka
Outside Dhaka
```

Do not hardcode shipping prices into JavaScript.

---

# 35. CMS

The owner must be able to manage the website without code.

## Banner

```text
id
title
subtitle
image
button_text
button_url
start_at
end_at
is_active
display_order
```

## HomeSection

```text
id
section_type
title
subtitle
display_order
is_active
```

Types:

```text
HERO
FEATURED_PRODUCTS
CATEGORY_GRID
BRANDS
FLASH_SALE
BEST_SELLERS
NEW_ARRIVALS
CUSTOM_PC
PROMOTION
```

## Page

```text
id
title
slug
content
meta_title
meta_description
is_published
published_at
updated_at
```

Pages:

```text
About Us
Privacy Policy
Terms & Conditions
Return Policy
Warranty Policy
Shipping Policy
```

## SiteSettings

```text
id
store_name
logo
favicon
phone
email
address
facebook_url
youtube_url
instagram_url
footer_text
currency
default_shipping_cost
google_analytics_id
updated_at
```

---

# 36. Contact Messages

```text
ContactMessage
```

Fields:

```text
id
name
email
phone
subject
message
status
created_at
updated_at
```

Statuses:

```text
NEW
READ
REPLIED
CLOSED
```

---

# 37. AuditLog

For important administrative actions:

```text
id
user_id
action
model_name
object_id
old_data
new_data
ip_address
created_at
```

Examples:

```text
PRODUCT_PRICE_CHANGED
STOCK_ADJUSTED
COUPON_CREATED
ORDER_STATUS_CHANGED
PRODUCT_ARCHIVED
USER_PERMISSION_CHANGED
SITE_SETTING_CHANGED
```

Sensitive information should not be unnecessarily copied into audit logs.

---

# 38. Role-Based Permissions

Do not give every staff member Django superuser privileges.

Recommended roles:

```text
OWNER
ADMIN
MANAGER
INVENTORY_MANAGER
ORDER_MANAGER
CONTENT_MANAGER
```

Examples:

### Inventory Manager

Can:

```text
manage stock
receive stock
adjust inventory
manage refurbished units
```

Cannot:

```text
change staff permissions
delete financial records
change security settings
```

### Content Manager

Can:

```text
manage banners
homepage sections
pages
product images
```

Cannot:

```text
change inventory
change payment settings
manage staff
```

---

# 39. Rate Limiting and Abuse Protection

This must be handled partly at the infrastructure/server layer and partly inside Django.

Infrastructure protections can include:

```text
WAF
reverse proxy
CDN
firewall
server-level request limits
bot protection
```

But business-specific abuse protection MUST exist in the Django application.

Use a proper rate-limiting strategy, preferably backed by Redis in production.

Potential Django rate limits:

```text
login attempts
password reset requests
OTP requests
coupon validation
cart mutation endpoints
checkout attempts
order creation
contact forms
review submission
custom PC requests
API endpoints
```

Do not rate-limit normal product browsing aggressively.

---

# 40. Brute-Force Protection

Protect:

```text
/login/
/password-reset/
/dashboard/login/
```

Use:

```text
IP-based limits
account-based limits
progressive delays
temporary lockouts
CAPTCHA/challenge after suspicious activity
```

Do not rely only on frontend validation.

Recommended approach:

```text
Repeated failed login
        ↓
rate limit
        ↓
progressive delay
        ↓
temporary block/challenge
```

For staff accounts, security should be stricter than normal customer accounts.

---

# 41. Fake Cart Automation Protection

Cart endpoints can be abused by bots.

Protect:

```text
POST /cart/add/
POST /cart/update/
POST /cart/remove/
```

Use:

```text
request rate limiting
session validation
CSRF
server-side product/price validation
maximum quantity limits
bot detection where appropriate
```

Never allow:

```text
quantity = 999999999
```

or arbitrary product IDs without validation.

---

# 42. Fake Order Protection

Protect checkout and order creation with:

```text
rate limiting
CSRF
server-side price recalculation
inventory validation
coupon validation
phone validation
email validation where applicable
request/session checks
order-frequency checks
risk scoring
duplicate-order detection
```

Recommended:

```text
Same phone + same cart + repeated checkout within a short window
→ suspicious
```

Do not block solely by IP.

Mobile networks can place many legitimate users behind the same public IP.

---

# 43. Checkout Transaction

Order creation must use:

```python
transaction.atomic()
```

Within the transaction:

```text
1. Re-read cart
2. Lock relevant inventory rows
3. Verify stock
4. Recalculate prices
5. Validate coupon
6. Calculate shipping
7. Calculate final total
8. Create Order
9. Create OrderItems
10. Reserve/decrease stock
11. Create Payment
12. Create inventory transactions
13. Clear cart
```

If any critical step fails:

```text
ROLLBACK
```

This prevents inconsistent orders and inventory.

---

# 44. Concurrency Protection

Example:

```text
Stock = 1

Customer A → checkout
Customer B → checkout
```

The system must not allow:

```text
A buys 1
B buys 1
stock becomes -1
```

Use PostgreSQL row locking where necessary:

```python
select_for_update()
```

inside a transaction.

Do not solve concurrency only with JavaScript.

---

# 45. Historical Data Rules

Never destroy important business history.

Do not physically delete:

```text
Order
OrderItem
Payment
InventoryTransaction
CouponUsage
AuditLog
```

unless there is a carefully designed legal/data-retention policy.

Prefer:

```text
status = ARCHIVED
is_active = False
```

for catalog entities.

---

# 46. Product Deletion Policy

Product deletion should generally mean:

```text
ARCHIVE
```

not:

```text
DELETE FROM product
```

If a product has historical orders:

```text
Product.status = ARCHIVED
Product.is_active = False
```

Historical orders remain intact.

---

# 47. Media Storage Strategy

Do not store thousands of large images directly in PostgreSQL.

Bad:

```text
PostgreSQL
└── millions of binary image blobs
```

Recommended:

```text
PostgreSQL
└── image metadata + object storage key

Object Storage
└── actual image files
```

Use CDN delivery for production.

Recommended image processing:

```text
Original
Thumbnail
Medium
Large
WebP/AVIF where supported
```

Do not make every page download the original 5 MB image.

---

# 48. Image Optimization

For product images:

```text
Maximum upload size
dimension validation
format validation
compression
responsive variants
lazy loading
WebP/AVIF conversion
thumbnail generation
```

Never trust the file extension alone.

Validate actual file content/type.

---

# 49. Image Cleanup Recommendation

The requested two-day policy should be treated as:

> **Eligibility for cleanup, not immediate deletion.**

Recommended lifecycle:

```text
ACTIVE
   ↓
OUT_OF_STOCK
   ↓
0 stock for 2 days
   ↓
CLEANUP_CANDIDATE
   ↓
grace period
   ↓
FINAL_RECHECK
   ↓
OBJECT_DELETED
   ↓
METADATA_RETENTION
   ↓
METADATA_PURGED later if safe
```

This prevents accidental deletion after a fast restock.

---

# 50. Scheduled Tasks

The system will eventually need scheduled background work.

Examples:

```text
image cleanup
expired cart cleanup
expired coupon checks
abandoned cart cleanup
order reminders
low-stock notifications
analytics aggregation
temporary file cleanup
```

Recommended architecture:

```text
Django
   │
   ▼
Celery
   │
   ▼
Redis
```

with:

```text
Celery Beat
```

for scheduled jobs.

If the initial deployment environment cannot support Celery, use its supported scheduled-job mechanism temporarily, but keep business operations designed so they can move to a worker system later.

---

# 51. Database Index Strategy

Do not index everything.

Recommended indexes:

```text
Product.slug UNIQUE
Product.status
Product.is_active
Product.category_id
Product.brand_id

ProductVariant.sku UNIQUE
ProductVariant.product_id

Inventory.variant_id UNIQUE
Inventory.out_of_stock_since

InventoryTransaction.variant_id
InventoryTransaction.created_at

Order.order_number UNIQUE
Order.user_id
Order.status
Order.created_at

OrderItem.order_id
OrderItem.variant_id

Coupon.code UNIQUE
Coupon.is_active
Coupon.start_at
Coupon.end_at

Review.product_id
Review.status

ProductImage.product_id
ProductImage.variant_id
ProductImage.status
```

Useful composite indexes:

```text
(category_id, is_active)
(brand_id, is_active)
(status, created_at)
```

Use `Meta.indexes` in Django.

---

# 52. Database Constraints

Use database-level constraints whenever possible.

Examples:

```text
price >= 0
quantity >= 0
reserved_quantity >= 0
rating BETWEEN 1 AND 5
discount >= 0
```

Unique constraints:

```text
Product.slug
Brand.slug
Category.slug
ProductVariant.sku
Coupon.code
Order.order_number
```

Composite unique constraints:

```text
CartItem(cart, variant)
WishlistItem(wishlist, variant)
ProductVariantAttribute(variant, attribute)
```

Database constraints are the final safety net.

---

# 53. Important Foreign Key Policies

Recommended general policy:

```text
User → Profile
CASCADE

User → CustomerAddress
CASCADE

Category → Product
PROTECT

Brand → Product
PROTECT

Product → ProductVariant
PROTECT

Product → ProductImage
CASCADE or controlled archival depending on media policy

ProductVariant → CartItem
PROTECT or nullable historical handling

Order → OrderItem
CASCADE

Order → Payment
PROTECT

Order → CouponUsage
PROTECT

Coupon → CouponUsage
PROTECT
```

The exact choice must follow whether the child is historical/business-critical.

The principle is:

> Never allow an innocent admin delete action to destroy financial history.

---

# 54. ERD — High-Level

```text
                         ┌──────────────┐
                         │    BRAND     │
                         └──────┬───────┘
                                │ 1:N
                                ▼
┌──────────────┐          ┌──────────────┐
│   CATEGORY   │─────────▶│   PRODUCT    │
└──────┬───────┘    1:N   └──────┬───────┘
       │                          │ 1:N
       │                          ▼
       │                   ┌──────────────┐
       │                   │   VARIANT    │
       │                   └──────┬───────┘
       │                          │
       │              ┌───────────┼──────────────┐
       │              │           │              │
       ▼              ▼           ▼              ▼
 CouponCategory   Inventory   CartItem      OrderItem
                                      │              │
                                      ▼              ▼
                                     Cart           Order
                                                     │
                                      ┌──────────────┼──────────────┐
                                      ▼              ▼              ▼
                                   Payment      CouponUsage     OrderItem


PRODUCT ──── PRODUCT IMAGE
PRODUCT ──── REVIEW
VARIANT ──── PRODUCT VARIANT ATTRIBUTE ──── ATTRIBUTE
ATTRIBUTE ──── ATTRIBUTE VALUE

COUPON ──── COUPON PRODUCT ──── PRODUCT
COUPON ──── COUPON CATEGORY ─── CATEGORY
COUPON ──── COUPON BRAND ────── BRAND

USER ──── CUSTOMER PROFILE
USER ──── CUSTOMER ADDRESS
USER ──── WISHLIST ──── WISHLIST ITEM ─── VARIANT

USER ──── BUILD ──── BUILD ITEM ─── VARIANT
BUILD REQUEST

CMS:
BANNER
HOME SECTION
PAGE
SITE SETTINGS

INVENTORY:
INVENTORY
INVENTORY ITEM
INVENTORY TRANSACTION

AUDIT:
AUDIT LOG
```

---

# 55. Exact Django Model Architecture

The models should be split by Django app.

Do NOT create one giant `models.py`.

Recommended:

```text
accounts/models.py
catalog/models.py
inventory/models.py
cart/models.py
orders/models.py
payments/models.py
promotions/models.py
pc_builder/models.py
reviews/models.py
shipping/models.py
cms/models.py
audit/models.py
```

---

# 56. Base Model

Create a reusable abstract model:

```python
import uuid

from django.db import models


class UUIDTimeStampedModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

All appropriate models should inherit from it.

---

# 57. Important Model Design Rules

Every model must explicitly consider:

```text
Primary key
Foreign keys
on_delete
null
blank
default
unique
db_index
choices
constraints
indexes
related_name
timestamps
```

Do not blindly add `null=True` everywhere.

For strings:

```text
blank=True
```

is usually preferred over `null=True`.

For nullable relationships:

```text
null=True
blank=True
```

is appropriate.

---

# 58. Django Model Meta Strategy

Use:

```python
class Meta:
    ordering = ["-created_at"]

    indexes = [
        models.Index(fields=["status", "created_at"]),
    ]

    constraints = [
        models.UniqueConstraint(
            fields=["cart", "variant"],
            name="unique_cart_variant",
        ),
    ]
```

Give constraints explicit names.

This makes migrations and database debugging much easier.

---

# 59. Admin Dashboard Requirement

The custom dashboard should provide:

```text
Dashboard
Catalog
Inventory
Orders
Customers
Coupons
Custom PC
Reviews
Shipping
CMS
Reports
Users & Permissions
Audit Logs
Settings
```

A nontechnical store owner should never need:

```text
terminal
manage.py
SQL
Django Admin
Python
Git
```

for ordinary store management.

Django Admin should remain available to authorized technical administrators as a fallback.

---

# 60. Dashboard Product Management

The product form should support:

```text
Product name
Category
Brand
Description
Condition
Product type
SEO title
SEO description
Images
Variants
SKU
Barcode
Cost price
Selling price
Compare-at price
Attributes
Stock
Featured
New arrival
Best seller
Active
```

All from the dashboard.

---

# 61. Dashboard Inventory Management

The owner/staff should see:

```text
Current stock
Available stock
Reserved stock
Low stock
Out of stock
Stock history
Refurbished units
Serial numbers
Purchase price
Selling price
```

Every manual adjustment should require a reason and create an `InventoryTransaction`.

---

# 62. Dashboard Coupon Management

The owner should be able to select:

```text
Coupon code
Percentage/fixed/free shipping
Minimum order amount
Maximum discount
Start date
End date
Usage limit
Per-user usage limit
Specific products
Specific categories
Specific brands
```

No code changes required.

---

# 63. Dashboard Order Management

Order page:

```text
Order number
Customer
Phone
Address
Items
Subtotal
Discount
Shipping
Total
Payment method
Payment status
Order status
Coupon
Risk indicators
Internal notes
Timeline
```

Staff can update:

```text
PENDING
→ CONFIRMED
→ PROCESSING
→ READY_TO_SHIP
→ SHIPPED
→ DELIVERED
```

with appropriate permissions.

---

# 64. Dashboard Reports

Eventually provide:

```text
Daily sales
Monthly sales
Yearly sales
Best-selling products
Best-selling categories
Best-selling brands
Low-stock products
Out-of-stock products
Coupon usage
Customer acquisition
COD orders
Cancelled orders
Returned orders
Profit estimates
```

Important:

Revenue and profit are different.

Do not call:

```text
sales - cost
```

"profit" unless all relevant costs are actually accounted for.

---

# 65. Search Architecture

Initial version:

```text
PostgreSQL search
```

Use indexed fields and PostgreSQL search capabilities where appropriate.

Do not immediately introduce Elasticsearch/OpenSearch.

When the catalog becomes genuinely large and search requirements become complex:

```text
PostgreSQL
+
OpenSearch/Elasticsearch
```

can be introduced later.

The application should keep search logic behind a service layer so this migration does not require rewriting the storefront.

---

# 66. Caching

Eventually use Redis for:

```text
rate limiting
sessions if required
temporary cart data if appropriate
frequently accessed catalog fragments
dashboard statistics
```

Do not cache financial truth blindly.

Order totals, stock, payment status, and coupon validity must always be validated against authoritative database state.

---

# 67. Scalability Strategy

The architecture should support:

```text
Phase 1:
One Django application
One PostgreSQL database
Object storage
CDN

Phase 2:
Django
PostgreSQL
Redis
Background worker

Phase 3:
Multiple application instances
Load balancer
CDN
Redis
PostgreSQL managed service
Object storage

Phase 4:
Read replicas / specialized search
if actual traffic requires them
```

Do not prematurely build microservices.

A modular Django monolith is the correct starting architecture.

---

# 68. Transactional Rules

Critical operations must be transactional:

```text
Create order
Reserve stock
Release stock
Cancel order
Return order
Apply coupon usage
Payment state changes
Inventory adjustments
```

Use:

```python
transaction.atomic()
```

and row-level locking where necessary.

---

# 69. Order Creation Service

Do not put the entire checkout process inside a Django view.

Use something like:

```text
orders/services.py
```

with a service:

```python
create_order_from_cart(...)
```

The view should coordinate HTTP.

The service should contain business logic.

This separation is essential for testing.

---

# 70. Coupon Service

Use:

```text
promotions/services.py
```

with logic such as:

```text
validate_coupon()
calculate_coupon_discount()
check_coupon_scope()
check_coupon_usage()
```

Never trust coupon calculations coming from JavaScript.

---

# 71. Inventory Service

Use:

```text
inventory/services.py
```

for:

```text
reserve_stock()
release_stock()
decrease_stock()
increase_stock()
adjust_stock()
mark_out_of_stock()
mark_restocked()
```

Views should not manually modify inventory fields.

---

# 72. Media Cleanup Service

Use:

```text
inventory/tasks.py
```

or a dedicated media service.

Conceptual functions:

```text
find_cleanup_candidates()
mark_media_for_cleanup()
recheck_media_candidate()
delete_media_object()
purge_old_media_metadata()
```

This must be safe to run multiple times.

---

# 73. API / AJAX Rules

Even though this is primarily Django server-rendered:

```text
Use JavaScript/AJAX for:
cart updates
coupon validation
product filtering
search suggestions
dashboard interactions
image uploads
dynamic variant management
```

But every AJAX endpoint must have:

```text
authentication where required
authorization
CSRF protection
validation
rate limiting
server-side business rules
```

---

# 74. Security Rules

Mandatory:

```text
DEBUG=False in production
SECRET_KEY from environment
DATABASE credentials from environment
ALLOWED_HOSTS configured
CSRF protection enabled
HTTPS
secure cookies
HSTS where appropriate
clickjacking protection
XSS protection
secure file uploads
request size limits
password hashing through Django
staff permission checks
audit logging
rate limiting
```

Never commit:

```text
.env
database passwords
API keys
secret keys
payment credentials
cloud storage credentials
```

to Git.

---

# 75. File Upload Security

Product images and CMS images must have:

```text
extension validation
MIME/content validation
size limit
dimension limit
image decoding validation
safe filename generation
randomized storage key
```

Never use user-provided filenames directly as storage paths.

---

# 76. Fake Order Prevention — Recommended Risk Score

Eventually create an internal risk score:

```text
risk_score = 0
```

Signals may add points:

```text
too many orders from phone
too many cancelled orders
too many failed deliveries
many orders from same IP
rapid checkout repetition
unusual quantity
coupon abuse
known blocked identifier
```

Then:

```text
0–29     LOW
30–59    MEDIUM
60–79    HIGH
80+      REVIEW_REQUIRED
```

The exact values should be configurable after observing real business data.

Do not automatically ban customers based on one signal.

---

# 77. Guest Checkout Abuse Controls

Guest checkout is good for conversion but increases abuse.

Use:

```text
CSRF token
session identifier
rate limits
phone validation
order frequency checks
cart limits
quantity limits
server-side price verification
coupon limits
risk scoring
```

Optional future verification:

```text
SMS OTP
```

Do not force OTP on every legitimate customer unless business data shows it is necessary.

---

# 78. Cart Expiration

Guest carts should expire eventually.

Example:

```text
7–30 days
```

depending on business requirements.

A background task can delete or archive expired cart data.

Do not let abandoned carts grow forever.

---

# 79. Data Retention

Recommended:

### Keep long-term

```text
Orders
OrderItems
Payments
InventoryTransactions
CouponUsage
AuditLogs
```

### Can expire

```text
Guest carts
Temporary sessions
Temporary checkout data
Temporary upload records
```

### Archive rather than delete

```text
Products
Variants
Categories
Brands
Coupons
Pages
```

### Cleanup carefully

```text
Unused media
Temporary files
Expired promotional assets
```

---

# 80. Backup Strategy

Production PostgreSQL must have:

```text
automated backups
point-in-time recovery if supported
backup retention
restore testing
```

A backup that has never been restored is not proven reliable.

Test:

```text
backup → restore → verify database
```

periodically.

Object storage should also have appropriate versioning/backup strategy.

---

# 81. Observability

Production should have:

```text
application logs
database monitoring
error tracking
background-task monitoring
slow-query monitoring
uptime monitoring
security alerts
```

Important metrics:

```text
500 errors
checkout failures
payment failures
database connection exhaustion
slow queries
rate-limit blocks
fake-order flags
inventory inconsistencies
```

---

# 82. Testing Strategy

Before production:

### Model tests

```text
constraints
relationships
validation
```

### Service tests

```text
order creation
coupon calculation
inventory reservation
returns
stock restoration
```

### Security tests

```text
unauthorized dashboard access
CSRF
rate limits
brute force
file upload attacks
coupon abuse
price manipulation
```

### Concurrency tests

Test:

```text
two users purchasing the last unit simultaneously
```

This is mandatory.

---

# 83. Critical Business Invariants

These rules must ALWAYS be true:

```text
available stock >= 0

reserved stock >= 0

reserved stock <= physical stock

order total = validated calculation

coupon discount <= configured maximum

product SKU is unique

order number is unique

coupon code is unique

cart cannot contain negative quantity

order cannot be created without sufficient stock

historical order prices never change

payment amount cannot exceed validated order amount

staff cannot perform actions outside their role
```

These are architectural invariants, not merely frontend validation rules.

---

# 84. Recommended Development Order

Do not start with the homepage.

Build in this order:

```text
1. Project configuration
2. PostgreSQL connection
3. Base model
4. Accounts
5. Catalog
6. Product variants
7. Attributes
8. Inventory
9. Inventory transactions
10. Cart
11. Orders
12. Payments / COD
13. Coupons
14. Shipping
15. Reviews
16. Custom PC Builder
17. CMS
18. Dashboard
19. Rate limiting
20. Risk detection
21. Media lifecycle
22. Reports
23. Testing
24. Production deployment
```

---

# 85. Do Not Make These Architectural Mistakes

## Mistake 1

Putting everything in one `models.py`.

**Don't.**

---

## Mistake 2

Using SQLite in production.

**Don't.**

Use PostgreSQL.

---

## Mistake 3

Putting images inside PostgreSQL.

**Don't.**

Use object storage.

---

## Mistake 4

Deleting products when they go out of stock.

**Don't.**

Archive them.

---

## Mistake 5

Deleting images immediately after two days of zero stock.

**Don't.**

Two days should make them **eligible for cleanup**, followed by revalidation and a grace period.

---

## Mistake 6

Trusting browser prices.

**Don't.**

Recalculate everything server-side.

---

## Mistake 7

Allowing frontend JavaScript to determine stock.

**Don't.**

PostgreSQL/Django is authoritative.

---

## Mistake 8

Creating orders without transactions.

**Don't.**

Use `transaction.atomic()`.

---

## Mistake 9

Ignoring concurrency.

**Don't.**

Use PostgreSQL row locks for stock-sensitive operations.

---

## Mistake 10

Giving the store owner raw database access.

**Don't.**

Build the management dashboard.

---

## Mistake 11

Giving all staff superuser privileges.

**Don't.**

Use role-based permissions.

---

## Mistake 12

Building microservices immediately.

**Don't.**

Start with a modular Django monolith.

---

# 86. Final Target Architecture

```text
                         ┌───────────────────────┐
                         │      CUSTOMERS        │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   DJANGO STOREFRONT   │
                         │ HTML / CSS / Bootstrap│
                         │       JavaScript      │
                         └───────────┬───────────┘
                                     │
                  ┌──────────────────┼──────────────────┐
                  │                  │                  │
                  ▼                  ▼                  ▼
              Catalog             Cart              Checkout
                  │                  │                  │
                  │                  │                  ▼
                  │                  │              Order Service
                  │                  │                  │
                  │                  │          ┌───────┴────────┐
                  │                  │          ▼                ▼
                  │                  │      Inventory          Payment
                  │                  │          │
                  │                  │          ▼
                  │                  │    PostgreSQL
                  │                  │
                  ▼                  ▼
             PostgreSQL          PostgreSQL


                         ┌───────────────────────┐
                         │  OWNER / STAFF        │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │ CUSTOM ADMIN DASHBOARD│
                         └───────────┬───────────┘
                                     │
       ┌───────────────┬────────────┼────────────┬──────────────┐
       ▼               ▼            ▼            ▼              ▼
    Catalog         Orders      Inventory     Coupons          CMS
       │               │            │            │              │
       └───────────────┴────────────┴────────────┴──────────────┘
                                     │
                                     ▼
                               PostgreSQL


                         ┌───────────────────────┐
                         │   BACKGROUND WORKERS  │
                         │ Celery / Scheduler    │
                         └───────────┬───────────┘
                                     │
             ┌───────────────────────┼─────────────────────┐
             ▼                       ▼                     ▼
       Media Cleanup          Cart Cleanup          Notifications
             │
             ▼
       Object Storage
             │
             ▼
            CDN


                         ┌───────────────────────┐
                         │       SECURITY        │
                         ├───────────────────────┤
                         │ HTTPS                 │
                         │ CSRF                  │
                         │ Rate Limiting         │
                         │ Brute Force Defense   │
                         │ WAF/CDN               │
                         │ RBAC                  │
                         │ Audit Logs            │
                         │ Validation            │
                         └───────────────────────┘
```

---

# 87. Final Engineering Rules for Copilot

When using GitHub Copilot or another coding assistant on this project, give it these rules:

```text
1. Do not invent database fields without checking the architecture.
2. Do not create duplicate models for existing concepts.
3. Do not put business logic inside templates.
4. Do not trust frontend calculations.
5. Do not use floating-point numbers for money.
6. Do not use SQLite in production.
7. Do not store product images as database blobs.
8. Do not delete historical orders.
9. Do not hard-delete products that have historical sales.
10. Do not modify historical OrderItem prices when Product prices change.
11. Use transactions for order/inventory operations.
12. Use row-level locking for concurrent stock-sensitive operations.
13. Use explicit ForeignKey on_delete behavior.
14. Add indexes based on actual query patterns.
15. Add database constraints for important invariants.
16. Do not expose unrestricted HTML/JavaScript execution through the CMS.
17. Never trust price, quantity, discount, coupon, or stock values from the browser.
18. All staff dashboard actions must pass authorization checks.
19. All important inventory changes must create InventoryTransaction records.
20. All important administrative changes should be auditable.
21. Guest checkout must remain supported.
22. COD must remain a first-class payment method.
23. Rate limiting must protect authentication, cart mutation, checkout, coupon, review, and other abuse-prone endpoints.
24. Image cleanup must be asynchronous and revalidated before deletion.
25. Two days of zero stock means "eligible for cleanup", not immediate deletion.
26. Media should have a grace period before physical deletion.
27. Prefer a modular Django monolith over premature microservices.
28. Write tests for business logic before changing critical services.
29. Never make destructive migrations without explicit review.
30. Before changing a model, check all dependent models, migrations, services, views, templates, tests, and dashboard forms.
```

---

# 88. Definition of Done

The Mr. Computers platform should not be considered production-ready until:

```text
[ ] PostgreSQL configured
[ ] Database migrations clean
[ ] Catalog working
[ ] Product variants working
[ ] Dynamic attributes working
[ ] Product images working
[ ] Object storage configured
[ ] Inventory working
[ ] Inventory transaction history working
[ ] Refurbished unit tracking working
[ ] Guest cart working
[ ] User cart working
[ ] Guest checkout working
[ ] COD working
[ ] Order creation transactional
[ ] Concurrent stock protection tested
[ ] Coupons working
[ ] Coupon abuse protection working
[ ] Shipping calculation working
[ ] Customer accounts working
[ ] Order tracking working
[ ] Reviews working
[ ] Custom PC builder working
[ ] CMS working
[ ] Custom dashboard working
[ ] RBAC working
[ ] Audit logging working
[ ] Brute-force protection working
[ ] Rate limiting working
[ ] Fake-order protection working
[ ] Image cleanup scheduler working
[ ] Media cleanup revalidation working
[ ] Backup configured
[ ] Restore tested
[ ] Error monitoring configured
[ ] Security headers configured
[ ] HTTPS enabled
[ ] Production secrets outside Git
[ ] Automated tests passing
[ ] Load/concurrency tests passing
```

---

# 89. Ruthless Mentor Directive

Do not begin by designing a beautiful homepage.

The correct order is:

```text
DATABASE
    ↓
DOMAIN MODEL
    ↓
DJANGO MODELS
    ↓
BUSINESS SERVICES
    ↓
TRANSACTIONS
    ↓
SECURITY
    ↓
DASHBOARD
    ↓
STOREFRONT
    ↓
DESIGN POLISH
```

A beautiful e-commerce website with a weak database is a decorated bug.

A boring-looking website with a strong domain model can be improved indefinitely.

For Mr. Computers, **the database, inventory system, order system, and security model are the foundation.**

Build those correctly first.
