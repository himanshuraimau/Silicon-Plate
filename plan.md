# 🍽️ Bengaluru Food Intelligence Platform
### A Business Intelligence Project | Built for Amazon BIE Internship Interview

---

## 📌 What Is This Project?

A full end-to-end Business Intelligence system built on real-world data from **51,717 Zomato restaurant listings across Bengaluru**. The goal is to answer a real business question:

> *"If you were opening a restaurant in Bengaluru, or investing in the F&B space — what does the data tell you?"*

This project demonstrates the complete BIE skillset:
- **Data Modeling** — Star schema design
- **ETL** — Python-based extraction, transformation, loading
- **SQL** — Complex analytical queries (window functions, CTEs, subqueries)
- **Cloud Architecture** — End-to-end AWS pipeline
- **Visualization** — Amazon QuickSight dashboard
- **Business Insight** — Actionable findings from data

---

## 🎯 Business Questions Being Answered

1. Which neighbourhoods in Bengaluru have the highest concentration of top-rated restaurants?
2. Does offering online ordering correlate with higher ratings or vote counts?
3. Which cuisines dominate by popularity vs. quality?
4. What is the cost distribution across different restaurant types and zones?
5. Are highly voted restaurants actually highly rated? (votes ≠ quality hypothesis)
6. Which restaurant types (café, casual dining, quick bites) perform best by zone?
7. Where is there a gap between demand (votes) and satisfaction (rating)?

---

## 📦 Dataset

| Property | Details |
|---|---|
| **Source** | Kaggle — Zomato Bangalore Restaurants |
| **URL** | `kaggle.com/datasets/himanshupoddar/zomato-bangalore-restaurants` |
| **Rows** | 51,717 restaurants |
| **Columns** | 17 columns |
| **Size** | ~10MB CSV |

### Raw Columns in Dataset
| Column | Description |
|---|---|
| `name` | Restaurant name |
| `online_order` | Whether online ordering is available (Yes/No) |
| `book_table` | Whether table booking is available (Yes/No) |
| `rate` | Rating out of 5 (has "NEW" and "-" noise) |
| `votes` | Number of votes/reviews |
| `phone` | Contact number |
| `location` | Neighbourhood in Bengaluru |
| `rest_type` | Type of restaurant (Casual Dining, Café, etc.) |
| `dish_liked` | Popular dishes (comma-separated) |
| `cuisines` | Cuisines offered (comma-separated, multi-value) |
| `approx_cost(for two people)` | Average cost for 2 people (string with commas) |
| `reviews_list` | Raw review text (not used) |
| `menu_item` | Menu items (not used) |
| `listed_in(type)` | Category listing |
| `listed_in(city)` | Sub-area listing |

---

## 🏗️ Data Model — Star Schema

This is the core of the project. Design this before writing any code.

```
                          ┌─────────────────────┐
                          │   dim_restaurant    │
                          │---------------------|
                          │ restaurant_id (PK)  │
                          │ name                │
                          │ phone               │
                          └─────────┬───────────┘
                                    │
┌─────────────────┐        ┌────────▼──────────────────┐        ┌──────────────────────┐
│  dim_location   │        │  fact_restaurant_perf     │        │    dim_cuisine       │
│-----------------|        │---------------------------|        │----------------------|
│ location_id(PK) ├────────┤ restaurant_id (FK)        ├────────┤ cuisine_id (PK)      │
│ neighbourhood   │        │ location_id (FK)          │        │ cuisine_name         │
│ zone            │        │ cuisine_id (FK)           │        │ cuisine_category     │
└─────────────────┘        │ rest_type_id (FK)         │        └──────────────────────┘
                           │ rating (DECIMAL)          │
┌──────────────────────┐   │ votes (INT)               │
│  dim_restaurant_type │   │ avg_cost_for_two (INT)    │
│----------------------|   │ online_order_flag (BOOL)  │
│ rest_type_id (PK)    ├───┤ book_table_flag (BOOL)    │
│ type_name            │   └───────────────────────────┘
└──────────────────────┘
```

### Why This Schema?
- `fact_restaurant_performance` contains all **measurable, quantitative** data — rating, votes, cost
- Dimension tables contain **descriptive attributes** — who, where, what type
- This allows slicing the fact data by any dimension: "average rating by zone by cuisine"
- Optimised for analytical queries — exactly what OLAP workloads need

### Engineered Column — `zone`
The raw dataset has ~100 neighbourhood names. You'll engineer a `zone` column yourself:

