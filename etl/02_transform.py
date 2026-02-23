# cleans raw zomato CSV and saves to data/cleaned/

from pathlib import Path

import pandas as pd

RAW_CSV = Path(__file__).parent.parent / "data" / "raw" / "zomato.csv"
CLEANED_CSV = Path(__file__).parent.parent / "data" / "cleaned" / "zomato_cleaned.csv"

# manually mapped from the 93 unique locations in the dataset
ZONE_MAPPING: dict[str, str] = {
    # South
    "BTM": "South",
    "Banashankari": "South",
    "Bannerghatta Road": "South",
    "Basavanagudi": "South",
    "Bellandur": "South",
    "Bommanahalli": "South",
    "Electronic City": "South",
    "HSR": "South",
    "JP Nagar": "South",
    "Jayanagar": "South",
    "Kanakapura Road": "South",
    "Koramangala": "South",
    "Koramangala 1st Block": "South",
    "Koramangala 2nd Block": "South",
    "Koramangala 3rd Block": "South",
    "Koramangala 4th Block": "South",
    "Koramangala 5th Block": "South",
    "Koramangala 6th Block": "South",
    "Koramangala 7th Block": "South",
    "Koramangala 8th Block": "South",
    "Kumaraswamy Layout": "South",
    "South Bangalore": "South",
    "Sarjapur Road": "South",
    "Uttarahalli": "South",
    "Wilson Garden": "South",
    "Hosur Road": "South",
    "Ejipura": "South",
    # East
    "Banaswadi": "East",
    "Brookefield": "East",
    "CV Raman Nagar": "East",
    "Domlur": "East",
    "East Bangalore": "East",
    "ITPL Main Road, Whitefield": "East",
    "Indiranagar": "East",
    "Jeevan Bhima Nagar": "East",
    "Kaggadasapura": "East",
    "Kammanahalli": "East",
    "KR Puram": "East",
    "Mahadevapura": "East",
    "Marathahalli": "East",
    "Old Airport Road": "East",
    "Old Madras Road": "East",
    "Rammurthy Nagar": "East",
    "Thippasandra": "East",
    "Varthur Main Road, Whitefield": "East",
    "Whitefield": "East",
    # North
    "HBR Layout": "North",
    "Hebbal": "North",
    "Hennur": "North",
    "Jakkur": "North",
    "Jalahalli": "North",
    "Kalyan Nagar": "North",
    "Malleshwaram": "North",
    "Nagawara": "North",
    "New BEL Road": "North",
    "North Bangalore": "North",
    "RT Nagar": "North",
    "Sadashiv Nagar": "North",
    "Sahakara Nagar": "North",
    "Sanjay Nagar": "North",
    "Seshadripuram": "North",
    "Yelahanka": "North",
    # West
    "Basaveshwara Nagar": "West",
    "Kengeri": "West",
    "Magadi Road": "West",
    "Mysore Road": "West",
    "Nagarbhavi": "West",
    "Peenya": "West",
    "Rajajinagar": "West",
    "Rajarajeshwari Nagar": "West",
    "Vijay Nagar": "West",
    "West Bangalore": "West",
    "Yeshwantpur": "West",
    # Central
    "Brigade Road": "Central",
    "Central Bangalore": "Central",
    "Church Street": "Central",
    "City Market": "Central",
    "Commercial Street": "Central",
    "Cunningham Road": "Central",
    "Frazer Town": "Central",
    "Infantry Road": "Central",
    "Langford Town": "Central",
    "Lavelle Road": "Central",
    "MG Road": "Central",
    "Majestic": "Central",
    "Race Course Road": "Central",
    "Residency Road": "Central",
    "Richmond Road": "Central",
    "Sankey Road": "Central",
    "Shanti Nagar": "Central",
    "Shivajinagar": "Central",
    "St. Marks Road": "Central",
    "Ulsoor": "Central",
    "Vasanth Nagar": "Central",
}


def fix_rating(series: pd.Series) -> pd.Series:
    # "3.1/5" -> 3.1, "NEW"/"-" -> NaN
    return pd.to_numeric(
        series.astype(str).str.replace("/5", "", regex=False).str.strip(),
        errors="coerce",
    )


def fix_cost(series: pd.Series) -> pd.Series:
    # "1,200" -> 1200
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def main() -> None:
    df = pd.read_csv(RAW_CSV)
    print(f"loaded {df.shape[0]:,} rows")

    df["rate"] = fix_rating(df["rate"])
    df["approx_cost(for two people)"] = fix_cost(df["approx_cost(for two people)"])

    df["online_order"] = df["online_order"].map({"Yes": True, "No": False})
    df["book_table"] = df["book_table"].map({"Yes": True, "No": False})

    df = df.drop_duplicates()

    df["zone"] = df["location"].map(ZONE_MAPPING).fillna("Other")
    unmapped = df[df["zone"] == "Other"]["location"].value_counts()
    if len(unmapped):
        print(f"unmapped locations ({len(unmapped)}): {unmapped.index.tolist()}")
    print("zone distribution:")
    print(df["zone"].value_counts().to_string())

    df["primary_cuisine"] = df["cuisines"].str.split(",").str[0].str.strip()
    df = df.rename(columns={"approx_cost(for two people)": "approx_cost_for_two"})

    drop_cols = ["reviews_list", "menu_item", "dish_liked", "phone"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    print(f"final shape: {df.shape}")
    nulls = df.isnull().sum()
    print(nulls[nulls > 0].to_string())

    CLEANED_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEANED_CSV, index=False)
    print(f"saved -> {CLEANED_CSV}  ({CLEANED_CSV.stat().st_size / 1_024 / 1_024:.1f} MB)")


if __name__ == "__main__":
    main()
