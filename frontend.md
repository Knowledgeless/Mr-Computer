# Mr. Computers — Frontend UI/UX Specification

**Document:** `FRONTEND_UI_UX_SPEC.md`  
**Project:** Mr. Computers E-commerce Platform  
**Purpose:** Implementation-ready frontend specification for GitHub Copilot  
**Frontend Stack:** HTML5 + CSS3 + Bootstrap 5 + Vanilla JavaScript + Django Templates  
**Design Goal:** Modern, premium, clean, fast, trustworthy, product-first e-commerce experience.

---

## 1. Purpose

This document defines the complete frontend design and implementation standard for the Mr. Computers website.

The frontend must feel like a **professional modern electronics retailer**, not a generic Bootstrap template.

The design should communicate:

- Trust
- Technical expertise
- Product quality
- Easy shopping
- Fast navigation
- Professional business operation
- Strong visual hierarchy
- Excellent mobile usability

The interface must work for both:

1. **Customers** — storefront, search, products, cart, checkout, account.
2. **Business staff/owner** — dashboard, products, inventory, orders, coupons, content, reports and settings.

The owner must be able to understand the dashboard without technical knowledge.

---

# 2. Non-Negotiable Design Principles

## 2.1 Product First

Products are the primary visual focus.

Do not allow:

- Excessive decorative graphics
- Huge empty hero sections
- Unnecessary animations
- Overloaded cards
- Excessive gradients
- Too many colors

The user should quickly understand:

> What is this product?  
> How much does it cost?  
> Is it available?  
> What can I do next?

---

## 2.2 Modern, Not Flashy

Use:

- Clean layouts
- Generous spacing
- Strong typography
- Subtle borders
- Soft shadows
- Rounded corners
- Controlled color usage
- Small interaction animations

Avoid:

- Neon-heavy gaming aesthetics everywhere
- Excessive glassmorphism
- Giant gradients
- Excessive shadows
- 3D effects
- Bouncing UI
- Auto-playing distracting animations

---

## 2.3 Consistency Over Creativity

Every page must use the same:

- Header
- Footer
- Typography
- Buttons
- Form controls
- Cards
- Badges
- Spacing
- Border radius
- Colors
- Feedback patterns
- Responsive behavior

Do not create a new visual style for every page.

---

# 3. Brand Personality

Mr. Computers should visually feel:

- Professional
- Technical
- Reliable
- Modern
- Approachable
- Efficient
- Premium but not luxury
- Suitable for both normal customers and computer enthusiasts

Tone:

> Clear + confident + helpful + concise.

Avoid aggressive sales language and fake urgency.

Do not use messages such as:

- "BUY NOW OR REGRET IT!"
- "ONLY 1 LEFT!!!" unless the backend genuinely confirms it
- "BEST PRODUCT IN THE WORLD"

---

# 4. Technology Rules

Use:

- HTML5
- CSS3
- Bootstrap 5
- Vanilla JavaScript
- Django templates
- Bootstrap Icons or another single consistent icon library

Do not introduce React, Vue, jQuery, Tailwind, or another frontend framework unless explicitly requested.

## JavaScript

Use separate JavaScript files.

Do not place large JavaScript blocks inside HTML.

Avoid inline:

```html
onclick=""
onchange=""
onsubmit=""
```

Use event listeners and `data-*` attributes.

Example:

```html
<button
    type="button"
    class="btn btn-primary js-add-to-cart"
    data-product-id="123">
    Add to Cart
</button>
```

---

# 5. Design System

## 5.1 Color System

Use CSS variables.

Recommended starting palette:

```css
:root {
    --mc-primary: #0f172a;
    --mc-primary-soft: #1e293b;

    --mc-accent: #2563eb;
    --mc-accent-hover: #1d4ed8;

    --mc-success: #16a34a;
    --mc-warning: #d97706;
    --mc-danger: #dc2626;
    --mc-info: #0891b2;

    --mc-background: #f8fafc;
    --mc-surface: #ffffff;
    --mc-surface-soft: #f1f5f9;

    --mc-text: #0f172a;
    --mc-text-secondary: #475569;
    --mc-text-muted: #64748b;

    --mc-border: #e2e8f0;
    --mc-border-dark: #cbd5e1;

    --mc-radius-sm: 0.5rem;
    --mc-radius-md: 0.75rem;
    --mc-radius-lg: 1rem;
    --mc-radius-xl: 1.25rem;

    --mc-shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
    --mc-shadow-md: 0 8px 24px rgba(15, 23, 42, 0.08);
    --mc-shadow-lg: 0 16px 40px rgba(15, 23, 42, 0.12);
}
```

These are design tokens, not hard requirements. Keep the visual system coherent if the brand palette is changed later.

### Color usage rule

Use the accent color primarily for:

- Primary CTA
- Links
- Active navigation
- Important actions
- Selected states

Do not make every element blue.

---

# 6. Typography

Recommended font:

- Inter

Fallback:

```css
font-family:
    Inter,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
```

