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
    coalesce(p.product_title, 'Unknown Product') as product_title,
    coalesce(p.main_category, 'Uncategorized') as main_category,
    r.rating,
    r.review_title,
    r.review_text,
    r.review_timestamp,
    r.helpful_votes,
    r.is_verified_purchase,
    -- ML Sentiment Enrichment Fields
    r.sentiment_label,
    r.sentiment_score
from reviews r
left join products p on r.parent_asin = p.parent_asin
