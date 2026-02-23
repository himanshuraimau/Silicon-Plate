# uploads cleaned CSV to S3 then loads star schema tables into RDS
# needs: AWS_S3_BUCKET, RDS_HOST, RDS_PORT, RDS_DBNAME, RDS_USER, RDS_PASSWORD env vars

import os
from pathlib import Path

import boto3
import pandas as pd
from sqlalchemy import create_engine, text

CLEANED_CSV = Path(__file__).parent.parent / "data" / "cleaned" / "zomato_cleaned.csv"

S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "silicon-plate-data")
RDS_HOST = os.environ.get("RDS_HOST", "localhost")
RDS_PORT = os.environ.get("RDS_PORT", "5432")
RDS_DBNAME = os.environ.get("RDS_DBNAME", "zomatodb")
RDS_USER = os.environ.get("RDS_USER", "postgres")
RDS_PASSWORD = os.environ.get("RDS_PASSWORD", "")


def upload_to_s3(local_path: Path, bucket: str, s3_key: str) -> None:
    print(f"\n☁️  Uploading to s3://{bucket}/{s3_key} ...")
    s3 = boto3.client("s3")
    s3.upload_file(str(local_path), bucket, s3_key)
    print("   ✓ Upload complete")


def get_engine():
    url = f"postgresql://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/{RDS_DBNAME}"
    return create_engine(url)


def load_dimensions(df: pd.DataFrame, engine) -> dict:
    ids: dict = {}

    with engine.connect() as conn:
        # dims first so we can get PKs back for the fact table
        locs = (
            df[["location", "zone"]]
            .dropna(subset=["location"])
            .drop_duplicates()
            .rename(columns={"location": "neighbourhood"})
            .reset_index(drop=True)
        )
        locs.to_sql("dim_location", conn, if_exists="append", index=False)
        result = conn.execute(text("SELECT location_id, neighbourhood FROM dim_location"))
        ids["location"] = {row.neighbourhood: row.location_id for row in result}
        print(f"dim_location: {len(locs)} rows")

        rests = df[["name"]].drop_duplicates().reset_index(drop=True)
        rests.to_sql("dim_restaurant", conn, if_exists="append", index=False)
        result = conn.execute(text("SELECT restaurant_id, name FROM dim_restaurant"))
        ids["restaurant"] = {row.name: row.restaurant_id for row in result}
        print(f"dim_restaurant: {len(rests)} rows")

        cuisines = (
            df[["primary_cuisine"]]
            .dropna(subset=["primary_cuisine"])
            .drop_duplicates()
            .rename(columns={"primary_cuisine": "cuisine_name"})
            .reset_index(drop=True)
        )
        cuisines.to_sql("dim_cuisine", conn, if_exists="append", index=False)
        result = conn.execute(text("SELECT cuisine_id, cuisine_name FROM dim_cuisine"))
        ids["cuisine"] = {row.cuisine_name: row.cuisine_id for row in result}
        print(f"dim_cuisine: {len(cuisines)} rows")

        types = (
            df[["rest_type"]]
            .dropna()
            .drop_duplicates()
            .rename(columns={"rest_type": "type_name"})
            .reset_index(drop=True)
        )
        types.to_sql("dim_restaurant_type", conn, if_exists="append", index=False)
        result = conn.execute(text("SELECT rest_type_id, type_name FROM dim_restaurant_type"))
        ids["rest_type"] = {row.type_name: row.rest_type_id for row in result}
        print(f"dim_restaurant_type: {len(types)} rows")

        conn.commit()

    return ids


def load_fact(df: pd.DataFrame, ids: dict, engine) -> None:
    fact = df.copy()
    fact["location_id"] = fact["location"].map(ids["location"])
    fact["restaurant_id"] = fact["name"].map(ids["restaurant"])
    fact["cuisine_id"] = fact["primary_cuisine"].map(ids["cuisine"])
    fact["rest_type_id"] = fact["rest_type"].map(ids["rest_type"])

    fact_cols = [
        "restaurant_id",
        "location_id",
        "cuisine_id",
        "rest_type_id",
        "rate",
        "votes",
        "approx_cost_for_two",
        "online_order",
        "book_table",
    ]
    fact_df = fact[fact_cols].rename(
        columns={
            "rate": "rating",
            "approx_cost_for_two": "avg_cost_for_two",
            "online_order": "online_order_flag",
            "book_table": "book_table_flag",
        }
    )
    # drop rows where any FK is unmapped (null location etc.)
    fact_df = fact_df.dropna(subset=["restaurant_id", "location_id"])

    with engine.connect() as conn:
        fact_df.to_sql(
            "fact_restaurant_performance", conn, if_exists="append", index=False, chunksize=1000
        )
        conn.commit()
    print(f"   ✓ fact_restaurant_performance loaded: {len(fact_df):,} rows")


def main() -> None:
    if not CLEANED_CSV.exists():
        print(f"run 02_transform.py first — {CLEANED_CSV} not found")
        return

    df = pd.read_csv(CLEANED_CSV)
    print(f"loaded {df.shape[0]:,} rows")

    upload_to_s3(CLEANED_CSV, S3_BUCKET, "zomato/cleaned/zomato_cleaned.csv")

    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(f"connected to {RDS_HOST}/{RDS_DBNAME}")

    ids = load_dimensions(df, engine)
    load_fact(df, ids, engine)
    print("done")


if __name__ == "__main__":
    main()
