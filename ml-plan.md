# Neighbourhood Clustering — Implementation Plan

**Goal:** Use K-Means clustering to group Bengaluru neighbourhoods by food culture patterns, not geography.

## Data Preparation

- Aggregate the fact table to neighbourhood level in SQL first
- Pull these features per neighbourhood: `avg_rating`, `avg_cost_for_two`, `total_restaurants`, `avg_votes`, `cuisine_diversity_count`, `pct_online_order`, `pct_book_table`, `dominant_restaurant_type`
- `cuisine_diversity_count` is a new engineered feature — count of distinct cuisines per neighbourhood
- Export aggregated neighbourhood-level dataframe from RDS using `pandas.read_sql()`
- Handle nulls — drop neighbourhoods with fewer than 5 restaurants
- Expected result: ~80–90 neighbourhoods as data points

## Clustering Process

- Normalize all features using `StandardScaler` from sklearn
- Run the Elbow Method: plot inertia vs K for K=2 to K=10
- Expect K=4 or K=5 as the elbow point
- Fit KMeans with chosen K, set `random_state=42`
- Assign cluster labels back to neighbourhood dataframe

## Cluster Profiling & Naming

Profile each cluster and assign meaningful names:
- **Cluster 0:** "Premium Dining Hubs" — high cost, high rating, high book_table %
- **Cluster 1:** "IT Corridor Food Courts" — high online order, medium cost, high volume
- **Cluster 2:** "Local Neighbourhood Gems" — low cost, decent rating, low votes
- **Cluster 3:** "High Traffic Low Satisfaction" — high votes, below avg rating

**Key Finding:** Geography doesn't predict food culture; socioeconomics does (e.g., Whitefield and Koramangala cluster together despite different geography).

## Visualization & Integration

- Create 2D scatter plot using PCA reduction
- Color points by cluster, label outlier neighbourhoods
- Export as PNG for GitHub README
- Add `cluster_id` column to `dim_location` in RDS
- Update QuickSight: add cluster as filter dimension and create cluster profile bar chart

## SQL & Business Intelligence

- Query: "Top cuisines within each cluster"
- Query: "Which clusters have most untapped table booking potential?"

## Optional: Predictive Classifier

- Train logistic regression to predict cluster from raw restaurant data
- Use 80/20 train/test split
- Report accuracy and confusion matrix
- Enables scoring for new restaurants

## Documentation & Delivery

- Document cluster profiles in README with business recommendations
- Example: "Cluster 2 has strong ratings but low online adoption — first-mover opportunity for delivery"
- Notebook: `03_neighbourhood_clustering.ipynb` in `/notebooks` folder
- Interview pitch (45s): Lead with insight, then mention method and business impact

## Libraries

`sklearn`, `matplotlib`, `seaborn`, `pandas`, `sqlalchemy`

**Timeline:** 1 day (with data already in RDS)