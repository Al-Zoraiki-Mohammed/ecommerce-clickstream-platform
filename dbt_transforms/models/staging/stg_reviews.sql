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
        timestamp_millis(cast(timestamp as int64)) as review_timestamp,
        cast(helpful_vote as int64) as helpful_votes,
        cast(verified_purchase as boolean) as is_verified_purchase
    from source
    where parent_asin is not null and user_id is not null
)

-- Deduplicate identical user reviews on the same product
select * from renamed
qualify row_number() over (partition by user_id, parent_asin, review_timestamp order by helpful_votes desc) = 1
