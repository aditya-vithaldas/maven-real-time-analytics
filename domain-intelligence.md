# Domain intelligence — Meridian commerce

This is the domain knowledge for a fresh build, grounded in the cloud dataset. Read `principles.md` for response behavior and `data/schema.json` for exact columns, types, table grains, and rules. This file describes supported interpretation; it does not assert that an application already implements it.

## Dataset and time

- Synthetic e-commerce data, USD, 10 million rows across 12 tables.
- Trading dates: 2025-09-30 through 2026-09-29, inclusive.
- Resolve relative dates using the latest dataset date unless the user explicitly chooses another anchor. Record that anchor in the answer context. With the default anchor, yesterday means 2026-09-28; last seven available days means 2026-09-23 through 2026-09-29.
- Customer signup dates precede this window and delivery dates can extend past it.
- One year supports within-year comparisons, but cannot establish recurring annual seasonality.

## Priorities and metric definitions

1. Conversion: buyers or orders relative to eligible visitors/sessions, with the exact numerator and denominator stated. The existing demo definition is placed-order sessions divided by all sessions; this is session conversion, not distinct visitor-to-buyer conversion.
2. Traffic: session count; analyze traffic_source, device, region via customer, and time. Order channel and traffic_source are different dimensions.
3. Revenue/GMV: default to completed-order net revenue. If a user requests GMV, state whether they mean net completed revenue or gross booked value; do not silently interchange them.
4. ASP: completed line-item net revenue divided by completed units (SUM(quantity)). AOV is completed-order revenue divided by completed-order count.
5. Loyalty/frequency: purchases per customer per month, active buyer frequency, repeat purchase share, and units/items per buyer with explicit denominators.
6. Funnel/retention: only compute stages and cohorts actually supported. Report missing measurement before promising an insight.

Orders are transactions, order_items are line-item rows, and units are quantities. Every order has exactly three line-item rows in this demo; that ratio cannot explain a change. Signup-based new-user retention in the trading year is not supported because customer signups are in 2024. First observed purchase within this window is not necessarily the customer's first lifetime purchase.

## Correct joins and aggregation

- Customer and region sales: sum orders.net_amount on completed orders. Join customers and regions; do not join line items.
- Category/product sales: sum order_items.net_amount joined to completed orders, products, and categories.
- A join to order_items repeats each order total three times. Never sum orders.net_amount after this join.
- Payment amount includes tax and shipping and is not sales revenue.
- Display entity names, but group by both ID and name because names need not be unique.
- Reconcile additive breakdowns to the corresponding total before presenting them.

## Evidence and missing data

The dataset has traffic_source and order channel, but does not provide the complete search → gallery → cart → checkout → payment funnel, session timestamps/boundaries, UTM campaign fields, seller attribution, acquisition spend, or inventory availability. Do not claim those metrics are available. Customer-linked sessions support some observed frequency measures; they do not establish browser-level stickiness or anonymous user identity.

business_events has 60 modeled scenarios. market_snapshots has 5,840 modeled daily competitor/category observations. They provide context, never proof of cause or live market intelligence. Say “overlaps” or “coincides with”; separately quantify the measured contribution and label explanatory hypotheses.

## Source-of-truth query rules

The following rules are copied from the downloaded cloud schema:

- Category, product and customer names are fictional human-readable demo labels. Always display their name columns, not numeric IDs or invented aliases. Names are not guaranteed unique: group by the entity ID and name for rankings, and use IDs for joins. Category names and departments are listed in categoryCatalog.
- All records, business events, and market snapshots are synthetic, reproducible demo data from 2025-09-30 through 2026-09-29; all monetary amounts are USD. Never present synthetic competitor observations as live facts.
- Table grains: orders/payments one row per order; order_items exactly three rows per order; shipments one row for each of 850000 orders; sessions one row per session; business_events one row per deliberately embedded scenario; market_snapshots one row per date, competitor, and category group.
- Business events provide known scenario context, not proof that an external event caused a measured change. Use cautious language such as coincides with or overlaps.
- Market snapshots are synthetic benchmark samples inspired by public European commerce category structures. sampled_price_index is currency-free, promotion_depth_pct is a modeled observation, products_sampled is the sample size, and headline_callout is modeled page copy.
- Sales/revenue means SUM(orders.net_amount) WHERE orders.status='completed'. Excludes tax/shipping and cancelled/returned orders. Gross booked sales includes all statuses only if explicitly requested.
- Orders count means COUNT(*) FROM orders, qualified by status when requested. AOV = completed revenue / completed order count.
- Customers.customer_id links orders.customer_id and sessions.customer_id. customers.region_id links regions.region_id. order_items.order_id, payments.order_id and shipments.order_id link orders.order_id. products.product_id links order_items.product_id; products.category_id links categories.category_id.
- Never sum orders.net_amount after joining to order_items; it repeats three times. For product/category revenue sum order_items.net_amount joined to orders filtered completed.
- Payment amount includes net+tax+shipping, so it is not sales revenue. Payment status captured/void/refunded corresponds to completed/cancelled/returned orders.
- Traffic = COUNT(*) FROM sessions. Conversion = count(sessions.order_id) / count(*) * 100; it includes placed orders of all statuses. For completed conversion join orders and explicitly filter status.
- For a single date return one aggregate and display number unless a breakdown is requested. For temporal questions default to daily line chart; use monthly grouping for full-year requests.
- Date filters on orders use order_date; sessions use session_date. Latest demo date is 2026-09-29. Relative last-7-days means 2026-09-23 through 2026-09-29 inclusive.
- Read-only SELECT/CTE queries only. Return columns label (text), value (numeric), optional secondary (numeric). Charts <= 1000 groups. No external files, extensions, system tables, or network operations.
