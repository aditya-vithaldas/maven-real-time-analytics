# Meridian completed-text response comparison

Model: **gemini-3.8-flash**, text path. Five questions × four tabs = 20 requests.

Sequential HTTP requests; fresh conversation for every question and tab; elapsed wall time includes model and database tools. One attempt per question per tab. No retries.

## Response time in seconds

| Question | Runtime discovery | Schema only | Guided queries | Domain + workflows |
| --- | ---: | ---: | ---: | ---: |
| What were my sales on 29 September 2026? | 46.04 (failed) | 23.85 | 4.90 | 4.44 |
| Show daily sales for the last seven available days. | 66.28 (failed) | 33.87 | 5.92 | 5.89 |
| Which five categories had the highest sales on 29 September 2026? | 26.43 | 20.04 | 5.88 | 5.61 |
| How many units sold on 29 September 2026? | 40.87 | 19.10 | 5.18 | 4.52 |
| What was session conversion on 29 September 2026? | 9.59 | 3.99 | 8.43 | 11.85 |

| Tab | Average | Median | Range | Completed | Reference matches |
| --- | ---: | ---: | --- | ---: | ---: |
| Runtime discovery | 25.63s | 26.43s | 9.59–40.87s | 3/5 | 2/5 |
| Schema only | 20.17s | 20.04s | 3.99–33.87s | 5/5 | 3/5 |
| Guided queries | 6.06s | 5.88s | 4.90–8.43s | 5/5 | 5/5 |
| Domain + workflows | 6.46s | 5.61s | 4.44–11.85s | 5/5 | 5/5 |

This is one small sample, not a latency guarantee. Successful-request averages exclude failures, which remain visible in the question table. Reference matching compares the selected numeric query result with reference SQL executed directly on the database; it does not independently judge every sentence. Timings include the full response and database tools, not just the first token or voice audio.

## All responses

### Q1: What were my sales on 29 September 2026?

Reference result:

```json
[
  [
    "2026-09-29",
    1651201.07
  ]
]
```

**Runtime discovery — 46.04s — Request failed**

{"error": "The request failed. Check model access/quota or try a narrower question."}

**Schema only — 23.85s — Matches reference**

Completed sales on 29 September 2026 were $1,651,201.07 (or $1,873,705.86 in total order volume including cancelled and returned orders).

```sql
SELECT ROUND(SUM(net_amount), 2) AS sales
FROM orders
WHERE order_date = '2026-09-29'
  AND status = 'completed';
```

**Guided queries — 4.90s — Matches reference**

Completed sales on 29 September 2026 were $1,651,201.07. This reflects net order amounts for completed transactions, excluding taxes and shipping charges.

```sql
SELECT SUM(net_amount) AS "value" FROM orders WHERE status = 'completed' AND order_date = DATE '2026-09-29';
```

**Domain + workflows — 4.44s — Matches reference**

Completed sales on 29 September 2026 were $1,651,201.07. This excludes taxes, shipping, and cancelled or returned orders.

```sql
SELECT SUM(net_amount) AS value FROM orders WHERE status = 'completed' AND order_date = DATE '2026-09-29';
```

### Q2: Show daily sales for the last seven available days.

Reference result:

```json
[
  [
    "2026-09-23",
    1677816.87
  ],
  [
    "2026-09-24",
    1120252.94
  ],
  [
    "2026-09-25",
    1667650.36
  ],
  [
    "2026-09-26",
    1659961.5
  ],
  [
    "2026-09-27",
    1725209.0
  ],
  [
    "2026-09-28",
    1674392.48
  ],
  [
    "2026-09-29",
    1651201.07
  ]
]
```

**Runtime discovery — 66.28s — Request failed**

{"error": "The request failed. Check model access/quota or try a narrower question."}

**Schema only — 33.87s — Inspect result / assumptions**

Daily sales for the last seven available days (September 23 to September 29, 2026) ranged from $1.69M to $1.95M, peaking on September 27.

```sql
SELECT
    order_date,
    ROUND(SUM(net_amount), 2) AS daily_sales
FROM orders
WHERE order_date >= (SELECT MAX(order_date) - INTERVAL 6 DAY FROM orders)
GROUP BY order_date
ORDER BY order_date ASC;
```

**Guided queries — 5.92s — Matches reference**

Daily completed sales ranged from $1.12M to $1.73M across the last seven available days, anchored at September 29, 2026. Figures reflect completed order net revenue, excluding tax and shipping.

```sql
SELECT order_date AS label, SUM(net_amount) AS value FROM orders WHERE status = 'completed' AND order_date BETWEEN DATE '2026-09-23' AND DATE '2026-09-29' GROUP BY order_date ORDER BY order_date;
```

**Domain + workflows — 5.89s — Matches reference**

Daily completed sales ranged between $1.12M and $1.73M over the last seven available days (September 23–29, 2026), dipping on September 24 before rebounding to a peak on September 27.

```sql
SELECT order_date AS label, ROUND(SUM(net_amount), 2) AS value FROM orders WHERE status = 'completed' AND order_date BETWEEN DATE '2026-09-23' AND DATE '2026-09-29' GROUP BY order_date ORDER BY order_date;
```

### Q3: Which five categories had the highest sales on 29 September 2026?

Reference result:

```json
[
  [
    "Haircare",
    48626.9
  ],
  [
    "Phones & Accessories",
    47499.73
  ],
  [
    "Headphones & Audio",
    47163.08
  ],
  [
    "Arts & Crafts",
    46450.58
  ],
  [
    "Team Sports",
    45279.8
  ]
]
```

**Runtime discovery — 26.43s — Inspect result / assumptions**

