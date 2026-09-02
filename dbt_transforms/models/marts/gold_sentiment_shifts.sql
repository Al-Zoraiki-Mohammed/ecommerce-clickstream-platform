with fct as (
    select * from {{ ref('fct_reviews') }}
),

-- Detect the latest review timestamp across all records
max_date as (
    select coalesce(max(review_timestamp), current_timestamp()) as max_ts from fct
),

-- 1. Baseline: Historical reviews older than 7 days from dataset max date
baseline as (
    select
        f.parent_asin,
        count(*) as baseline_review_count,
        avg(case when f.sentiment_label = 'POSITIVE' then 1.0 else 0.0 end) as baseline_positive_ratio
    from fct f
    cross join max_date m
    where f.review_timestamp < timestamp_sub(m.max_ts, interval 7 day)
    group by f.parent_asin
),

-- 2. Recent Delta: Reviews within the last 7 days of dataset max date
recent as (
    select
        f.parent_asin,
        count(*) as recent_review_count,
        avg(case when f.sentiment_label = 'POSITIVE' then 1.0 else 0.0 end) as recent_positive_ratio
    from fct f
    cross join max_date m
    where f.review_timestamp >= timestamp_sub(m.max_ts, interval 7 day)
    group by f.parent_asin
)

-- 3. Calculate Sentiment Shift Index
select
    coalesce(r.parent_asin, b.parent_asin) as parent_asin,
    coalesce(b.baseline_review_count, 0) as baseline_review_count,
    coalesce(r.recent_review_count, 0) as recent_review_count,
    round(coalesce(b.baseline_positive_ratio, 0.0), 4) as baseline_positive_ratio,
    round(coalesce(r.recent_positive_ratio, 0.0), 4) as recent_positive_ratio,
    
    -- Calculate shift index percentage change
    case 
        when coalesce(b.baseline_review_count, 0) = 0 then 0.0
        when coalesce(r.recent_review_count, 0) = 0 then 0.0
        else round(safe_divide(coalesce(r.recent_positive_ratio, 0.0) - coalesce(b.baseline_positive_ratio, 0.0), coalesce(b.baseline_positive_ratio, 0.0)), 4)
    end as sentiment_shift_index,
    
    -- Anomaly flag logic: baseline exists, recent delta exists, positive sentiment dropped by >= 20%
    case
        when coalesce(b.baseline_review_count, 0) > 0 
         and coalesce(r.recent_review_count, 0) > 0
         and safe_divide(coalesce(r.recent_positive_ratio, 0.0) - coalesce(b.baseline_positive_ratio, 0.0), coalesce(b.baseline_positive_ratio, 0.0)) <= -0.20
        then true
        else false
    end as is_negative_anomaly

from recent r
full outer join baseline b on r.parent_asin = b.parent_asin
