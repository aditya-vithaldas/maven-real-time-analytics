# Database structure

regions(region_id INTEGER, region_name VARCHAR)
categories(category_id INTEGER, category_name VARCHAR, department VARCHAR)
products(product_id INTEGER, product_name VARCHAR, category_id INTEGER, list_price DECIMAL(12,2), unit_cost DECIMAL(12,2))
customers(customer_id INTEGER, customer_name VARCHAR, email VARCHAR, region_id INTEGER, signup_date DATE, segment VARCHAR)
calendar(date DATE, calendar_year INTEGER, month_number INTEGER, day_number INTEGER, weekday VARCHAR, quarter_number INTEGER)
order_items(order_item_id INTEGER, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price DECIMAL(12,2), discount_amount DECIMAL(12,2), net_amount DECIMAL(12,2))
orders(order_id INTEGER, customer_id INTEGER, order_date DATE, channel VARCHAR, status VARCHAR, net_amount DECIMAL(14,2), tax_amount DECIMAL(14,2), shipping_amount DECIMAL(12,2))
payments(payment_id INTEGER, order_id INTEGER, payment_date DATE, payment_method VARCHAR, status VARCHAR, amount DECIMAL(14,2))
shipments(shipment_id INTEGER, order_id INTEGER, shipped_date DATE, delivered_date DATE, carrier VARCHAR, status VARCHAR)
sessions(session_id INTEGER, customer_id INTEGER, session_date DATE, traffic_source VARCHAR, device VARCHAR, page_views INTEGER, order_id INTEGER)
business_events(event_id INTEGER, event_name VARCHAR, event_type VARCHAR, start_date DATE, end_date DATE, market VARCHAR, scope VARCHAR, expected_effect_pct DECIMAL(3,1), summary VARCHAR, source_type VARCHAR)
market_snapshots(snapshot_date DATE, market VARCHAR, competitor VARCHAR, category_group VARCHAR, homepage_promotion BOOLEAN, sampled_price_index DOUBLE, promotion_depth_pct DECIMAL(3,1), products_sampled INTEGER, headline_callout VARCHAR, source_type VARCHAR)