Hierarchy:

- H1 — page/hero title
- H2 — major section
- H3 — card/subsection
- Body — normal information
- Small — metadata/helper text

Avoid using too many font weights.

Recommended:

- 400 — normal
- 500 — medium
- 600 — semibold
- 700 — bold

---

# 7. Spacing System

Prefer Bootstrap spacing utilities.

Use a consistent rhythm:

- 4px — tiny
- 8px — compact
- 12px — small
- 16px — standard
- 24px — medium
- 32px — section spacing
- 48px — large
- 64px+ — major sections

Do not randomly use dozens of different spacing values.

---

# 8. Border Radius

Use:

- Small controls: `8px`
- Cards: `12px–16px`
- Large containers: `16px–20px`
- Pills/badges: `999px`

Avoid excessive rounded containers.

---

# 9. Global Layout

## Desktop

Main structure:

```text
Announcement / Utility Bar
        ↓
Main Navigation
        ↓
Optional Breadcrumb
        ↓
Page Content
        ↓
Footer
```

## Mobile

Use:

```text
Compact Header
Search
Content
Mobile-friendly controls
Optional fixed bottom navigation
Footer
```

The mobile experience must not simply be a shrunken desktop interface.

---

# 10. Header / Navigation

The header is one of the most important components.

## Desktop

Recommended structure:

```text
┌──────────────────────────────────────────────────────────────┐
│ Logo │ Categories │ Search...              │ Account │ Cart │
└──────────────────────────────────────────────────────────────┘
```

Include:

- Mr. Computers logo
- Category navigation
- Large search field
- Account
- Cart
- Optional wishlist
- Optional support/contact shortcut

Search should be visually prominent.

---

## Mobile

Use:

```text
┌─────────────────────────────┐
│ ☰  Logo              Cart   │
├─────────────────────────────┤
│ Search products...          │
└─────────────────────────────┘
```

Use Bootstrap Offcanvas for categories/menu.

Do not allow the mobile header to become extremely tall.

---

# 11. Search

Search should feel like a core feature.

Features:

- Product name search
- SKU/model search
- Category-aware search
- Search suggestions
- Recent searches if implemented
- Empty search state
- Loading state

Use debounce for live search.

Example:

```javascript
let searchTimeout;

searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);

    searchTimeout = setTimeout(() => {
        performSearch(searchInput.value);
    }, 300);
});
```

Do not send a request for every keystroke.

---

# 12. Homepage

The homepage should immediately communicate what Mr. Computers sells.

Recommended structure:

```text
Header
↓
Hero
↓
Popular Categories
↓
Featured Products
↓
Deals / Promotions
↓
Laptop Section
↓
Computer Components
↓
Custom PC Builder
↓
Refurbished Products
↓
Accessories / Oraimo / Mobile
↓
Why Choose Mr. Computers
↓
Trust / Delivery / COD
↓
Footer
```

---

# 13. Hero Section

Hero should be visually strong but not enormous.

Layout:

```text
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Build Better.                                         │
│  Choose Smarter.                                       │
│                                                         │
│  Computers, components, laptops and accessories.       │
│                                                         │
│  [ Shop Products ] [ Build a PC ]                      │
│                                                         │
│                              Product / PC Visual        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Requirements:

- Strong heading
- Short supporting text
- One primary CTA
- Optional secondary CTA
- Product/computer visual
- Responsive layout

Do not put five buttons in the hero.

---

# 14. Category Section

Use clean visual category cards.

Examples:

- Laptops
- Desktop Components
- Graphics Cards
- Processors
- RAM
- Storage
- Monitors
- Accessories
- Mobile Phones
- Routers
- Oraimo

Category card:

```text
┌───────────────────┐
│                   │
│     Product       │
│      Image        │
│                   │
│   Graphics Card   │
│   24 Products     │
└───────────────────┘
```

Keep cards visually consistent.

---

# 15. Product Card

This is one of the most important reusable components.

Structure:

```text
┌─────────────────────────┐
│ Badge                   │
│                         │
│      Product Image      │
│                         │
├─────────────────────────┤
│ Brand                   │
│ Product Name            │
│ ★★★★★ (24)              │
│                         │
│ ৳ 89,999                │
│ ৳ 94,999                │
│                         │
│ [ Add to Cart ]         │
└─────────────────────────┘
```

Include where appropriate:

- Product image
- Brand
- Product name
- Rating
- Current price
- Previous price
- Discount
- Stock state
- Quick action
- Add to cart

Do not overload the card with every specification.

---

# 16. Product Card States

Every product card must support:

- Default
- Hover
- Focus
- Loading
- In stock
- Low stock
- Out of stock
- Discounted
- Refurbished
- New
- Featured

Example badges:

```text
NEW
SALE
REFURBISHED
OUT OF STOCK
LOW STOCK
```

Use badges sparingly.

---

# 17. Product Listing Page

Structure:

```text
Breadcrumb
↓
Page title + result count
↓
Filter / Sort toolbar
↓
Product grid
↓
Pagination
```

Desktop:

```text
┌──────────────┬──────────────────────────────────────┐
│ Filters      │ Sort: Recommended   48 Products      │
│              │                                      │
│ Brand        │ [Product] [Product] [Product]       │
│ Price        │ [Product] [Product] [Product]       │
│ Category     │ [Product] [Product] [Product]       │
│ Availability │                                      │
└──────────────┴──────────────────────────────────────┘
```

Mobile:

- Filters open in Offcanvas
- Sort remains easily accessible
- Product grid becomes 2 columns where appropriate
- Use 1 column on very narrow screens if necessary

---

# 18. Filters

Possible filters:

- Category
- Brand
- Price range
- Availability
- Condition
- Rating
- Product-specific attributes

Do not show irrelevant filters for every category.

For example:

GPU page may show:

- VRAM
- Chipset
- Manufacturer
- Interface

Laptop page may show:

- RAM
- Storage
- Processor
- Display size
- GPU

---

# 19. Product Detail Page

Recommended layout:

```text
Breadcrumb

