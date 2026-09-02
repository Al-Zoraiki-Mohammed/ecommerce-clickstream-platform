with baseline_reviews as (
    select
        cast(user_id as string) as user_id,
        cast(parent_asin as string) as parent_asin,
        cast(rating as numeric) as rating,
        cast(title as string) as review_title,
        cast(text as string) as review_text,
        timestamp_millis(cast(timestamp as int64)) as review_timestamp,
        cast(helpful_vote as int64) as helpful_votes,
        cast(verified_purchase as boolean) as is_verified_purchase,
        cast(sentiment_label as string) as sentiment_label,
        cast(sentiment_score as numeric) as sentiment_score
    from {{ source('raw_data', 'raw_reviews_baseline') }}
),

delta_reviews as (
    select
        cast(user_id as string) as user_id,
        cast(parent_asin as string) as parent_asin,
        cast(rating as numeric) as rating,
        cast(title as string) as review_title,
        cast(text as string) as review_text,
        timestamp_millis(cast(timestamp as int64)) as review_timestamp,
        cast(helpful_vote as int64) as helpful_votes,
        cast(verified_purchase as boolean) as is_verified_purchase,
        cast(sentiment_label as string) as sentiment_label,
        cast(sentiment_score as numeric) as sentiment_score
    from {{ source('raw_data', 'raw_reviews_delta') }}
)

select * from baseline_reviews
union all
select * from delta_reviews