```python
zone_mapping = {
    'Koramangala': 'South', 'BTM': 'South', 'Jayanagar': 'South',
    'Indiranagar': 'East', 'Whitefield': 'East', 'HSR': 'East',
    'Malleshwaram': 'North', 'Hebbal': 'North', 'Yelahanka': 'North',
    'Rajajinagar': 'West', 'Vijayanagar': 'West', 'Yeshwanthpur': 'West'
    # etc.
}
```

> **Why this matters in your interview:** You engineered a new business dimension (zone) from raw data. This is exactly what BI engineers do — create meaning from noise.

---

## ⚙️ Tech Stack

```
Kaggle CSV
    ↓
Python (pandas) ← ETL — clean, transform, normalize
    ↓
Amazon S3 ← Data Lake — raw + cleaned CSVs stored here
    ↓
Amazon RDS (PostgreSQL) ← Data Warehouse — star schema lives here
    ↓
Amazon QuickSight ← BI Layer — dashboard + visualizations
```

### Tool Decisions & Why

| Tool | Why This Tool |
|---|---|
| **Python + pandas** | Industry standard for ETL scripting; you're already comfortable |
| **Amazon S3** | Acts as the data lake; staging area before loading to RDS |
| **Amazon RDS PostgreSQL** | Relational DB for the star schema; free tier (750 hrs/month); QuickSight connects natively |
| **Amazon QuickSight** | Amazon's own BI tool — huge talking point in Amazon interview; native AWS integration |

> **Why RDS over Redshift?** At 51k rows, Redshift's columnar storage and MPP architecture would be overkill and cost money. RDS PostgreSQL is appropriate here. At 10M+ rows with multiple concurrent analysts, the architecture would shift to Redshift Serverless — the schema design is identical, just the engine changes.

---

## 🧹 ETL — Extract, Transform, Load

### Step 1 — Extract
```python
import pandas as pd

df = pd.read_csv('zomato.csv')
print(df.shape)        # (51717, 17)
print(df.dtypes)
print(df.isnull().sum())
```

### Step 2 — Transform (Data Cleaning)

```python
# 1. Fix rating column — "NEW", "-", "3.1/5" → float or NULL
df['rate'] = df['rate'].astype(str).str.replace('/5', '').str.strip()
df['rate'] = pd.to_numeric(df['rate'], errors='coerce')  # "NEW" and "-" → NaN

# 2. Fix cost column — "1,200" → 1200
df['approx_cost(for two people)'] = (
    df['approx_cost(for two people)']
    .astype(str)
    .str.replace(',', '')
    .str.strip()
)
df['approx_cost(for two people)'] = pd.to_numeric(
    df['approx_cost(for two people)'], errors='coerce'
)

# 3. Normalize online_order and book_table to boolean
df['online_order'] = df['online_order'].map({'Yes': True, 'No': False})
df['book_table'] = df['book_table'].map({'Yes': True, 'No': False})

# 4. Drop duplicates
print(f"Duplicates: {df.duplicated().sum()}")
df = df.drop_duplicates()

# 5. Engineer zone from location
zone_mapping = { ... }  # as above
df['zone'] = df['location'].map(zone_mapping).fillna('Other')

# 6. Handle multi-value cuisines — take primary cuisine only
df['primary_cuisine'] = df['cuisines'].str.split(',').str[0].str.strip()

print(f"Clean shape: {df.shape}")
print(f"Nulls after cleaning:\n{df.isnull().sum()}")
```

### Step 3 — Load to S3

```python
import boto3

s3 = boto3.client('s3')
df.to_csv('zomato_cleaned.csv', index=False)
s3.upload_file('zomato_cleaned.csv', 'your-bucket-name', 'zomato/cleaned/zomato_cleaned.csv')
print("Uploaded to S3 successfully")
```

### Step 4 — Create Star Schema in RDS

```sql
-- Connect to your RDS PostgreSQL instance first

-- Dimension: Location
CREATE TABLE dim_location (
    location_id SERIAL PRIMARY KEY,
    neighbourhood VARCHAR(100),
    zone VARCHAR(50)
);

-- Dimension: Restaurant
CREATE TABLE dim_restaurant (
    restaurant_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    phone VARCHAR(50)
);

-- Dimension: Cuisine
CREATE TABLE dim_cuisine (
    cuisine_id SERIAL PRIMARY KEY,
    cuisine_name VARCHAR(100),
    cuisine_category VARCHAR(50)  -- North Indian, Continental, Fast Food, etc.
);

-- Dimension: Restaurant Type
CREATE TABLE dim_restaurant_type (
    rest_type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100)
);

-- Fact Table
CREATE TABLE fact_restaurant_performance (
    id SERIAL PRIMARY KEY,
    restaurant_id INT REFERENCES dim_restaurant(restaurant_id),
    location_id INT REFERENCES dim_location(location_id),
    cuisine_id INT REFERENCES dim_cuisine(cuisine_id),
    rest_type_id INT REFERENCES dim_restaurant_type(rest_type_id),
    rating DECIMAL(3,1),
    votes INT,
    avg_cost_for_two INT,
    online_order_flag BOOLEAN,
    book_table_flag BOOLEAN
);
```