┌──────────────────────┬────────────────────────────────┐
│                      │ Brand                          │
│   Product Gallery   │ Product Name                   │
│                      │ Rating                         │
│                      │ Price                          │
│                      │ Discount                       │
│                      │ Stock                          │
│                      │ Quantity                       │
│                      │ [ Add to Cart ]                │
│                      │ [ Buy Now ]                    │
└──────────────────────┴────────────────────────────────┘

Product Information
Specifications
Delivery Information
Related Products
```

---

# 20. Product Gallery

Use:

- Main image
- Thumbnail images
- Active thumbnail state
- Zoom/lightbox where useful
- Keyboard-accessible controls

Images must maintain consistent aspect ratios.

Do not stretch images.

Use:

```html
<img
    src="..."
    alt="..."
    width="..."
    height="..."
    loading="lazy">
```

The primary product image may use eager loading if it is above the fold.

---

# 21. Pricing

Show:

```text
৳ 89,999
৳ 94,999
Save ৳ 5,000
```

Do not make the old price visually stronger than the current price.

Currency formatting must be consistent across the entire site.

---

# 22. Stock States

Use clear messaging:

### In stock

```text
✓ In Stock
```

### Low stock

```text
Only a few left
```

Only show this if the backend confirms it.

### Out of stock

```text
Out of Stock
```

Disable purchasing controls when appropriate.

Do not rely on frontend JavaScript to determine stock validity.

---

# 23. Product Specifications

Use a readable specification table.

Example:

```text
Processor        Intel Core i7
Generation       14th Gen
RAM              16 GB
Storage          1 TB SSD
Graphics         RTX 4060
Warranty         1 Year
```

On mobile, convert large tables into:

- Stacked rows
- Accordions
- Horizontally scrollable tables when unavoidable

---

# 24. Cart Page

Cart should be extremely clear.

Structure:

```text
Your Cart

┌────────────────────────────────────┬───────────────┐
│ Product / Quantity                 │ Price         │
│                                    │               │
│ Product                            │ ৳ XX          │
│ Quantity controls                  │               │
│ Remove                             │               │
└────────────────────────────────────┴───────────────┘

Coupon Code
[ Apply ]

Order Summary
Subtotal
Discount
Delivery
Total

[ Proceed to Checkout ]
```

---

# 25. Quantity Controls

Use:

```text
[ − ]  2  [ + ]
```

Requirements:

- Keyboard accessible
- Disabled state
- Loading state
- Prevent negative values
- Backend must validate final quantity

Do not trust browser values.

---

# 26. Checkout

Guest checkout is required.

The user must NOT be forced to create an account.

Recommended flow:

```text
Contact Information
↓
Delivery Information
↓
Order Items
↓
Coupon
↓
Payment Method
↓
Order Summary
↓
Place Order
```

Payment method:

```text
● Cash on Delivery
```

Optional:

```text
Create an account after placing the order
```

Do not make registration a blocker.

---

# 27. Checkout Form UX

Use:

- Clear labels
- Helpful placeholders
- Inline validation
- Required indicators
- Error messages directly below fields
- Mobile-friendly inputs

Example:

```text
Phone Number *
[ 01XXXXXXXXX ]

Please enter a valid Bangladeshi phone number.
```

Do not use placeholder text as the only label.

---

# 28. Order Confirmation

After successful order:

```text
✓ Order Placed Successfully

Thank you for your order.

Order #MC-123456

We'll contact you shortly to confirm your order.

[ Continue Shopping ]
[ View Order ]
```

Make the order number prominent.

---

# 29. Authentication

Optional account system.

Pages:

- Login
- Registration
- Forgot password
- Reset password

Do not force login during checkout.

Allow users to create an account later if supported.

---

# 30. Customer Account

Dashboard should include:

```text
Overview
Orders
Order Details
Profile
Addresses
Wishlist
Account Settings
Logout
```

Keep it much simpler than the staff dashboard.

---

# 31. Wishlist

Wishlist card should support:

- Product image
- Name
- Price
- Stock state
- Add to cart
- Remove

If product becomes unavailable, clearly communicate it.

---

# 32. Custom PC Builder

The PC builder should feel like a guided tool.

Example:

```text
1. CPU
2. Motherboard
3. RAM
4. GPU
5. Storage
6. PSU
7. Case
8. Cooling
```

Show:

```text
Build Progress
████████░░ 70%

