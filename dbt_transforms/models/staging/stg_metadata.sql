with source as (
    select * from {{ source('raw_data', 'raw_metadata') }}
),

renamed as (
    select
        cast(parent_asin as string) as parent_asin,
        cast(title as string) as product_title,
        cast(main_category as string) as main_category,
        -- Remove currency symbols and safely convert to numeric
        safe_cast(regexp_replace(cast(price as string), r'[^\d.]', '') as numeric) as price,
        safe_cast(average_rating as float64) as average_rating,
        safe_cast(rating_number as int64) as total_ratings,
        cast(store as string) as store_name
    from source
)

select * from renamed
