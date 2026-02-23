-- star schema for zomato bangalore dataset
-- safe to re-run

DROP TABLE IF EXISTS fact_restaurant_performance CASCADE;
DROP TABLE IF EXISTS dim_location CASCADE;
DROP TABLE IF EXISTS dim_restaurant CASCADE;
DROP TABLE IF EXISTS dim_cuisine CASCADE;
DROP TABLE IF EXISTS dim_restaurant_type CASCADE;

CREATE TABLE dim_location (
    location_id   SERIAL PRIMARY KEY,
    neighbourhood VARCHAR(100) NOT NULL,
    zone          VARCHAR(50)  NOT NULL
);

CREATE TABLE dim_restaurant (
    restaurant_id SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL
);

CREATE TABLE dim_cuisine (
    cuisine_id       SERIAL PRIMARY KEY,
    cuisine_name     VARCHAR(100) NOT NULL,
    cuisine_category VARCHAR(50)
);

CREATE TABLE dim_restaurant_type (
    rest_type_id SERIAL PRIMARY KEY,
    type_name    VARCHAR(100) NOT NULL
);

CREATE TABLE fact_restaurant_performance (
    id                SERIAL PRIMARY KEY,
    restaurant_id     INT REFERENCES dim_restaurant(restaurant_id),
    location_id       INT REFERENCES dim_location(location_id),
    cuisine_id        INT REFERENCES dim_cuisine(cuisine_id),
    rest_type_id      INT REFERENCES dim_restaurant_type(rest_type_id),
    rating            DECIMAL(3,1),
    votes             INT,
    avg_cost_for_two  INT,
    online_order_flag BOOLEAN,
    book_table_flag   BOOLEAN
);

CREATE INDEX idx_fact_location  ON fact_restaurant_performance(location_id);
CREATE INDEX idx_fact_cuisine   ON fact_restaurant_performance(cuisine_id);
CREATE INDEX idx_fact_rest_type ON fact_restaurant_performance(rest_type_id);
CREATE INDEX idx_fact_rating    ON fact_restaurant_performance(rating);
CREATE INDEX idx_fact_votes     ON fact_restaurant_performance(votes);