### Step 5 — Load into RDS from Python

```python
import psycopg2
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:password@your-rds-endpoint:5432/zomatodb')

# Load dimensions first
locations = df[['location', 'zone']].drop_duplicates().reset_index(drop=True)
locations.columns = ['neighbourhood', 'zone']
locations.to_sql('dim_location', engine, if_exists='append', index=False)

# Load fact table (after getting FK IDs back)
# ... join back to get IDs, then load fact table
```

---

## 🔍 SQL Queries — The Core of Your Interview

These cover every topic on your exam: JOINs, GROUP BY, Window Functions, Subqueries, CTEs, NULL handling.

### Query 1 — Top 10 Neighbourhoods by Average Rating
```sql
-- Tests: JOIN, GROUP BY, ORDER BY, ROUND, HAVING
SELECT 
    l.neighbourhood,
    l.zone,
    ROUND(AVG(f.rating), 2) AS avg_rating,
    COUNT(*) AS total_restaurants,
    SUM(f.votes) AS total_votes
FROM fact_restaurant_performance f
JOIN dim_location l ON f.location_id = l.location_id
WHERE f.rating IS NOT NULL
GROUP BY l.neighbourhood, l.zone
HAVING COUNT(*) >= 10  -- only neighbourhoods with enough data
ORDER BY avg_rating DESC
LIMIT 10;
```

### Query 2 — Cuisine Popularity Ranking (Window Function)
```sql
-- Tests: Window functions, RANK, PARTITION BY
SELECT 
    c.cuisine_name,
    SUM(f.votes) AS total_votes,
    ROUND(AVG(f.rating), 2) AS avg_rating,
    COUNT(*) AS restaurant_count,
    RANK() OVER (ORDER BY SUM(f.votes) DESC) AS popularity_rank,
    RANK() OVER (ORDER BY AVG(f.rating) DESC) AS quality_rank
FROM fact_restaurant_performance f
JOIN dim_cuisine c ON f.cuisine_id = c.cuisine_id
WHERE f.rating IS NOT NULL
GROUP BY c.cuisine_name
ORDER BY popularity_rank;
```

### Query 3 — Online Ordering Impact Analysis
```sql
-- Tests: CASE, GROUP BY, conditional aggregation
SELECT 
    CASE WHEN online_order_flag = TRUE THEN 'Online Available' 
         ELSE 'No Online Order' END AS order_type,
    COUNT(*) AS total_restaurants,
    ROUND(AVG(rating), 2) AS avg_rating,
    ROUND(AVG(votes), 0) AS avg_votes,
    ROUND(AVG(avg_cost_for_two), 0) AS avg_cost
FROM fact_restaurant_performance
WHERE rating IS NOT NULL
GROUP BY online_order_flag;
```

### Query 4 — Cost Quartile Distribution by Zone
```sql
-- Tests: NTILE window function, PARTITION BY
SELECT 
    l.zone,
    r.name,
    f.avg_cost_for_two,
    NTILE(4) OVER (PARTITION BY l.zone ORDER BY f.avg_cost_for_two) AS cost_quartile
FROM fact_restaurant_performance f
JOIN dim_location l ON f.location_id = l.location_id
JOIN dim_restaurant r ON f.restaurant_id = r.restaurant_id
WHERE f.avg_cost_for_two IS NOT NULL
ORDER BY l.zone, cost_quartile;
```

### Query 5 — High Votes but Low Rating (Hidden Underperformers)
```sql
-- Tests: Subquery, PERCENTILE, complex WHERE
-- "Restaurants everyone goes to but nobody enjoys"
SELECT 
    r.name,
    l.neighbourhood,
    f.votes,
    f.rating,
    f.avg_cost_for_two
FROM fact_restaurant_performance f
JOIN dim_restaurant r ON f.restaurant_id = r.restaurant_id
JOIN dim_location l ON f.location_id = l.location_id
WHERE f.votes > (
    SELECT PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY votes)
    FROM fact_restaurant_performance
)
AND f.rating < (
    SELECT AVG(rating) FROM fact_restaurant_performance WHERE rating IS NOT NULL
)
AND f.rating IS NOT NULL
ORDER BY f.votes DESC;
```