Estimated Total
৳ 185,000

Compatibility
✓ CPU compatible
✓ RAM compatible
⚠ PSU recommendation
```

The UI should make compatibility understandable.

Avoid overwhelming users with raw technical information.

---

# 33. Dashboard Design

The staff dashboard should feel like a professional business application.

Recommended structure:

```text
┌──────────────┬──────────────────────────────────────────┐
│ Sidebar      │ Top Bar                                  │
│              ├──────────────────────────────────────────┤
│ Overview     │                                          │
│ Orders       │ Dashboard                                │
│ Products     │                                          │
│ Inventory    │ KPI Cards                                │
│ Customers    │                                          │
│ Coupons      │ Charts / Activity                        │
│ Categories   │                                          │
│ Media        │ Tables                                   │
│ Content      │                                          │
│ Reports      │                                          │
│ Settings     │                                          │
└──────────────┴──────────────────────────────────────────┘
```

---

# 34. Dashboard Sidebar

Navigation:

- Dashboard
- Orders
- Products
- Categories
- Inventory
- Customers
- Coupons
- Media
- Content
- Reports
- Settings

Use icons consistently.

Active item should have:

- Accent background
- Accent icon
- Strong text

Do not use a different color for every menu item.

---

# 35. Dashboard KPI Cards

Examples:

```text
┌────────────────────┐
│ Total Sales        │
│ ৳ 1,245,000        │
│ ↑ 12.4%            │
└────────────────────┘
```

Possible KPIs:

- Today's Sales
- Monthly Sales
- New Orders
- Pending Orders
- Low Stock Products
- Customers
- Products

Do not show meaningless metrics just to fill space.

---

# 36. Dashboard Charts

Use charts only when they help decision-making.

Useful:

- Sales over time
- Orders over time
- Top categories
- Top products
- Order status distribution

Avoid:

- 3D charts
- Excessive colors
- Decorative charts

Charts must have accessible text summaries where practical.

---

# 37. Orders Dashboard

Table:

```text
Order ID
Customer
Date
Items
Total
Payment
Status
Actions
```

Statuses should have consistent badges:

- Pending
- Confirmed
- Processing
- Shipped
- Delivered
- Cancelled

Use confirmation dialogs for destructive actions.

---

# 38. Order Detail

Structure:

```text
Order Header
Customer Information
Delivery Information
Products
Payment
Order Timeline
Internal Notes
Actions
```

Primary action should be obvious.

Example:

```text
[ Confirm Order ]
[ Mark as Processing ]
[ Mark as Delivered ]
```

Only show actions appropriate to the current order state.

---

# 39. Product Management

Product table should support:

- Search
- Filter
- Sort
- Pagination
- Bulk selection
- Edit
- View
- Archive/deactivate

Columns should not become excessively wide.

Use responsive tables or mobile cards.

---

# 40. Product Form

Group fields logically.

### Basic Information

- Product name
- Brand
- Category
- SKU
- Condition
- Description

### Pricing

- Selling price
- Previous price
- Cost if appropriate for staff
- Tax/other pricing information if applicable

### Inventory

- Stock quantity
- Low stock threshold
- Availability

### Media

- Main image
- Gallery
- Alt text
- Ordering

### Specifications

Use structured fields where appropriate.

Do not make the owner edit raw JSON unless absolutely necessary.

---

# 41. Inventory UI

Inventory should clearly communicate:

```text
Healthy
Low Stock
Out of Stock
Archived
```

Use visual hierarchy rather than huge warning colors.

Example:

```text
RTX 4060
Stock: 7
Status: Healthy
```

---

# 42. Coupon Management

Dashboard UI:

```text
Coupons

[ + Create Coupon ]

