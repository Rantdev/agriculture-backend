# backend_api.py - Updated with Oracle Database Integration
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import json
from pathlib import Path
import numpy as np
from datetime import datetime
import os
import traceback
import random
import oracledb
import uuid

app = Flask(__name__)
CORS(app)

# Configuration
MODELS_DIR = Path("models")
SUIT_MODEL = MODELS_DIR / "suitability_pipeline.joblib"
YIELD_MODEL = MODELS_DIR / "yield_pipeline.joblib"
META_PATH = MODELS_DIR / "metadata.json"

# Oracle Database Configuration
ORACLE_CONFIG = {
    'user': os.getenv('ORACLE_USER', 'your_username'),
    'password': os.getenv('ORACLE_PASSWORD', 'your_password'),
    'dsn': os.getenv('ORACLE_DSN', 'localhost:1521/XE'),
    'min': 1,
    'max': 10,
    'increment': 1
}

# Initialize Oracle connection pool
# Initialize Oracle connection pool
oracle_pool = None

def init_oracle_pool():
    """Initialize Oracle connection pool"""
    global oracle_pool
    try:
        oracle_pool = oracledb.create_pool(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=ORACLE_CONFIG['dsn'],
            min=ORACLE_CONFIG['min'],
            max=ORACLE_CONFIG['max'],
            increment=ORACLE_CONFIG['increment']
        )
        print("✅ Oracle Database connection pool created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating Oracle connection pool: {e}")
        return False

def get_oracle_connection():
    """Get connection from Oracle pool"""
    try:
        return oracle_pool.acquire()
    except Exception as e:
        print(f"❌ Error getting Oracle connection: {e}")
        return None

def release_oracle_connection(connection):
    """Release connection back to pool"""
    try:
        if connection:
            oracle_pool.release(connection)
    except Exception as e:
        print(f"❌ Error releasing Oracle connection: {e}")
# Crop database with enhanced information
CROP_DATABASE = {
    "Rice": {
        "season": "Kharif", 
        "water_need": "High",
        "duration": "90-120 days",
        "profitability": "High",
        "risk": "Medium",
        "market_demand": "High",
        "ideal_soil": "Clayey Loam",
        "special_notes": "Requires standing water, high labor",
        "base_yield": 4.0,
        "optimal_fertilizer": 2.5,
        "optimal_water": 6000
    },
    "Wheat": {
        "season": "Rabi",
        "water_need": "Medium", 
        "duration": "110-130 days",
        "profitability": "Medium",
        "risk": "Low",
        "market_demand": "High",
        "ideal_soil": "Well-drained Loam",
        "special_notes": "Cold weather crop, frost tolerant",
        "base_yield": 3.5,
        "optimal_fertilizer": 2.0,
        "optimal_water": 4000
    },
    "Maize": {
        "season": "Kharif",
        "water_need": "Medium",
        "duration": "80-100 days", 
        "profitability": "Medium",
        "risk": "Medium",
        "market_demand": "High",
        "ideal_soil": "Well-drained Sandy Loam",
        "special_notes": "Quick growing, multiple varieties",
        "base_yield": 2.8,
        "optimal_fertilizer": 1.8,
        "optimal_water": 3500
    },
    "Cotton": {
        "season": "Kharif",
        "water_need": "Medium-High",
        "duration": "150-170 days",
        "profitability": "High", 
        "risk": "High",
        "market_demand": "Medium",
        "ideal_soil": "Black Cotton Soil",
        "special_notes": "Long duration, pest sensitive",
        "base_yield": 1.8,
        "optimal_fertilizer": 2.2,
        "optimal_water": 4500
    },
    "Sugarcane": {
        "season": "Throughout Year",
        "water_need": "Very High",
        "duration": "10-12 months",
        "profitability": "Very High",
        "risk": "Medium",
        "market_demand": "Medium",
        "ideal_soil": "Deep Loamy Soil",
        "special_notes": "Long term investment, high water need",
        "base_yield": 70.0,
        "optimal_fertilizer": 3.0,
        "optimal_water": 8000
    }
}