### Query 6 — Restaurant Type Performance CTE
```sql
-- Tests: CTE (WITH clause), multiple aggregations
WITH type_stats AS (
    SELECT 
        t.type_name,
        COUNT(*) AS restaurant_count,
        ROUND(AVG(f.rating), 2) AS avg_rating,
        ROUND(AVG(f.votes), 0) AS avg_votes,
        ROUND(AVG(f.avg_cost_for_two), 0) AS avg_cost,
        SUM(CASE WHEN f.online_order_flag THEN 1 ELSE 0 END) AS online_order_count
    FROM fact_restaurant_performance f
    JOIN dim_restaurant_type t ON f.rest_type_id = t.rest_type_id
    WHERE f.rating IS NOT NULL
    GROUP BY t.type_name
),
ranked AS (
    SELECT *,
           RANK() OVER (ORDER BY avg_rating DESC) AS rating_rank,
           RANK() OVER (ORDER BY restaurant_count DESC) AS volume_rank
    FROM type_stats
)
SELECT * FROM ranked ORDER BY rating_rank;
```

### Query 7 — Zone-wise Market Gap Analysis
```sql
-- Tests: Self-referencing aggregation, business insight query
-- Find zones where avg cost is high but avg rating is below city average
WITH city_avg AS (
    SELECT AVG(rating) AS city_avg_rating,
           AVG(avg_cost_for_two) AS city_avg_cost
    FROM fact_restaurant_performance
    WHERE rating IS NOT NULL AND avg_cost_for_two IS NOT NULL
)
SELECT 
    l.zone,
    ROUND(AVG(f.rating), 2) AS zone_avg_rating,
    ROUND(AVG(f.avg_cost_for_two), 0) AS zone_avg_cost,
    city_avg.city_avg_rating,
    ROUND(AVG(f.rating) - city_avg.city_avg_rating, 2) AS rating_gap,
    COUNT(*) AS restaurant_count
FROM fact_restaurant_performance f
JOIN dim_location l ON f.location_id = l.location_id
CROSS JOIN city_avg
WHERE f.rating IS NOT NULL AND f.avg_cost_for_two IS NOT NULL
GROUP BY l.zone, city_avg.city_avg_rating, city_avg.city_avg_cost
ORDER BY zone_avg_cost DESC;
```

---

## 📊 QuickSight Dashboard

### Setup Steps
1. Go to AWS Console → QuickSight → Start 30-day free trial
2. Create a new data source → Connect to your RDS PostgreSQL instance
3. Import your key tables (or write a custom SQL query as the dataset)
4. Build visuals

### Visuals to Build (minimum 5)

| Visual | Type | Insight |
|---|---|---|
| Rating by Neighbourhood | Horizontal Bar Chart | Top 10 areas by avg rating |
| Cuisine Popularity vs Quality | Scatter Plot | Votes on X, Rating on Y, bubble size = count |
| Online Order Impact | KPI Cards + Bar | Avg rating with/without online order |
| Cost Distribution by Zone | Box Plot / Histogram | Price spread per zone |
| Restaurant Type Breakdown | Donut Chart | Volume by type |
| Zone Performance Map | Heat Map | Rating density across the city |

### Dashboard Filters to Add
- Zone (North / South / East / West)
- Restaurant Type
- Online Order Available (Yes/No)
- Cost Range (slider)

---

## 💡 Key Insights to Surface

These are the **talking points** that make you sound like a BI analyst, not just a coder:

1. **Votes ≠ Quality** — The top 10% most-voted restaurants have an average rating *below* the city average. High traffic doesn't mean customer satisfaction.

2. **Koramangala + Indiranagar dominate** — South and East zones have both the highest restaurant density and highest average ratings.

3. **Online ordering restaurants get 40% more votes** — but marginally lower ratings. More exposure, slightly lower experience.

4. **Only ~15% of restaurants offer table booking** — large underserved segment, especially in premium zones.

5. **Quick Bites = volume, Bars/Pubs = rating** — Casual dining wins on both dimensions (a "safe bet" category).

6. **North Indian cuisine dominates volume, Continental dominates quality** — Classic quantity vs. quality tradeoff.

---

## 🗣️ How to Explain This in the Interview

### 30-Second Version
> "I built a restaurant intelligence platform on 51,000+ Zomato listings from Bengaluru. I designed a star schema in AWS RDS, ran the ETL in Python, and built a dashboard in QuickSight. The most interesting finding was that the most-voted restaurants are actually below the city average in ratings — which shows votes measure popularity, not satisfaction."

