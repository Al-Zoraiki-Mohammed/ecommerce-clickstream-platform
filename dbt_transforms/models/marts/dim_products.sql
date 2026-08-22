with metadata as (
    select * from {{ ref('stg_metadata') }}
),

reviews_aggregated as (
    select
        parent_asin,
        count(user_id) as calculated_total_reviews,
        avg(rating) as calculated_avg_rating
    from {{ ref('stg_reviews') }}
    group by parent_asin
)

select
    m.parent_asin,
    m.product_title,
    m.main_category,
    m.price,
    m.average_rating as reported_average_rating,
    m.total_ratings as reported_total_ratings,
    coalesce(r.calculated_total_reviews, 0) as calculated_total_reviews,
    coalesce(r.calculated_avg_rating, m.average_rating) as calculated_avg_rating,
    m.store_name
from metadata m
left join reviews_aggregated r on m.parent_asin = r.parent_asin
