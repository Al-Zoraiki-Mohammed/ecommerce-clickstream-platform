with source as (
    select * from {{ source('raw_data', 'raw_reviews') }}
),

renamed as (
    select
        cast(user_id as string) as user_id,
        cast(parent_asin as string) as parent_asin,
        cast(rating as float64) as rating,
        cast(title as string) as review_title,
        cast(text as string) as review_text,
        -- Convert Unix timestamp (ms) to TIMESTAMP
        timestamp_millis(cast(timestamp as int64)) as review_timestamp,
        cast(helpful_vote as int64) as helpful_votes,
        cast(verified_purchase as boolean) as is_verified_purchase
    from source
)

select * from renamed
