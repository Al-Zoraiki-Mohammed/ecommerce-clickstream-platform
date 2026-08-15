{{ config(materialized='table', schema='gold') }}

WITH silver_products AS (
    SELECT * FROM {{ ref('stg_amazon_products') }}
)

SELECT
    COALESCE(primary_category, 'Uncategorized') AS category,
    COUNT(DISTINCT product_id) AS total_products,
    COUNT(DISTINCT brand) AS total_active_brands,
    ROUND(AVG(price_usd), 2) AS avg_product_price_usd,
    ROUND(MIN(price_usd), 2) AS min_product_price_usd,
    ROUND(MAX(price_usd), 2) AS max_product_price_usd,
    ROUND(AVG(avg_rating), 2) AS category_avg_rating,
    SUM(total_reviews) AS total_category_reviews,
    ROUND(SUM(total_reviews) / NULLIF(COUNT(DISTINCT product_id), 0), 1) AS avg_reviews_per_product
FROM silver_products
GROUP BY 1
HAVING total_products > 5
ORDER BY total_products DESC
