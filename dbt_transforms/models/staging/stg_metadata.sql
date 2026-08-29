with source as (
    select * from {{ source('raw_data', 'raw_metadata') }}
),

renamed as (
    select
        cast(parent_asin as string) as parent_asin,
        cast(title as string) as product_title,
        coalesce(cast(main_category as string), 'Uncategorized') as main_category,
        safe_cast(regexp_extract(cast(price as string), r'(\d+\.\d{2})') as numeric) as price,        safe_cast(average_rating as float64) as average_rating,
        safe_cast(rating_number as int64) as total_ratings,
        cast(store as string) as store_name
    from source
    where parent_asin is not null
)

-- Deduplicate products appearing in multiple category exports
select * from renamed
qualify row_number() over (partition by parent_asin order by total_ratings desc) = 1
