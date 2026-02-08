import pandas as pd
import joblib
import json
import sys
import argparse

# Load models
clf = joblib.load('suitability_pipeline.joblib')
reg = joblib.load('yield_pipeline.joblib')

def predict_single(crop_type, irrigation_type, soil_type, season, farm_area, fertilizer, pesticide, water_usage):
    input_data = {
        "Crop_Type": [crop_type],
        "Irrigation_Type": [irrigation_type],
        "Soil_Type": [soil_type],
        "Season": [season],
        "Farm_Area_acres": [farm_area],
        "Fertilizer_Used_tons": [fertilizer],
        "Pesticide_Used_kg": [pesticide],
        "Water_Usage_cubic_meters": [water_usage]
    }
    
    input_df = pd.DataFrame(input_data)
    
    suit_pred = clf.predict(input_df)[0]
    yield_pred = reg.predict(input_df)[0]
    
    return {
        "crop": crop_type,
        "suit_pred": int(suit_pred),
        "yield_pred": float(yield_pred)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--crop_type', required=True)
    parser.add_argument('--irrigation_type', required=True)
    parser.add_argument('--soil_type', required=True)
    parser.add_argument('--season', required=True)
    parser.add_argument('--farm_area', type=float, required=True)
    parser.add_argument('--fertilizer', type=float, required=True)
    parser.add_argument('--pesticide', type=float, required=True)
    parser.add_argument('--water_usage', type=float, required=True)
    
    args = parser.parse_args()
    
    if args.crop_type == 'all':
        crops = ['Rice', 'Wheat', 'Maize', 'Cotton', 'Sugarcane']
        results = []
        for crop in crops:
            result = predict_single(
                crop, args.irrigation_type, args.soil_type, args.season,
                args.farm_area, args.fertilizer, args.pesticide, args.water_usage
            )
            results.append(result)
        print(json.dumps(results))
    else:
        result = predict_single(
            args.crop_type, args.irrigation_type, args.soil_type, args.season,
            args.farm_area, args.fertilizer, args.pesticide, args.water_usage
        )
        print(json.dumps([result]))