# Enhanced configuration
IRRIGATION_EFFICIENCY = {
    'Canal': 0.7, 'Tube-well': 0.8, 'Rain-fed': 0.5, 
    'Drip': 0.95, 'Sprinkler': 0.85
}

SOIL_QUALITY = {
    'Loamy': 1.0, 'Sandy': 0.8, 'Clay': 0.9, 
    'Alluvial': 1.1, 'Black': 1.05, 'Red': 0.75
}

EXPERIENCE_MULTIPLIER = {
    'Beginner': 0.8, 'Intermediate': 1.0, 'Expert': 1.15
}

WATER_QUALITY_MULTIPLIER = {
    'Poor': 0.7, 'Average': 0.85, 'Good': 1.0, 'Excellent': 1.1
}

REGION_MULTIPLIER = {
    'North': 1.0, 'South': 1.05, 'East': 0.95, 
    'West': 1.02, 'Central': 0.98
}

SEASON_MULTIPLIER = {
    'Kharif': 1.0, 'Rabi': 1.05, 'Zaid': 0.9, 'Whole Year': 1.02
}

MARKET_PRICES = {
    "Rice": 25, "Wheat": 22, "Maize": 18, 
    "Cotton": 65, "Sugarcane": 3.5
}

def load_models():
    """Load ML models and metadata with detailed error handling"""
    try:
        print("🔍 Looking for models...")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Models directory: {MODELS_DIR.absolute()}")
        
        if not MODELS_DIR.exists():
            print(f"❌ Models directory not found: {MODELS_DIR}")
            return None, None, None
        
        print("📁 Files in models directory:")
        for file in MODELS_DIR.iterdir():
            print(f"   - {file.name}")
        
        if not SUIT_MODEL.exists():
            print(f"❌ Suitability model not found: {SUIT_MODEL}")
            return None, None, None
            
        if not YIELD_MODEL.exists():
            print(f"❌ Yield model not found: {YIELD_MODEL}")
            return None, None, None
            
        if not META_PATH.exists():
            print(f"❌ Metadata not found: {META_PATH}")
            return None, None, None
        
        print("📦 Loading models...")
        clf = joblib.load(SUIT_MODEL)
        reg = joblib.load(YIELD_MODEL)
        meta = json.loads(META_PATH.read_text())
        
        print("✅ Models loaded successfully!")
        print(f"   - Numeric features: {meta.get('numeric_features', [])}")
        print(f"   - Categorical features: {meta.get('categorical_features', [])}")
        
        return clf, reg, meta
        
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        print(traceback.format_exc())
        return None, None, None

