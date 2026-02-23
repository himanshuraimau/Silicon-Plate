-- analytical queries for the zomato bangalore dataset


-- Q1: top 10 neighbourhoods by avg rating
SELECT
    l.neighbourhood,
    l.zone,
    ROUND(AVG(f.rating), 2)   AS avg_rating,
    COUNT(*)                  AS total_restaurants,
    SUM(f.votes)              AS total_votes
FROM fact_restaurant_performance f
JOIN dim_location l ON f.location_id = l.location_id
WHERE f.rating IS NOT NULL
GROUP BY l.neighbourhood, l.zone
HAVING COUNT(*) >= 10          -- only areas with enough data
ORDER BY avg_rating DESC
LIMIT 10;


-- Q2: cuisine popularity vs quality — are the most popular ones actually good?
SELECT
    c.cuisine_name,
    COUNT(*)                                               AS restaurant_count,
    SUM(f.votes)                                           AS total_votes,
    ROUND(AVG(f.rating), 2)                                AS avg_rating,
    RANK() OVER (ORDER BY SUM(f.votes) DESC)               AS popularity_rank,
    RANK() OVER (ORDER BY AVG(f.rating) DESC)              AS quality_rank
FROM fact_restaurant_performance f
JOIN dim_cuisine c ON f.cuisine_id = c.cuisine_id
WHERE f.rating IS NOT NULL
GROUP BY c.cuisine_name
ORDER BY popularity_rank;


-- Q3: does having online ordering correlate with higher ratings?
SELECT
    CASE
        WHEN online_order_flag = TRUE THEN 'Online Available'
        ELSE 'No Online Order'
    END                               AS order_type,
    COUNT(*)                          AS total_restaurants,
    ROUND(AVG(rating),  2)            AS avg_rating,
    ROUND(AVG(votes),   0)            AS avg_votes,
    ROUND(AVG(avg_cost_for_two), 0)   AS avg_cost_inr
FROM fact_restaurant_performance
WHERE rating IS NOT NULL
GROUP BY online_order_flag;


-- Q4: cost quartiles by zone
SELECT
    l.zone,
    r.name,
    f.avg_cost_for_two,
    NTILE(4) OVER (
        PARTITION BY l.zone
        ORDER BY f.avg_cost_for_two
    ) AS cost_quartile
FROM fact_restaurant_performance f
JOIN dim_location   l ON f.location_id    = l.location_id
JOIN dim_restaurant r ON f.restaurant_id  = r.restaurant_id
WHERE f.avg_cost_for_two IS NOT NULL
ORDER BY l.zone, cost_quartile;


-- Q5: high votes but low rating — places everyone visits but nobody enjoys
SELECT
    r.name,
    l.neighbourhood,
    l.zone,
    f.votes,
    f.rating,
    f.avg_cost_for_two
FROM fact_restaurant_performance f
JOIN dim_restaurant r ON f.restaurant_id = r.restaurant_id
JOIN dim_location   l ON f.location_id   = l.location_id
WHERE f.votes > (
    SELECT PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY votes)
    FROM fact_restaurant_performance
)
AND f.rating < (
    SELECT AVG(rating)
    FROM fact_restaurant_performance
    WHERE rating IS NOT NULL
)
AND f.rating IS NOT NULL
ORDER BY f.votes DESC;


-- Q6: performance by restaurant type
WITH type_stats AS (
    SELECT
        t.type_name,
        COUNT(*)                                                     AS restaurant_count,
        ROUND(AVG(f.rating),           2)                            AS avg_rating,
        ROUND(AVG(f.votes),            0)                            AS avg_votes,
        ROUND(AVG(f.avg_cost_for_two), 0)                            AS avg_cost,
        SUM(CASE WHEN f.online_order_flag THEN 1 ELSE 0 END)         AS online_order_count,
        ROUND(
            100.0 * SUM(CASE WHEN f.online_order_flag THEN 1 ELSE 0 END) / COUNT(*),
            1
        )                                                            AS online_order_pct
    FROM fact_restaurant_performance f
    JOIN dim_restaurant_type t ON f.rest_type_id = t.rest_type_id
    WHERE f.rating IS NOT NULL
    GROUP BY t.type_name
),
ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY avg_rating      DESC) AS rating_rank,
        RANK() OVER (ORDER BY restaurant_count DESC) AS volume_rank
    FROM type_stats
)
SELECT * FROM ranked
ORDER BY rating_rank;


-- Q7: zone market gap — zones with high avg cost but below-average ratings
WITH city_avg AS (
    SELECT
        AVG(rating)           AS city_avg_rating,
        AVG(avg_cost_for_two) AS city_avg_cost
    FROM fact_restaurant_performance
    WHERE rating IS NOT NULL
      AND avg_cost_for_two IS NOT NULL
)
SELECT
    l.zone,
    ROUND(AVG(f.rating),           2)                           AS zone_avg_rating,
    ROUND(AVG(f.avg_cost_for_two), 0)                           AS zone_avg_cost,
    ROUND(city_avg.city_avg_rating::numeric, 2)                 AS city_avg_rating,
    ROUND((AVG(f.rating) - city_avg.city_avg_rating)::numeric, 2) AS rating_gap,
    COUNT(*)                                                    AS restaurant_count,
    CASE
        WHEN AVG(f.avg_cost_for_two) > city_avg.city_avg_cost
         AND AVG(f.rating)           < city_avg.city_avg_rating
        THEN 'High Cost, Low Quality ⚠️'
        WHEN AVG(f.avg_cost_for_two) < city_avg.city_avg_cost
         AND AVG(f.rating)           > city_avg.city_avg_rating
        THEN 'Low Cost, High Quality ✅'
        ELSE 'Balanced'
    END                                                         AS market_signal
FROM fact_restaurant_performance f
JOIN dim_location l ON f.location_id = l.location_id
CROSS JOIN city_avg
WHERE f.rating IS NOT NULL
  AND f.avg_cost_for_two IS NOT NULL
GROUP BY l.zone, city_avg.city_avg_rating, city_avg.city_avg_cost
ORDER BY zone_avg_cost DESC;