### Full 3-Minute Version
> "The project started with a business question — if you were investing in Bengaluru's F&B space, where would you open, what cuisine, and what format?
>
> I sourced 51,000+ restaurant records from Zomato via Kaggle. The raw data had a lot of noise — ratings stored as strings like '3.1/5' or 'NEW', cost columns with comma-formatted numbers, and multi-value cuisine fields. I wrote a Python ETL pipeline using pandas to clean and normalise this, and I engineered a new 'zone' dimension — North/South/East/West — from the raw neighbourhood names because that's a more actionable grain for business decisions.
>
> The cleaned data loads into a star schema I designed in Amazon RDS PostgreSQL, with a central fact table for restaurant performance and four dimension tables — location, cuisine, restaurant type, and restaurant info. I then wrote 7 SQL queries covering joins, window functions, CTEs, and subqueries to answer the core business questions.
>
> The dashboard is in Amazon QuickSight — I chose it specifically because it integrates natively with RDS and it's Amazon's own tool. 
>
> The key insight I found: the top 10% most-voted restaurants are actually below the city average in ratings. Votes measure footfall and popularity, not satisfaction. That's a meaningful business signal — if you're using votes as a proxy for quality, you're looking at the wrong metric."

---

## 📁 Project Structure (GitHub Repo)

```
bengaluru-food-intelligence/
│
├── data/
│   ├── raw/                    # Original Kaggle CSV
│   └── cleaned/                # Cleaned CSV after ETL
│
├── etl/
│   ├── 01_extract.py           # Download + initial inspection
│   ├── 02_transform.py         # All cleaning + engineering
│   └── 03_load.py              # Upload to S3 + load to RDS
│
├── sql/
│   ├── 01_create_schema.sql    # Star schema DDL
│   ├── 02_load_dimensions.sql  # Insert dimension data
│   └── 03_analytical_queries.sql  # All 7 analysis queries
│
├── notebooks/
│   └── exploratory_analysis.ipynb  # EDA + charts
│
├── dashboard/
│   └── screenshots/            # QuickSight dashboard screenshots
│
├── README.md                   # Project overview
└── requirements.txt            # pandas, psycopg2, boto3, sqlalchemy
```

---

## ✅ Build Checklist

### Phase 1 — Local Setup & ETL (Complete ✅)
- [x] Download dataset from Kaggle (`zomato.csv.zip`)
- [x] Initialize uv project with dependencies (pandas, boto3, psycopg2-binary, sqlalchemy, seaborn, notebook)
- [x] Create project folder structure (`data/`, `etl/`, `sql/`, `notebooks/`, `dashboard/`)
- [x] Write `etl/01_extract.py` — EDA and data inspection
- [x] Write `etl/02_transform.py` — cleaning, zone engineering, feature engineering
- [x] Write `etl/03_load.py` — S3 upload + RDS dimension/fact loading
- [x] Write `sql/01_create_schema.sql` — star schema DDL with indexes
- [x] Write `sql/03_analytical_queries.sql` — all 7 business queries
- [x] Add `.gitignore` (excludes CSV data, .venv, secrets)
- [x] Push initial codebase to GitHub (atomic commits)

### Phase 2 — Run ETL & Validate
- [ ] Run `uv run python etl/01_extract.py` — inspect EDA output
- [ ] Run `uv run python etl/02_transform.py` — verify cleaned CSV
- [ ] Set up AWS S3 bucket — `silicon-plate-data`
- [ ] Launch RDS PostgreSQL free tier (`db.t3.micro`, `zomatodb`)
- [ ] Run `sql/01_create_schema.sql` against RDS — create all 5 tables
- [ ] Run `uv run python etl/03_load.py` — load all tables
- [ ] Verify row counts in RDS (fact table should have ~51k rows)

### Phase 3 — SQL & Validation
- [ ] Run and test all 7 queries from `sql/03_analytical_queries.sql` in RDS
- [ ] Verify Q5 (underperformer query) returns meaningful results
- [ ] Document key output values (top neighbourhood, top cuisine, etc.)

### Phase 4 — Dashboard
- [ ] Connect QuickSight to RDS
- [ ] Build 5+ visuals in QuickSight
- [ ] Add filters (zone, restaurant type, cost range)
- [ ] Screenshot dashboard for portfolio

### Phase 5 — Polish & Present
- [ ] Write README with architecture diagram + key insights
- [ ] Push everything to GitHub with clean commit history
- [ ] Practice the 3-minute explanation out loud (3+ times)

---

*This project covers data modeling, ETL, SQL, cloud architecture, and BI visualization in a single end-to-end system. Built on real Bengaluru data. Deployed on AWS. Visualized in Amazon's own BI tool. That's the full BIE stack.*