# Database Functions
async def store_crop_recommendation(user_id, form_data, recommendations, weather_data=None):
    """Store crop recommendation in Oracle Database"""
    connection = None
    try:
        connection = get_oracle_connection()
        if not connection:
            return False
        
        recommendation_id = f"CR_{uuid.uuid4().hex[:16]}"
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO crop_recommendations (
                recommendation_id, user_id, location, soil_type, irrigation_type, 
                water_availability, season, budget, farm_area, recommendations, weather_data
            ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11)
        """, (
            recommendation_id, user_id, form_data.get('location'), 
            form_data.get('soilType'), form_data.get('irrigationType'),
            form_data.get('waterAvailability'), form_data.get('season'),
            form_data.get('budget'), form_data.get('farmArea'),
            json.dumps(recommendations), 
            json.dumps(weather_data) if weather_data else None
        ))
        
        connection.commit()
        print(f"✅ Crop recommendation stored: {recommendation_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error storing crop recommendation: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            release_oracle_connection(connection)

async def store_yield_prediction(user_id, form_data, prediction):
    """Store yield prediction in Oracle Database"""
    connection = None
    try:
        connection = get_oracle_connection()
        if not connection:
            return False
        
        prediction_id = f"YP_{uuid.uuid4().hex[:16]}"
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO yield_predictions (
                prediction_id, user_id, crop_type, farm_area, soil_type, soil_ph,
                irrigation_type, water_usage, fertilizer, predicted_yield, confidence,
                suitability, recommendations, profitability_data
            ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14)
        """, (
            prediction_id, user_id, form_data.get('cropType'), 
            form_data.get('farmArea'), form_data.get('soilType'),
            form_data.get('soilPh'), form_data.get('irrigationType'),
            form_data.get('waterUsage'), form_data.get('fertilizer'),
            prediction.get('predicted_yield'), prediction.get('confidence'),
            prediction.get('suitability'), 
            json.dumps(prediction.get('recommendations', [])),
            json.dumps(prediction.get('profitability', {}))
        ))
        
        connection.commit()
        print(f"✅ Yield prediction stored: {prediction_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error storing yield prediction: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            release_oracle_connection(connection)

async def store_chat_message(user_id, user_message, assistant_response, source):
    """Store chat message in Oracle Database"""
    connection = None
    try:
        connection = get_oracle_connection()
        if not connection:
            return False
        
        message_id = f"CHAT_{uuid.uuid4().hex[:16]}"
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (message_id, user_id, user_message, assistant_response, message_source)
            VALUES (:1, :2, :3, :4, :5)
        """, (message_id, user_id, user_message, assistant_response, source))
        
        connection.commit()
        print(f"✅ Chat message stored: {message_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error storing chat message: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            release_oracle_connection(connection)

async def store_batch_processing(user_id, file_info, process_type, results):
    """Store batch processing result in Oracle Database"""
    connection = None
    try:
        connection = get_oracle_connection()
        if not connection:
            return False
        
        batch_id = f"BATCH_{uuid.uuid4().hex[:16]}"
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO batch_processings (batch_id, user_id, file_name, file_size, process_type, total_records, results)
            VALUES (:1, :2, :3, :4, :5, :6, :7)
        """, (
            batch_id, user_id, file_info.get('name'), 
            file_info.get('size'), process_type,
            results.get('total_records'), json.dumps(results)
        ))
        
        connection.commit()
        print(f"✅ Batch processing stored: {batch_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error storing batch processing: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            release_oracle_connection(connection)

async def store_user_favorite(user_id, crop_name, category='crops'):
    """Store user favorite in Oracle Database"""
    connection = None
    try:
        connection = get_oracle_connection()
        if not connection:
            return False
        
        favorite_id = f"FAV_{uuid.uuid4().hex[:16]}"
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO user_favorites (favorite_id, user_id, crop_name, category)
            VALUES (:1, :2, :3, :4)
        """, (favorite_id, user_id, crop_name, category))
        
        connection.commit()
        print(f"✅ User favorite stored: {favorite_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error storing user favorite: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            release_oracle_connection(connection)

async def remove_user_favorite(user_id, crop_name):
    """Remove user favorite from Oracle Database"""
    connection = None
    try:
        connection = get_oracle_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM user_favorites 
            WHERE user_id = :1 AND crop_name = :2
        """, (user_id, crop_name))
        
        connection.commit()
        print(f"✅ User favorite removed: {crop_name}")
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"❌ Error removing user favorite: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            release_oracle_connection(connection)

# Load models at startup
print("🚀 Initializing Agriculture Backend...")
clf, reg, meta = load_models()

# Initialize Oracle pool