Code
Type
Discount
Applicable Products
Minimum Order
Start
Expiry
Status
Actions
```

Coupon form should clearly distinguish:

- Percentage discount
- Fixed discount
- Product-specific coupon
- Category-specific coupon
- Minimum cart amount
- Maximum discount if applicable
- Start/end date
- Usage limits
- Active/inactive state

---

# 43. Media Management

The media interface should be designed for many product photos.

Features:

- Grid/list view
- Search
- Filter
- Preview
- Alt text
- Usage/reference information
- Upload
- Archive
- Safe deletion confirmation

Never provide a destructive "delete everything unused" button without strong confirmation.

Frontend must not assume that an image is safe to delete merely because a product has zero stock.

---

# 44. Content Management

Owner-manageable frontend content may include:

- Homepage hero
- Promotional banners
- Featured products
- Categories
- Announcements
- Footer information
- Contact information
- Store policies

Use simple forms and previews.

The owner should not need to understand HTML.

---

# 45. Settings UI

Group settings:

```text
Store
Orders
Delivery
Payments
Coupons
Notifications
Appearance
SEO
Security
```

Do not place dozens of unrelated settings on one page.

Use tabs or grouped sections.

---

# 46. Reusable Components

Build reusable components for:

- Navbar
- Footer
- Breadcrumb
- Search bar
- Product card
- Category card
- Buttons
- Badges
- Alerts
- Toasts
- Modals
- Confirmation dialogs
- Form controls
- Tables
- Pagination
- Tabs
- Accordions
- Dropdowns
- Offcanvas
- Skeleton loaders
- Empty states
- Error states
- Loading states

Do not duplicate identical markup across pages.

---

# 47. Buttons

Primary:

```html
<button class="btn btn-primary">
    Add to Cart
</button>
```

Secondary:

```html
<button class="btn btn-outline-primary">
    View Details
</button>
```

Danger:

```html
<button class="btn btn-danger">
    Delete
</button>
```

Use destructive buttons carefully.

Do not use red for ordinary actions.

---

# 48. Button States

Every interactive button should support:

- Default
- Hover
- Focus
- Active
- Disabled
- Loading

Loading example:

```text
[ Processing... ]
```

Do not allow multiple clicks while an action is processing.

---

# 49. Forms

Forms must have:

- Visible labels
- Required indicators
- Helpful errors
- Focus state
- Disabled state
- Loading state
- Success feedback

Use semantic HTML.

Example:

```html
<label for="phone" class="form-label">
    Phone Number
</label>

<input
    id="phone"
    name="phone"
    type="tel"
    class="form-control"
    autocomplete="tel"
    required>
```

---

# 50. Modals

Use modals for:

- Confirmation
- Quick view
- Small forms
- Important warnings

Do not put long complicated workflows inside a modal.

Use a full page for complex editing.

---

# 51. Toast Notifications

Use toasts for short-lived feedback:

```text
✓ Added to cart
✓ Coupon applied
✓ Product updated
✕ Unable to save changes
```

Do not use toasts as the only place for critical error information.

---

# 52. Empty States

Example:

```text
No products found

Try changing your filters or search terms.

[ Clear Filters ]
```

Empty states should always tell users what they can do next.

---

# 53. Loading States

Use skeleton loaders for:

- Product grids
- Dashboard cards
- Tables
- Product details

Example:

```text
████████████
████████
██████
```

Avoid showing blank screens during normal loading.

---

# 54. Error States

Example:

```text
Something went wrong

We couldn't load this information.

[ Try Again ]
```

Do not expose raw server errors, stack traces, SQL errors, or internal information to users.

---

# 55. Responsive Design

Use Bootstrap breakpoints:

```text
xs  < 576px
sm  ≥ 576px
md  ≥ 768px
lg  ≥ 992px
xl  ≥ 1200px
xxl ≥ 1400px
```

Build mobile-first.

---

# 56. Mobile Rules

On mobile:

- Reduce navigation complexity
- Use Offcanvas for large menus
- Stack forms
- Use 2-column product grids when readable
- Convert large tables into cards or scrollable regions
- Keep buttons touch-friendly
- Keep important CTAs visible
- Avoid tiny text
- Avoid horizontal overflow

Minimum comfortable touch target:

Approximately 44×44px.

---

# 57. Dashboard Mobile Behavior

The dashboard must remain usable on phones/tablets.

Desktop:

```text
Sidebar + Content
```

Mobile:

```text
Top Bar
↓
Menu Button
↓
Offcanvas Sidebar
↓
Content
```

Do not squeeze a desktop table into a tiny screen.

---

# 58. Accessibility

Target WCAG AA-level usability.

Requirements:

- Semantic HTML
- Proper heading hierarchy
- Visible focus states
- Keyboard navigation
- Form labels
- Accessible buttons
- Meaningful alt text
- Sufficient color contrast
- Do not rely on color alone
- Respect `prefers-reduced-motion`
- Accessible modal behavior
- Accessible dropdowns
- Accessible error messages

Example:

Bad:

```html
<div onclick="deleteItem()">Delete</div>
```

Good:

```html
<button type="button" class="btn btn-danger">
    Delete
