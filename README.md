# Silicon Plate — Bengaluru Food Intelligence Platform

End-to-end BI project on 51,717 Zomato restaurant listings across Bengaluru.

**Stack:** Python · PostgreSQL (Amazon RDS) · Amazon S3 · Amazon QuickSight

---

## Architecture

```
Kaggle CSV → Python ETL → Amazon S3 → Amazon RDS (Star Schema) → Amazon QuickSight
```

## Data Model

Star schema with 4 dimension tables and 1 fact table:

- `fact_restaurant_performance` — rating, votes, cost, flags
- `dim_location` — neighbourhood, zone
- `dim_restaurant` — name, phone
- `dim_cuisine` — cuisine name, category
- `dim_restaurant_type` — type name

## Business Questions Answered

1. Which neighbourhoods have the highest-rated restaurants?
2. Does online ordering correlate with higher ratings or votes?
3. Which cuisines dominate by popularity vs. quality?
4. How does cost distribute across zones?
5. Which restaurant types perform best?

## Key Insights

- **Votes ≠ Quality** — Top 10% most-voted restaurants average *below* city rating
- **South & East dominate** — Koramangala and Indiranagar lead on both density and rating
- **Online ordering → 40% more votes**, but marginally lower ratings

## Dashboard

Built on Amazon QuickSight. 5 visuals with filters on zone, restaurant type, and online order availability.

| Visual | Type |
|--------|------|
| Avg Rating by Neighbourhood | Horizontal Bar |
| Cuisine Popularity vs Quality | Scatter Plot |
| Online Order Impact | KPI / Bar |
| Cost Distribution by Zone | Box Plot |
| Restaurant Type Volume | Donut Chart |

![Rating by Neighbourhood](dashboard/screenshots/rating_by_neighbourhood.png)
![Cuisine Popularity vs Quality](dashboard/screenshots/cuisine_popularity_vs_quality.png)
![Online Order Impact](dashboard/screenshots/online_order_impact.png)
![Cost Distribution by Zone](dashboard/screenshots/cost_distribution_by_zone.png)
![Restaurant Type Volume](dashboard/screenshots/restaurant_type_volume.png)

## Running the ETL

```bash
# Install dependencies
uv sync

# Set up credentials
cp .env.example .env
# fill in RDS and S3 credentials in .env

# Run pipeline
uv run python etl/01_extract.py
uv run python etl/02_transform.py
uv run python etl/03_load.py

# Create schema in RDS
psql -h <rds-endpoint> -U postgres -d zomatodb -f sql/01_create_schema.sql
```

## Project Structure

```
etl/                  # Extract, transform, load scripts
sql/                  # Schema DDL + analytical queries
dashboard/screenshots # QuickSight dashboard visuals
data/raw              # Original Kaggle CSV
data/cleaned          # Transformed CSV uploaded to S3
docs/                 # RDS + S3 setup guide
```