def calculate_real_yield_prediction(inputs):
    """Calculate realistic yield prediction based on input parameters"""
    crop_data = CROP_DATABASE[inputs['cropType']]
    base_yield = crop_data['base_yield']
    
    # Apply realistic modifiers with some randomness
    random_factor = 0.9 + (random.random() * 0.2)  # 0.9 to 1.1
    
    # Start with base yield
    predicted_yield = base_yield * random_factor
    
    # Apply all modifiers
    irrigation_eff = IRRIGATION_EFFICIENCY.get(inputs['irrigationType'], 0.8)
    soil_qual = SOIL_QUALITY.get(inputs['soilType'], 1.0)
    experience_mult = EXPERIENCE_MULTIPLIER.get(inputs['experienceLevel'], 1.0)
    water_qual_mult = WATER_QUALITY_MULTIPLIER.get(inputs['waterQuality'], 1.0)
    region_mult = REGION_MULTIPLIER.get(inputs['region'], 1.0)
    season_mult = SEASON_MULTIPLIER.get(inputs['season'], 1.0)
    
    predicted_yield *= irrigation_eff
    predicted_yield *= soil_qual
    predicted_yield *= experience_mult
    predicted_yield *= water_qual_mult
    predicted_yield *= region_mult
    predicted_yield *= season_mult
    
    # Fertilizer effect (optimal range based on crop)
    optimal_fert = crop_data['optimal_fertilizer']
    fertilizer_effect = calculate_fertilizer_effect(inputs['fertilizer'], optimal_fert)
    predicted_yield *= fertilizer_effect
    
    # Water usage effect
    optimal_water = crop_data['optimal_water']
    water_effect = calculate_water_effect(inputs['waterUsage'], optimal_water)
    predicted_yield *= water_effect
    
    # Organic fertilizer bonus
    if inputs.get('organicFertilizer', False):
        predicted_yield *= 1.08
    
    # IPM approach bonus
    if inputs.get('ipmApproach', False):
        predicted_yield *= 1.05
    
    # Calculate confidence based on input quality
    confidence = calculate_confidence(inputs, crop_data)
    
    # Margin of error (5-15% based on confidence)
    margin_error = predicted_yield * (0.15 - (confidence * 0.1))
    
    # Determine suitability
    yield_percentage = (predicted_yield / base_yield) * 100
    suitability = determine_suitability(yield_percentage)
    
    # Calculate optimization score
    optimization_score = calculate_optimization_score(inputs, crop_data)
    
    return {
        'predicted_yield': round(predicted_yield, 2),
        'margin_error': round(margin_error, 2),
        'confidence': round(confidence, 2),
        'suitability': suitability,
        'yield_range': {
            'min': round(predicted_yield - margin_error, 2),
            'max': round(predicted_yield + margin_error, 2)
        },
        'optimization_score': optimization_score,
        'risk_factors': generate_risk_factors(inputs, predicted_yield, base_yield),
        'recommendations': generate_recommendations(inputs, crop_data)
    }

def calculate_fertilizer_effect(actual_fert, optimal_fert):
    """Calculate fertilizer effect on yield"""
    if actual_fert < optimal_fert * 0.5:
        return 0.7  # Severe deficiency
    elif actual_fert < optimal_fert * 0.8:
        return 0.85  # Moderate deficiency
    elif actual_fert <= optimal_fert * 1.2:
        return 1.0  # Optimal range
    elif actual_fert <= optimal_fert * 1.5:
        return 0.95  # Slight excess
    else:
        return 0.9  # Significant excess

def calculate_water_effect(actual_water, optimal_water):
    """Calculate water effect on yield"""
    if actual_water < optimal_water * 0.5:
        return 0.6  # Severe water stress
    elif actual_water < optimal_water * 0.8:
        return 0.8  # Moderate water stress
    elif actual_water <= optimal_water * 1.2:
        return 1.0  # Optimal range
    elif actual_water <= optimal_water * 1.5:
        return 0.9  # Slight excess
    else:
        return 0.85  # Significant excess (waterlogging)

def calculate_confidence(inputs, crop_data):
    """Calculate prediction confidence based on input quality"""
    confidence = 0.7  # Base confidence
    
    # Check fertilizer optimization
    optimal_fert = crop_data['optimal_fertilizer']
    if optimal_fert * 0.8 <= inputs['fertilizer'] <= optimal_fert * 1.2:
        confidence += 0.1
    
    # Check water optimization
    optimal_water = crop_data['optimal_water']
    if optimal_water * 0.8 <= inputs['waterUsage'] <= optimal_water * 1.2:
        confidence += 0.1
    
    # Experience level
    if inputs['experienceLevel'] == 'Expert':
        confidence += 0.05
    
    # Water quality
    if inputs['waterQuality'] == 'Excellent':
        confidence += 0.05
    
    # Additional practices
    if inputs.get('organicFertilizer', False):
        confidence += 0.03
    if inputs.get('ipmApproach', False):
        confidence += 0.02
    
    return min(confidence, 0.95)  # Cap at 95%

