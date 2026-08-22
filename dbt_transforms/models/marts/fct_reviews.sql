with reviews as (
    select * from {{ ref('stg_reviews') }}
),

products as (
    select parent_asin, product_title, main_category from {{ ref('stg_metadata') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['r.user_id', 'r.parent_asin', 'r.review_timestamp']) }} as review_id,
    r.user_id,
    r.parent_asin,
    p.product_title,
    p.main_category,
    r.rating,
    r.review_title,
    r.review_text,
    r.review_timestamp,
    r.helpful_votes,
    r.is_verified_purchase
from reviews r
left join products p on r.parent_asin = p.parent_asin