</button>
```

---

# 59. Motion and Animation

Animations should be subtle.

Use approximately:

```css
transition: 180ms ease;
```

Good:

- Button hover
- Card elevation
- Dropdown
- Modal
- Toast
- Image hover

Avoid:

- Constant floating animations
- Excessive parallax
- Large page transitions
- Bouncing elements
- Animation that delays interaction

Respect:

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

# 60. Image Rules

Product images are important and numerous.

Frontend rules:

- Never stretch images
- Use consistent containers
- Use `object-fit: contain` for product photography
- Use `object-fit: cover` only where appropriate
- Lazy-load below-the-fold images
- Provide width/height where possible
- Use modern image formats where supported
- Do not embed huge base64 images in HTML
- Use responsive image sizes where available

Example:

```css
.product-card__image {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: contain;
}
```

The frontend must not implement storage cleanup logic.

Image lifecycle/deletion belongs to backend/storage management.

---

# 61. Performance

Requirements:

- Minimize unnecessary JavaScript
- Defer non-critical scripts
- Lazy-load below-fold images
- Avoid huge unoptimized images
- Avoid duplicate CSS
- Avoid loading unused libraries
- Use pagination
- Avoid rendering hundreds of products simultaneously
- Use skeleton loading where appropriate
- Avoid layout shift

Do not load every product image on a page if pagination can solve the problem.

---

# 62. Frontend Security Rules

The frontend is not a security boundary.

Never trust:

- Product price
- Discount
- Coupon result
- Stock quantity
- Cart total
- Shipping cost
- Order total

The backend must recalculate and validate all important values.

Frontend responsibilities:

- CSRF support for Django forms/AJAX
- Safe rendering of user-provided content
- Avoid unsafe `innerHTML` where unnecessary
- Do not expose secrets
- Do not put API keys in JavaScript
- Do not store sensitive data in localStorage
- Do not expose internal server errors

---

# 63. Django Integration

The frontend should work naturally with Django templates.

Recommended:

```text
templates/
├── base.html
├── partials/
│   ├── navbar.html
│   ├── footer.html
│   ├── product_card.html
│   ├── breadcrumbs.html
│   ├── alerts.html
│   └── pagination.html
│
├── storefront/
├── products/
├── cart/
├── checkout/
├── account/
└── dashboard/
```

Static files:

```text
static/
├── css/
│   ├── app.css
│   ├── components/
│   └── pages/
│
├── js/
│   ├── app.js
│   ├── components/
│   └── pages/
│
└── images/
```

Keep page-specific CSS/JS separate when it becomes substantial.

---

# 64. CSS Architecture

Recommended:

```text
css/
├── app.css
├── base/
├── components/
├── layout/
├── pages/
└── utilities/
```

Do not create one 5,000-line CSS file if the project grows.

Use clear component naming.

Example:

```text
.product-card
.product-card__image
.product-card__title
.product-card__price
.product-card__actions
```

Avoid deeply nested selectors.

---

# 65. JavaScript Architecture

Recommended:

```text
js/
├── app.js
├── components/
│   ├── cart.js
│   ├── search.js
│   ├── toast.js
│   ├── modal.js
│   └── filters.js
│
└── pages/
    ├── product-detail.js
    ├── checkout.js
    ├── dashboard.js
    └── product-form.js
```

Use modules where appropriate.

Keep responsibilities separated.

---

# 66. Data Attributes

Use `data-*` attributes for frontend hooks.

Example:

```html
<button
    class="js-add-to-cart"
    data-product-id="{{ product.id }}">
    Add to Cart
</button>
```

Avoid coupling JavaScript to fragile CSS selectors.

Bad:

```javascript
document.querySelector(".blue-button:nth-child(3)")
```

Good:

```javascript
document.querySelector("[data-product-id]")
```

---

# 67. AJAX / Fetch

When JavaScript communicates with Django:

- Use `fetch`
- Handle loading
- Handle success
- Handle validation errors
- Handle server errors
- Prevent duplicate requests
- Respect CSRF
- Update only the necessary UI

Never assume a successful HTTP request means the business operation succeeded.

Always inspect the response.

---

# 68. Search Debouncing

Search requests must be debounced.

Suggested delay:

```text
250–350ms
```

Cancel stale requests where appropriate using `AbortController`.

---

# 69. Confirmation Dialogs

For destructive operations:

```text
Delete Product?

This action may affect product availability and associated media.

[ Cancel ] [ Delete ]
```

For irreversible actions, explain the consequence clearly.

Do not use browser `alert()` for important application workflows.

---

# 70. Breadcrumbs

Use breadcrumbs on deeper pages:

```text
Home / Laptops / Gaming Laptops / Product Name
```

Do not use breadcrumbs on every tiny dashboard interaction if they add no value.

---

# 71. Footer

Footer should contain:

### Store

- About
- Contact
- Store information

### Customer Support

- Delivery
- Returns
- Warranty
- FAQ

### Categories

- Laptops
- Components
- Accessories
- Mobile

### Legal

- Privacy
- Terms
- Refund/Return Policy

### Contact

- Phone
- Email
- Address
- Social links

Keep the footer structured, not enormous.

---

# 72. SEO-Friendly Frontend

Use:

- One meaningful H1 per page
- Semantic HTML
- Descriptive titles
- Meta descriptions
- Proper image alt text
- Canonical URLs where appropriate
- Crawlable product/category links

Do not hide important product information behind JavaScript unnecessarily.

---

# 73. Product Image Alt Text

Bad:

```text
image1.jpg
```

Good:

```text
ASUS GeForce RTX 4060 8GB graphics card
```

Alt text should describe the image's purpose.

---

# 74. Dashboard Tables

Tables should support:

- Sorting
- Filtering
- Pagination
- Row actions
- Selection where appropriate

Avoid 15+ columns in the default view.

Use a details page for deeper information.

---

# 75. Bulk Actions

Where useful:

```text
☐ Select All

