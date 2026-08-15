{{ config(materialized='table', schema='silver') }}

WITH raw_source AS (
    SELECT
        TRIM(parent_asin) AS product_id,
        TRIM(title) AS product_name,
        TRIM(main_category) AS primary_category,
        TRIM(store) AS brand,
        CAST(average_rating AS FLOAT64) AS avg_rating,
        CAST(rating_number AS INT64) AS total_reviews,
        SAFE_CAST(REGEXP_REPLACE(price, r'[^0-9.]', '') AS FLOAT64) AS price_usd,
        ROW_NUMBER() OVER(
            PARTITION BY parent_asin 
            ORDER BY rating_number DESC NULLS LAST
        ) AS dedupe_id
    FROM {{ source('ecommerce_bronze', 'raw_amazon_metadata') }}
    WHERE parent_asin IS NOT NULL
)

SELECT
    product_id,
    product_name,
    primary_category,
    brand,
    avg_rating,
    total_reviews,
    price_usd
FROM raw_source
WHERE dedupe_id = 1
