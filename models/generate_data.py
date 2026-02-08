"""
generate_data.py
Produces a synthetic agriculture suitability CSV dataset.
Usage: python generate_data.py
Output: ./data/agriculture_suitability.csv
"""
import random
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = DATA_DIR / "agriculture_suitability.csv"

def generate(n_rows: int = 200, seed: int = 42):
    random.seed(seed)
    crop_types = ["Wheat", "Rice", "Maize", "Cotton", "Sugarcane"]
    soil_types = ["Loamy", "Sandy", "Clay", "Alluvial", "Black"]
    irrigation_types = ["Canal", "Tube-well", "Rain-fed", "Drip"]
    seasons = ["Kharif", "Rabi", "Zaid"]

    rows = []
    for i in range(1, n_rows + 1):
        crop = random.choice(crop_types)
        soil = random.choice(soil_types)
        irrigation = random.choice(irrigation_types)
        season = random.choice(seasons)

        farm_area = round(random.uniform(1, 50), 2)  # acres
        fertilizer = round(random.uniform(0.1, 5.0), 2)  # tons
        pesticide = round(random.uniform(0.5, 20.0), 2)  # kg
        water_usage = round(random.uniform(100, 10000), 2)  # cubic meters

        base_yield = {"Wheat": 3.0, "Rice": 4.5, "Maize": 3.8, "Cotton": 2.5, "Sugarcane": 6.0}[crop]
        yield_tons = round(base_yield * farm_area * random.uniform(0.6, 1.4), 2)

        suitable = (
            (soil in ["Loamy", "Alluvial", "Black"]) and
            (water_usage > 500) and
            (fertilizer >= 0.5) and
            (yield_tons / farm_area > 2.0)
        )
        suitability = "Suitable" if suitable else "Not Suitable"

        rows.append({
            "Farm_ID": f"FARM_{i:04d}",
            "Crop_Type": crop,
            "Farm_Area_acres": farm_area,
            "Irrigation_Type": irrigation,
            "Fertilizer_Used_tons": fertilizer,
            "Pesticide_Used_kg": pesticide,
            "Yield_tons": yield_tons,
            "Soil_Type": soil,
            "Season": season,
            "Water_Usage_cubic_meters": water_usage,
            "Suitability": suitability
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"Saved synthetic dataset to {OUT_CSV}")
    return OUT_CSV

if __name__ == "__main__":
    generate(n_rows=200, seed=42)
