# Field and query guide

Read the raw structure for exact types. All names/emails and competitor observations are synthetic. Currency is USD.

## Tables and fields

- regions: region_id identifies a region; region_name is the display label.
- categories: category_id identifies a category; category_name is its label; department is its broader grouping.
- products: product_id identifies a product; product_name is its label; category_id links categories; list_price is the nominal per-unit price; unit_cost is the modeled per-unit cost.
- customers: customer_id identifies a customer; customer_name is the display label; email is fictional contact data; region_id links regions; signup_date is registration date; segment is consumer/business/loyalty.
- calendar: date is the trading day; calendar_year, month_number, day_number, weekday, quarter_number are date components.
- orders: order_id identifies a transaction; customer_id links customers; order_date is the transaction date; channel is web/mobile_app/marketplace; status is completed/cancelled/returned; net_amount is the order net total excluding tax/shipping; tax_amount and shipping_amount are separate charges.
- order_items: order_item_id identifies a line; order_id links orders; product_id links products; quantity is units on the line; unit_price is nominal unit price; discount_amount is the modeled line adjustment; net_amount is the final line value. Each order has three lines. Adjustments can include campaign premiums, so discount_amount is not always positive.
- payments: payment_id identifies the payment; order_id links orders; payment_date is the payment date; payment_method is card/wallet/bank_transfer; status is captured/void/refunded; amount includes order net, tax, and shipping.
- shipments: shipment_id identifies the shipment; order_id links orders; shipped_date and delivered_date are fulfillment dates; carrier is a synthetic service label; status is delivered/cancelled/returned.
- sessions: session_id identifies a session; customer_id links customers; session_date is session day; traffic_source is organic/paid_search/social/email/direct; device is mobile/desktop/tablet; page_views counts visited pages; nullable order_id links the order placed in that session.
- business_events: event_id identifies modeled context; event_name and event_type describe it; start_date/end_date bound its window; market and scope describe its intended reach; expected_effect_pct is a modeled assumption, not a computed result; summary is the scenario explanation; source_type marks synthetic scenario.
- market_snapshots: snapshot_date is observation day; market is modeled geography; competitor and category_group are benchmark labels; homepage_promotion indicates a modeled promotion; sampled_price_index is a unitless price index; promotion_depth_pct is the modeled percentage promotion; products_sampled is sample count; headline_callout is modeled page copy; source_type marks synthetic benchmark sample.

## Links and grains

orders.customer_id → customers.customer_id → regions through customers.region_id.
order_items.order_id → orders.order_id; order_items.product_id → products.product_id → categories through products.category_id.
payments.order_id and shipments.order_id → orders.order_id.
sessions.customer_id → customers.customer_id; nullable sessions.order_id → orders.order_id.
Orders/payments are one row per order; items are three rows per order; sessions are one row per session. Group rankings by ID and label to retain distinct entities.

## Key query recipes

Sales: SUM(orders.net_amount) WHERE status='completed'. Exclude tax and shipping. AOV = completed sales / completed order count.
Category/product sales: SUM(order_items.net_amount), joined to completed orders and the product/category dimension. Never sum orders.net_amount after joining items; it repeats three times.
Units: SUM(order_items.quantity) joined to completed orders. Order count, line count, and unit count are different.
Traffic: COUNT(*) FROM sessions. Placed-order session conversion: 100.0*COUNT(order_id)/COUNT(*) FROM sessions. Completed conversion requires joining orders and filtering status explicitly.
ASP: completed line-item revenue / completed units.
Region/customer revenue: use orders joined to customers and regions; do not join items.
Relative dates: obtain MAX(order_date) or MAX(session_date) from the database first. Use this latest data date as the default anchor; yesterday is anchor minus one day. State the anchor if relevant.
Use order_date for order metrics and session_date for traffic. Compare periods of equal length or disclose day-count differences.

Example daily sales:
SELECT order_date AS label, SUM(net_amount) AS value FROM orders WHERE status='completed' AND order_date BETWEEN DATE '2026-09-23' AND DATE '2026-09-29' GROUP BY order_date ORDER BY order_date;

Example category sales:
SELECT c.category_name AS label, SUM(i.net_amount) AS value FROM order_items i JOIN orders o ON o.order_id=i.order_id JOIN products p ON p.product_id=i.product_id JOIN categories c ON c.category_id=p.category_id WHERE o.status='completed' GROUP BY c.category_id,c.category_name ORDER BY value DESC;

Business events and market observations provide context, not causal proof. Describe only database-returned results.