def determine_suitability(yield_percentage):
    """Determine crop suitability based on yield percentage"""
    if yield_percentage >= 90:
        return "Highly Suitable"
    elif yield_percentage >= 75:
        return "Suitable"
    elif yield_percentage >= 60:
        return "Moderately Suitable"
    else:
        return "Not Suitable"

def calculate_optimization_score(inputs, crop_data):
    """Calculate optimization score (0-100)"""
    score = 50  # Base score
    
    # Fertilizer optimization
    optimal_fert = crop_data['optimal_fertilizer']
    if optimal_fert * 0.9 <= inputs['fertilizer'] <= optimal_fert * 1.1:
        score += 20
    elif optimal_fert * 0.8 <= inputs['fertilizer'] <= optimal_fert * 1.2:
        score += 10
    
    # Water optimization
    optimal_water = crop_data['optimal_water']
    if optimal_water * 0.9 <= inputs['waterUsage'] <= optimal_water * 1.1:
        score += 20
    elif optimal_water * 0.8 <= inputs['waterUsage'] <= optimal_water * 1.2:
        score += 10
    
    # Additional practices
    if inputs.get('organicFertilizer', False):
        score += 8
    if inputs.get('ipmApproach', False):
        score += 7
    
    # Water quality
    if inputs['waterQuality'] == 'Excellent':
        score += 5
    elif inputs['waterQuality'] == 'Good':
        score += 3
    
    # Experience
    if inputs['experienceLevel'] == 'Expert':
        score += 5
    
    return max(0, min(100, score))

def generate_risk_factors(inputs, predicted_yield, optimal_yield):
    """Generate risk factors based on inputs"""
    factors = []
    yield_percentage = (predicted_yield / optimal_yield) * 100
    
    if yield_percentage < 70:
        factors.append("Yield significantly below optimal potential")
    
    if inputs['waterQuality'] == 'Poor':
        factors.append("Poor water quality may affect crop health")
    
    if inputs['fertilizer'] < CROP_DATABASE[inputs['cropType']]['optimal_fertilizer'] * 0.7:
        factors.append("Insufficient fertilizer for optimal growth")
    
    if inputs['waterUsage'] < CROP_DATABASE[inputs['cropType']]['optimal_water'] * 0.7:
        factors.append("Low water availability may stress crops")
    
    if inputs['experienceLevel'] == 'Beginner':
        factors.append("Beginner experience may impact best practices implementation")
    
    return factors

