# quick EDA script — run this first to understand the raw data
import sys
from pathlib import Path

import pandas as pd

RAW_CSV = Path(__file__).parent.parent / "data" / "raw" / "zomato.csv"


def main() -> None:
    df = pd.read_csv(RAW_CSV)

    print(f"shape: {df.shape}")
    print("\ndtypes:")
    print(df.dtypes.to_string())

    nulls = df.isnull().sum()
    null_pct = (nulls / len(df) * 100).round(1)
    null_report = pd.DataFrame({"null_count": nulls, "null_%": null_pct})
    null_report = null_report[null_report["null_count"] > 0].sort_values("null_count", ascending=False)
    print("\nnulls:")
    print(null_report.to_string())

    print("\nrate values (sample):")
    print(df["rate"].value_counts(dropna=False).head(20).to_string())

    print("\napprox_cost values (sample):")
    print(df["approx_cost(for two people)"].value_counts(dropna=False).head(15).to_string())

    print("\nrest_type:")
    print(df["rest_type"].value_counts(dropna=False).to_string())

    locations = sorted(df["location"].dropna().unique().tolist())
    print(f"\nunique locations ({len(locations)}):")
    for loc in locations:
        print(f"  {loc!r}")

    print("\ntop primary cuisines:")
    primary = df["cuisines"].str.split(",").str[0].str.strip()
    print(primary.value_counts().head(20).to_string())

    print(f"\nduplicates: {df.duplicated().sum()}")


if __name__ == "__main__":
    if not RAW_CSV.exists():
        print(f"file not found: {RAW_CSV}")
        sys.exit(1)
    main()