[ Archive Selected ]
[ Change Status ]
[ Export ]
```

Destructive bulk actions require confirmation.

Do not make bulk deletion easy to trigger accidentally.

---

# 76. Notification System

Use a consistent feedback system.

Success:

```text
✓ Product saved successfully.
```

Warning:

```text
⚠ Some fields need attention.
```

Error:

```text
✕ We couldn't save the product.
```

Info:

```text
i This product is currently out of stock.
```

---

# 77. Design for Real Business Data

The interface must remain usable when:

- There are 10 products
- There are 1,000 products
- There are 10,000+ products
- Product names are very long
- Images fail to load
- Prices are large
- Orders have many items
- Customers have long names
- Tables contain large datasets

Do not design only for perfect demo data.

---

# 78. Long Product Names

Product titles may be long.

Cards should use controlled line clamping where appropriate.

Example:

```css
.product-card__title {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
```

Product detail pages should show the full name.

---

# 79. Failed Images

Always have a graceful fallback.

If an image fails:

```text
Image unavailable
```

or use a neutral placeholder.

Do not leave broken image icons throughout the site.

---

# 80. No-Result Search

Example:

```text
No products found for "RTX 9999"

Try:

• Checking the spelling
• Using fewer keywords
• Browsing a category

[ Browse All Products ]
```

---

# 81. Dashboard Empty State

If the store is new:

```text
No orders yet

Orders will appear here when customers place them.

[ View Products ]
```

Do not show fake numbers.

---

# 82. Responsive Product Grid

Recommended:

```text
xs: 1–2 columns
sm: 2 columns
md: 3 columns
lg: 4 columns
xl: 4–5 columns depending on container width
```

Prioritize readability over maximum density.

---

# 83. Container Width

Use Bootstrap containers.

Do not make content span the entire screen on very large monitors.

Dashboard may use a wider container.

Product pages should retain comfortable reading width.

---

# 84. Visual Hierarchy

Every page must answer:

1. Where am I?
2. What is this page about?
3. What is the primary action?
4. What information matters most?
5. What should I do next?

If everything looks equally important, the design has failed.

---

# 85. Avoid These Design Mistakes

Never:

- Use five different button styles for the same action
- Use random colors
- Use random border radii
- Mix multiple icon libraries
- Use giant text everywhere
- Use excessive gradients
- Use excessive shadows
- Put too many cards inside cards
- Make every section full-screen
- Create horizontal scrolling accidentally
- Use tiny text on mobile
- Hide important actions
- Force account creation during checkout
- Put business-critical information only inside hover states

---

# 86. Do Not Overuse Bootstrap

Bootstrap is the foundation, not the final visual identity.

Use Bootstrap for:

- Grid
- Responsive utilities
- Forms
- Buttons
- Modal
- Offcanvas
- Dropdown
- Accordion
- Container
- Spacing utilities

Customize the visual layer with project CSS.

The result must not look like an untouched Bootstrap demo.

---

# 87. Page Inventory

The frontend should be prepared for these pages.

## Storefront

- Home
- All Products
- Category
- Search Results
- Product Detail
- Cart
- Checkout
- Order Success
- About
- Contact
- FAQ
- Delivery Policy
- Return Policy
- Warranty
- Privacy Policy
- Terms

## Customer

- Login
- Register
- Forgot Password
- Account Dashboard
- Orders
- Order Detail
- Profile
- Addresses
- Wishlist
- Settings

## PC Builder

- Builder
- Component Selection
- Build Summary

## Dashboard

- Overview
- Orders
- Order Detail
- Products
- Product Create
- Product Edit
- Categories
- Inventory
- Customers
- Coupons
- Media
- Content
- Reports
- Settings

---

# 88. Frontend File Organization

Recommended project structure:

```text
project/
│
├── templates/
│   ├── base.html
│   │
│   ├── partials/
│   │   ├── navbar.html
│   │   ├── footer.html
│   │   ├── breadcrumbs.html
│   │   ├── product_card.html
│   │   ├── category_card.html
│   │   ├── pagination.html
│   │   ├── alerts.html
│   │   └── empty_state.html
│   │
│   ├── storefront/
│   ├── products/
│   ├── cart/
│   ├── checkout/
│   ├── account/
│   └── dashboard/
│
└── static/
    ├── css/
    │   ├── app.css
    │   ├── components/
    │   ├── layout/
    │   └── pages/
    │
    ├── js/
    │   ├── app.js
    │   ├── components/
    │   └── pages/
    │
    └── images/
```

Adapt this structure to the actual Django project instead of blindly creating duplicate directories.

---

# 89. Copilot Implementation Rules

GitHub Copilot must follow these rules when implementing this frontend.

## Rule 1

Do not rewrite backend logic.

## Rule 2

Do not invent Django models.

## Rule 3

Do not invent API endpoints unless explicitly requested.

## Rule 4

Use existing Django context variables and URLs when they already exist.

## Rule 5

If backend data is not available yet, use clearly marked mock/placeholder data.

## Rule 6

Never hard-code production prices, stock, coupon values, or order totals.

## Rule 7

Do not put JavaScript directly into HTML unless it is a tiny initialization/configuration value that genuinely needs to exist there.

## Rule 8

Do not create duplicate components.

## Rule 9

Reuse existing components.

## Rule 10

Keep the UI responsive from the beginning.

## Rule 11

Do not sacrifice accessibility for appearance.

## Rule 12

Do not sacrifice usability for visual effects.

---

# 90. Copilot Development Order

Implement in this order:

### Phase 1 — Design Foundation

1. CSS variables
2. Typography
3. Global spacing
4. Buttons
5. Forms
6. Cards
7. Badges
8. Alerts
9. Modal
10. Toast
11. Responsive utilities

### Phase 2 — Global Layout

1. Base template
2. Navbar
3. Search
4. Footer
5. Breadcrumbs

### Phase 3 — Storefront

1. Homepage
2. Category page
3. Product listing
4. Product card
5. Product detail

### Phase 4 — Shopping

1. Cart
2. Coupon UI
3. Checkout
4. Order confirmation

### Phase 5 — Customer

1. Login
2. Registration
3. Account
4. Orders
5. Wishlist

### Phase 6 — PC Builder

1. Component selector
2. Build summary
3. Compatibility UI
4. Price summary

### Phase 7 — Dashboard

1. Layout
2. Overview
3. Orders
4. Products
5. Inventory
6. Coupons
7. Customers
8. Media
9. Content
10. Reports
11. Settings

### Phase 8 — Polish

1. Accessibility
2. Responsive testing
3. Loading states
4. Empty states
5. Error states
6. Performance
7. Cross-browser testing
8. Visual consistency

---

# 91. Acceptance Checklist

Before considering the frontend complete:

## Visual

- [ ] Consistent design system
- [ ] Consistent typography
- [ ] Consistent colors
- [ ] Consistent spacing
- [ ] Consistent buttons
- [ ] Consistent cards
- [ ] No random visual styles

## Storefront

- [ ] Homepage works
- [ ] Category page works
- [ ] Search works
- [ ] Product listing works
- [ ] Product detail works
- [ ] Cart works
- [ ] Checkout works
- [ ] Order confirmation works

## Dashboard

- [ ] Dashboard responsive
- [ ] Sidebar works
- [ ] Orders UI works
- [ ] Product management UI works
- [ ] Inventory UI works
- [ ] Coupon UI works
- [ ] Media UI works
- [ ] Content UI works
- [ ] Settings UI works

## Responsive

- [ ] Mobile
- [ ] Tablet
- [ ] Laptop
- [ ] Desktop
- [ ] Large desktop

## Accessibility

- [ ] Keyboard navigation
- [ ] Visible focus
- [ ] Labels
- [ ] Alt text
- [ ] Contrast
- [ ] Reduced motion
- [ ] Accessible buttons

## UX States

- [ ] Loading
- [ ] Empty
- [ ] Error
- [ ] Success
- [ ] Disabled
- [ ] Out of stock
- [ ] Low stock
- [ ] Form validation

## Performance

- [ ] Images optimized
- [ ] Lazy loading
- [ ] No unnecessary libraries
- [ ] No huge JavaScript bundle
- [ ] No excessive DOM rendering
- [ ] No layout-shift-heavy components

---

# 92. Final Design Direction

The final Mr. Computers frontend should feel like:

> **A modern, trustworthy technology retailer with the simplicity of a premium e-commerce store and the operational clarity of a professional business dashboard.**

The customer experience should be:

```text
Discover
   ↓
Understand
   ↓
Compare
   ↓
Choose
   ↓
Buy
   ↓
Track
```

The owner experience should be:

```text
See
   ↓
Understand
   ↓
Manage
   ↓
Act
```

Every interface decision should support those two journeys.

---

# 93. Final Instruction to GitHub Copilot

When implementing this specification:

> Build the frontend as a cohesive design system, not as a collection of unrelated pages.

> Reuse components aggressively, keep HTML semantic, keep CSS maintainable, keep JavaScript modular, and make every page responsive.

> The website must look custom-designed rather than like a default Bootstrap template.

> Prioritize usability, accessibility, performance, consistency and maintainability over visual gimmicks.

> Never invent backend behavior. Use placeholders where backend integration is not yet available.

> Never trust client-side values for prices, stock, discounts, coupons, shipping or order totals.

> Keep the frontend prepared for a large catalog, many product images, large order history and future business growth.

> If a visual decision conflicts with usability, choose usability.

> If a shortcut creates technical debt, do not take the shortcut merely to make the page look finished.

**This document is the frontend source of truth for Mr. Computers.**