def generate_recommendations(inputs, crop_data):
    """Generate personalized recommendations"""
    recommendations = []
    
    # Fertilizer recommendations
    optimal_fert = crop_data['optimal_fertilizer']
    if inputs['fertilizer'] < optimal_fert * 0.8:
        recommendations.append(f"Increase fertilizer to {optimal_fert} tons for better yield")
    elif inputs['fertilizer'] > optimal_fert * 1.3:
        recommendations.append(f"Reduce fertilizer to {optimal_fert} tons to prevent nutrient runoff")
    
    # Water recommendations
    optimal_water = crop_data['optimal_water']
    if inputs['waterUsage'] < optimal_water * 0.8:
        recommendations.append(f"Increase water supply to {optimal_water}m³ for optimal growth")
    elif inputs['waterUsage'] > optimal_water * 1.3:
        recommendations.append(f"Reduce water usage to {optimal_water}m³ to improve efficiency")
    
    # Additional practices
    if not inputs.get('organicFertilizer', False):
        recommendations.append("Consider organic fertilizers for long-term soil health")
    
    if not inputs.get('ipmApproach', False):
        recommendations.append("Implement Integrated Pest Management to reduce chemical dependency")
    
    if inputs['waterQuality'] == 'Poor':
        recommendations.append("Improve water quality through filtration or alternative sources")
    
    return recommendations

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "🌾 Smart Agriculture API Server",
        "status": "running",
        "models_loaded": clf is not None and reg is not None,
        "oracle_connected": oracle_pool is not None,
        "endpoints": {
            "GET /": "API information",
            "GET /api/health": "Health check",
            "POST /api/recommendations": "Crop recommendations",
            "POST /api/predict-yield": "Yield prediction",
            "GET /api/crop-database": "All crop data",
            "GET /api/crop/<name>": "Specific crop details",
            "POST /api/store-crop-recommendation": "Store crop recommendation",
            "POST /api/store-yield-prediction": "Store yield prediction",
            "POST /api/store-chat-message": "Store chat message",
            "POST /api/store-batch-processing": "Store batch processing",
            "POST /api/store-favorite": "Store user favorite",
            "DELETE /api/remove-favorite": "Remove user favorite"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    models_loaded = clf is not None and reg is not None
    oracle_connected = oracle_pool is not None
    status = "healthy" if models_loaded and oracle_connected else "degraded"
    
    return jsonify({
        "status": status,
        "models_loaded": models_loaded,
        "oracle_connected": oracle_connected,
        "message": "All systems operational" if models_loaded and oracle_connected else "Some components unavailable",
        "crops_available": list(CROP_DATABASE.keys()),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/predict-yield', methods=['POST'])
async def predict_yield():
    """Enhanced yield prediction endpoint that matches frontend inputs"""
    try:
        data = request.json
        print(f"📨 Received yield prediction request: {data}")
        
        # Validate required fields
        required_fields = ['cropType', 'irrigationType', 'soilType', 'season', 'farmArea']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Set default values for optional fields
        inputs = {
            'cropType': data['cropType'],
            'irrigationType': data['irrigationType'],
            'soilType': data['soilType'],
            'season': data['season'],
            'farmArea': float(data['farmArea']),
            'fertilizer': float(data.get('fertilizer', 2.0)),
            'pesticide': float(data.get('pesticide', 10.0)),
            'waterUsage': float(data.get('waterUsage', 5000)),
            'experienceLevel': data.get('experienceLevel', 'Intermediate'),
            'organicFertilizer': data.get('organicFertilizer', False),
            'ipmApproach': data.get('ipmApproach', False),
            'waterQuality': data.get('waterQuality', 'Good'),
            'region': data.get('region', 'North'),
            'previousYield': float(data.get('previousYield', 3.5))
        }
        
        # Validate crop type
        if inputs['cropType'] not in CROP_DATABASE:
            return jsonify({"error": f"Invalid crop type: {inputs['cropType']}"}), 400
        
        # Calculate prediction using real algorithm
        prediction_result = calculate_real_yield_prediction(inputs)
        
        # Add crop info
        prediction_result['crop_info'] = {
            'season': CROP_DATABASE[inputs['cropType']]['season'],
            'water_need': CROP_DATABASE[inputs['cropType']]['water_need'],
            'duration': CROP_DATABASE[inputs['cropType']]['duration'],
            'risk': CROP_DATABASE[inputs['cropType']]['risk']
        }
        
        response = {
            'predicted_yield': prediction_result['predicted_yield'],
            'margin_error': prediction_result['margin_error'],
            'confidence': prediction_result['confidence'],
            'suitability': prediction_result['suitability'],
            'yield_range': prediction_result['yield_range'],
            'crop_info': prediction_result['crop_info'],
            'optimization_score': prediction_result['optimization_score'],
            'risk_factors': prediction_result['risk_factors'],
            'recommendations': prediction_result['recommendations'],
            'inputs_used': inputs,
            'message': 'Yield prediction calculated using real agricultural algorithm'
        }
        
        # Store in database if user_id provided
        user_id = data.get('userId')
        if user_id and oracle_pool:
            await store_yield_prediction(user_id, inputs, prediction_result)
        
        print(f"✅ Prediction completed: {prediction_result['predicted_yield']} tons")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in yield prediction: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommendations', methods=['POST'])
async def get_recommendations():
    try:
        data = request.json
        print(f"📨 Received recommendation request")
        
        # Use real algorithm if models aren't loaded
        if clf is None or reg is None:
            print("⚠️ Using real algorithm (models not loaded)")
            return await get_real_recommendations(data)
        
        # ... (existing recommendation logic)
        
    except Exception as e:
        print(f"Error in recommendations: {e}")
        return jsonify({"error": str(e)}), 500

async def get_real_recommendations(data):
    """Provide real recommendations using the yield prediction algorithm"""
    farm_area = float(data.get('farmArea', 10))
    soil_type = data.get('soilType', 'Loamy')
    irrigation_type = data.get('irrigationType', 'Canal')
    season = data.get('season', 'Kharif')
    
    recommendations = []
    
    for crop in CROP_DATABASE.keys():
        try:
            # Create input data for the crop
            inputs = {
                'cropType': crop,
                'irrigationType': irrigation_type,
                'soilType': soil_type,
                'season': season,
                'farmArea': farm_area,
                'fertilizer': CROP_DATABASE[crop]['optimal_fertilizer'],
                'waterUsage': CROP_DATABASE[crop]['optimal_water'],
                'experienceLevel': 'Intermediate',
                'organicFertilizer': False,
                'ipmApproach': False,
                'waterQuality': 'Good',
                'region': 'North',
                'previousYield': CROP_DATABASE[crop]['base_yield'] * 0.8
            }
            
            # Get prediction
            prediction = calculate_real_yield_prediction(inputs)
            
            recommendations.append({
                "crop": crop,
                "suitability": prediction['suitability'],
                "expectedYield": prediction['predicted_yield'],
                "netProfit": int(prediction['predicted_yield'] * 1000 * MARKET_PRICES.get(crop, 20) * 0.3),
                "roi": prediction['optimization_score'],
                "risk": CROP_DATABASE[crop]["risk"],
                "season": CROP_DATABASE[crop]["season"],
                "waterNeed": CROP_DATABASE[crop]["water_need"],
                "duration": CROP_DATABASE[crop]["duration"],
                "profitability": CROP_DATABASE[crop]["profitability"],
                "marketDemand": CROP_DATABASE[crop]["market_demand"]
            })
            
        except Exception as e:
            print(f"Error predicting for {crop}: {e}")
            continue
    
    recommendations.sort(key=lambda x: x["expectedYield"], reverse=True)
    
    # Store in database if user_id provided
    user_id = data.get('userId')
    if user_id and oracle_pool:
        await store_crop_recommendation(user_id, data, recommendations)
    
    return jsonify({
        "recommendations": recommendations,
        "total_crops_evaluated": len(recommendations),
        "recommendations": {
    "recommendations": [
      {
        "crop": "Rice",
        "suitability": "Suitable",
        "expectedYield": "3.5 tons",
        "netProfit": 42000,
        "roi": "35%",
        "risk": "Medium",
        "season": "Kharif",
        "waterNeed": "Medium",
        "duration": "120 days",
        "profitability": "High",
        "marketDemand": "Medium"
      }
    ],
    "message": "AI-powered recommendations based on your farm conditions"
  }
    })

@app.route('/api/crop-database', methods=['GET'])
def get_crop_database():
    return jsonify(CROP_DATABASE)

@app.route('/api/crop/<crop_name>', methods=['GET'])
def get_crop_details(crop_name):
    crop_info = CROP_DATABASE.get(crop_name)
    if not crop_info:
        return jsonify({"error": "Crop not found"}), 404
    return jsonify({"name": crop_name, **crop_info})

@app.route('/api/chat', methods=['POST'])
async def chat_assistant():
    try:
        data = request.json
        message = data.get('message', '').lower()
        user_id = data.get('userId', 'anonymous')
        
        # Enhanced responses based on crop data
        for crop in CROP_DATABASE.keys():
            if crop.lower() in message:
                crop_info = CROP_DATABASE[crop]
                response = f"""For {crop} cultivation:
• Season: {crop_info['season']}
• Water Need: {crop_info['water_need']}
• Duration: {crop_info['duration']}
• Ideal Soil: {crop_info['ideal_soil']}
• Risk Level: {crop_info['risk']}
• Special Notes: {crop_info['special_notes']}
Optimal fertilizer: {crop_info['optimal_fertilizer']} tons, Water: {crop_info['optimal_water']}m³"""
                
                # Store chat message
                if oracle_pool:
                    await store_chat_message(user_id, message, response, 'crop_info')
                
                return jsonify({"response": response})
        
        # General farming advice
        response = """I can provide detailed farming advice! Ask me about:
• Specific crops (Rice, Wheat, Maize, Cotton, Sugarcane)
• Soil preparation techniques
• Irrigation methods
• Pest management
• Yield optimization
Just mention a crop name or ask a specific question!"""
        
        # Store chat message
        if oracle_pool:
            await store_chat_message(user_id, message, response, 'general')
        
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Database storage endpoints
@app.route('/api/store-crop-recommendation', methods=['POST'])
async def api_store_crop_recommendation():
    try:
        data = request.json
        user_id = data.get('userId')
        form_data = data.get('formData')
        recommendations = data.get('recommendations')
        weather_data = data.get('weather')
        
        if not all([user_id, form_data, recommendations]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = await store_crop_recommendation(user_id, form_data, recommendations, weather_data)
        
        return jsonify({
            "success": success,
            "message": "Crop recommendation stored successfully" if success else "Failed to store crop recommendation"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/store-yield-prediction', methods=['POST'])
async def api_store_yield_prediction():
    try:
        data = request.json
        user_id = data.get('userId')
        form_data = data.get('formData')
        prediction = data.get('prediction')
        
        if not all([user_id, form_data, prediction]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = await store_yield_prediction(user_id, form_data, prediction)
        
        return jsonify({
            "success": success,
            "message": "Yield prediction stored successfully" if success else "Failed to store yield prediction"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/store-chat-message', methods=['POST'])
async def api_store_chat_message():
    try:
        data = request.json
        user_id = data.get('userId')
        user_message = data.get('userMessage')
        assistant_response = data.get('assistantResponse')
        source = data.get('source', 'chat')
        
        if not all([user_id, user_message, assistant_response]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = await store_chat_message(user_id, user_message, assistant_response, source)
        
        return jsonify({
            "success": success,
            "message": "Chat message stored successfully" if success else "Failed to store chat message"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/store-batch-processing', methods=['POST'])
async def api_store_batch_processing():
    try:
        data = request.json
        user_id = data.get('userId')
        file_info = data.get('fileInfo')
        process_type = data.get('processType')
        results = data.get('results')
        
        if not all([user_id, file_info, process_type, results]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = await store_batch_processing(user_id, file_info, process_type, results)
        
        return jsonify({
            "success": success,
            "message": "Batch processing stored successfully" if success else "Failed to store batch processing"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/store-favorite', methods=['POST'])
async def api_store_favorite():
    try:
        data = request.json
        user_id = data.get('userId')
        crop_name = data.get('cropName')
        category = data.get('category', 'crops')
        
        if not all([user_id, crop_name]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = await store_user_favorite(user_id, crop_name, category)
        
        return jsonify({
            "success": success,
            "message": "Favorite stored successfully" if success else "Failed to store favorite"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/remove-favorite', methods=['DELETE'])
async def api_remove_favorite():
    try:
        data = request.json
        user_id = data.get('userId')
        crop_name = data.get('cropName')
        
        if not all([user_id, crop_name]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = await remove_user_favorite(user_id, crop_name)
        
        return jsonify({
            "success": success,
            "message": "Favorite removed successfully" if success else "Failed to remove favorite"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
print("🚀 Initializing Agriculture Backend...")
clf, reg, meta = load_models()
init_oracle_pool()
if __name__ == '__main__':
    print("\n🌾 Agriculture Backend Server - REAL ALGORITHM")
    print("📍 Endpoints available at:")
    print("   http://localhost:8000")
    print("   http://127.0.0.1:8000")
    print("\n📊 Status:", "✅ ML Models Loaded" if clf and reg else "✅ Real Algorithm Ready")
    print("🗄️  Database:", "✅ Oracle Connected" if oracle_pool else "❌ Oracle Not Connected")
    print("🌱 Supported Crops:", list(CROP_DATABASE.keys()))
    app.run(debug=True, host='0.0.0.0', port=8000)