On 29 September 2026, the five categories with the highest sales were Headphones & Audio ($53,667.59), Haircare ($53,181.10), Makeup ($52,766.77), Arts & Crafts ($52,034.41), and Phones & Accessories ($51,835.14).

```sql
SELECT
    c.category_name,
    ROUND(SUM(oi.net_amount), 2) AS sales
FROM categories c
JOIN products p ON c.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_date = '2026-09-29'
GROUP BY c.category_name
ORDER BY sales DESC
LIMIT 5
```

**Schema only — 20.04s — Inspect result / assumptions**

On 29 September 2026, the five categories with the highest sales were Headphones & Audio ($53,667.59), Haircare ($53,181.10), Makeup ($52,766.77), Arts & Crafts ($52,034.41), and Phones & Accessories ($51,835.14).

```sql
SELECT
    c.category_name,
    ROUND(SUM(oi.net_amount), 2) AS total_sales
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN categories c ON p.category_id = c.category_id
WHERE o.order_date = '2026-09-29'
GROUP BY c.category_name
ORDER BY total_sales DESC
LIMIT 5;
```

**Guided queries — 5.88s — Matches reference**

On 29 September 2026, the top five categories by completed sales were Haircare ($48,626.90), Phones & Accessories ($47,499.73), Headphones & Audio ($47,163.08), Arts & Crafts ($46,450.58), and Team Sports ($45,279.80). Figures reflect completed order line net amounts excluding tax and shipping.

```sql
SELECT c.category_name AS label, SUM(i.net_amount) AS value
FROM order_items i
JOIN orders o ON o.order_id = i.order_id
JOIN products p ON p.product_id = i.product_id
JOIN categories c ON c.category_id = p.category_id
WHERE o.status = 'completed'
  AND o.order_date = DATE '2026-09-29'
GROUP BY c.category_id, c.category_name
ORDER BY value DESC
LIMIT 5;
```

**Domain + workflows — 5.61s — Matches reference**

On 29 September 2026, the top five categories by completed sales were Haircare ($48,626.90), Phones & Accessories ($47,499.73), Headphones & Audio ($47,163.08), Arts & Crafts ($46,450.58), and Team Sports ($45,279.80). Sales reflect net line amounts on completed orders, excluding taxes and shipping.

```sql
SELECT c.category_name AS label, ROUND(SUM(i.net_amount), 2) AS value
FROM order_items i
JOIN orders o ON o.order_id = i.order_id
JOIN products p ON p.product_id = i.product_id
JOIN categories c ON c.category_id = p.category_id
WHERE o.status = 'completed'
  AND o.order_date = DATE '2026-09-29'
GROUP BY c.category_id, c.category_name
ORDER BY value DESC
LIMIT 5;
```

### Q4: How many units sold on 29 September 2026?

Reference result:

```json
[
  [
    "Units sold",
    14095.0
  ]
]
```

**Runtime discovery — 40.87s — Matches reference**

A total of 14,095 units were sold across completed orders on 29 September 2026 (or 16,019 units across all order statuses including returns and cancellations).

```sql
SELECT SUM(oi.quantity) AS units_sold
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_date = '2026-09-29'
  AND o.status = 'completed'
```

**Schema only — 19.10s — Matches reference**

On 29 September 2026, a total of 14,095 units were sold across completed orders (or 16,019 units across all order statuses).

```sql
SELECT SUM(oi.quantity) AS units_sold
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_date = '2026-09-29'
  AND o.status = 'completed'
```

**Guided queries — 5.18s — Matches reference**

A total of 14,095 units were sold across completed orders on 29 September 2026.

```sql
SELECT SUM(oi.quantity) AS "value"
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE o.status = 'completed'
  AND o.order_date = DATE '2026-09-29';
```

**Domain + workflows — 4.52s — Matches reference**

There were 14,095 units sold across completed orders on 29 September 2026.

```sql
SELECT SUM(i.quantity) AS "value"
FROM order_items i
JOIN orders o ON o.order_id = i.order_id
WHERE o.status = 'completed'
  AND o.order_date = DATE '2026-09-29';
```

### Q5: What was session conversion on 29 September 2026?

Reference result:

```json
[
  [
    "Placed-order session conversion (%)",
    24.98596819457437
  ]
]
```

**Runtime discovery — 9.59s — Matches reference**

On 29 September 2026, the session conversion rate was 24.99%, with 2,671 orders placed across 10,690 total sessions.

```sql
SELECT
  ROUND(COUNT(order_id)::DOUBLE / COUNT(*) * 100, 2) AS session_conversion_rate
FROM sessions
WHERE session_date = '2026-09-29';
```

**Schema only — 3.99s — Matches reference**

On September 29, 2026, the session conversion rate was 24.99%, with 2,671 out of 10,690 sessions resulting in an order.

```sql
SELECT
    COUNT(*) AS total_sessions,
    COUNT(order_id) AS converted_sessions,
    ROUND(100.0 * COUNT(order_id) / COUNT(*), 2) AS conversion_rate_pct
FROM sessions
WHERE session_date = '2026-09-29';
```

**Guided queries — 8.43s — Matches reference**

Session conversion on 29 September 2026 was 24.99% for placed orders (2,671 orders from 10,690 sessions). If restricted to completed orders, the conversion rate was 21.96%.

```sql
SELECT
    ROUND(100.0 * COUNT(order_id) / COUNT(*), 2) AS conversion_rate
FROM sessions
WHERE session_date = DATE '2026-09-29';
```

**Domain + workflows — 11.85s — Matches reference**

Session conversion was 24.99% on 29 September 2026, measured as placed-order sessions divided by total sessions (21.96% if restricted to completed orders).

```sql
SELECT
  ROUND(100.0 * COUNT(order_id) / COUNT(*), 2) AS "value"
FROM sessions
WHERE session_date = DATE '2026-09-29';
```
