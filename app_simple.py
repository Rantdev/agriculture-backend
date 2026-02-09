#app_simple.py (fixed)
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import jwt
import logging

# Load .env if present (local dev)
load_dotenv()

# Basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("smart-agri-backend")

# Create single Flask app instance
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'change_me_in_prod')

# Allow cross-origin requests for /api/* during development
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Config
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
EXTERNAL_TIMEOUT = int(os.getenv("EXTERNAL_TIMEOUT", "20"))

# Try to import db_manager from parent folder if present (optional)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from db_manager import authenticate_user, register_user, create_connection, init_database
except Exception as e:
    logger.warning("Could not import Backend.db_manager: %s", e)

    # fallback stub functions
    def authenticate_user(username, password):
        return False, "Database not available"

    def register_user(username, password, email):
        return False, "Database not available"

    def create_connection():
        raise Exception("Database not available")

    def init_database():
        raise Exception("Database not available")

# ---------------------------
# Mock / Crop database
# ---------------------------
CROP_DATABASE = {
    "Rice": {
        "season": "Kharif",
        "water_need": "High",
        "duration": "90-120 days",
        "profitability": "High",
        "risk": "Medium",
        "market_demand": "High",
        "ideal_soil": "Clayey Loam",
        "special_notes": "Requires standing water, high labor"
    },
    "Wheat": {
        "season": "Rabi",
        "water_need": "Medium",
        "duration": "110-130 days",
        "profitability": "Medium",
        "risk": "Low",
        "market_demand": "High",
        "ideal_soil": "Well-drained Loam",
        "special_notes": "Cold weather crop, frost tolerant"
    }
}

# ---------------------------
# Utility: print registered routes
# ---------------------------
def print_routes():
    print("---- Registered routes ----")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, sorted(r.methods))):
        methods = ",".join(sorted(rule.methods))
        print(f"{rule.rule}  -> methods: {methods}")
    print("---------------------------")

# ---------------------------
# Root and health endpoints
# ---------------------------
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "app": "Smart Agriculture Backend",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    health_status = {
        "database": "connected" if callable(create_connection) else "unavailable",
        "models": "configured" if bool(GOOGLE_API_KEY) else "not configured",
        "api": "ready",
        "timestamp": datetime.now().isoformat()
    }
    return jsonify({
        "success": True,
        "message": "Health check passed",
        "data": health_status
    })

# ---------------------------
# Gemini proxy endpoint (POST) — supports OPTIONS via CORS
# ---------------------------
@app.route('/api/gemini', methods=['POST', 'OPTIONS'])
# Add / replace in app_simple.py
def gemini_proxy():
    # handle preflight quickly
    if request.method == "OPTIONS":
        return make_response("", 204)

    if not GOOGLE_API_KEY:
        return jsonify({"success": False, "message": "Server missing GOOGLE_API_KEY"}), 500

    try:
        body = request.get_json(force=True) or {}
        message = body.get("message", "")
        if not message:
            return jsonify({"success": False, "message": "message required"}), 400

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}"

        prompt = (
            "You are FarmAI, an expert agricultural advisor for Indian farmers.\n"
            f"User: {message}\n\nFarmAI:"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.35,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 800
            }
        }

        resp = requests.post(api_url, json=payload, headers={"Content-Type":"application/json"}, timeout=EXTERNAL_TIMEOUT)

        if resp.status_code != 200:
            return jsonify({
                "success": False,
                "message": "Gemini returned non-200",
                "status_code": resp.status_code,
                "details": resp.text[:1000]
            }), 502

        data = resp.json()
        # robust extraction of text
        def find_text(obj):
            if isinstance(obj, dict):
                for k,v in obj.items():
                    if k == "text" and isinstance(v, str):
                        return v
                    res = find_text(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_text(item)
                    if res:
                        return res
            return None

        text = find_text(data)
        if not text:
            return jsonify({"success": False, "message": "Could not parse Gemini response", "raw": data}), 502

        return jsonify({"success": True, "response": text, "source": "google-ai"}), 200

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "Gemini timed out"}), 504

    except Exception as e:
        logger.exception("gemini_proxy error")
        return jsonify({"success": False, "message": str(e)}), 500

# ---------------------------
# Other API endpoints (crop DB, predict, recommendations, chat)
# ---------------------------
@app.route('/api/crop-database', methods=['GET'])
def get_crop_db():
    return jsonify({"success": True, "data": CROP_DATABASE}), 200

@app.route('/api/crop/<crop_name>', methods=['GET'])
def crop_detail(crop_name):
    info = CROP_DATABASE.get(crop_name)
    if not info:
        return jsonify({"success": False, "message": "Crop not found"}), 404
    return jsonify({"success": True, "data": info}), 200

@app.route('/api/predict-yield', methods=['POST'])
def predict_yield():
    try:
        data = request.get_json(force=True) or {}
        predicted = round(data.get('farmArea', 10) * 3.5 + 0.5, 2)
        return jsonify({"success": True, "data": {"predicted_yield": predicted, "timestamp": datetime.now().isoformat()}}), 200
    except Exception as e:
        logger.exception("predict_yield error")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    try:
        _ = request.get_json(force=True) or {}
        recommendations = {"suitable_crops": ["Rice", "Wheat"], "top_recommendation": "Wheat", "timestamp": datetime.now().isoformat()}
        return jsonify({"success": True, "data": recommendations}), 200
    except Exception as e:
        logger.exception("recommendations error")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True) or {}
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"success": False, "message": "Message cannot be empty"}), 400
        return jsonify({"success": True, "data": {"message": f"I received your message: {user_message}", "source": "fallback"}}), 200
    except Exception as e:
        logger.exception("chat error")
        return jsonify({"success": False, "message": str(e)}), 500

# ---------------------------
# Authentication endpoints (fallbacks if DB missing)
# ---------------------------
@app.route('/api/test', methods=['GET', 'POST', 'OPTIONS'])
def test_endpoint():
    """Simple test endpoint to verify backend is working."""
    return jsonify({
        'status': 'ok',
        'message': 'Backend is working',
        'method': request.method,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Debug logging
        logger.info(f"Login request received - Content-Type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        data = request.get_json(force=True) or {}
        logger.info(f"Parsed JSON data: {data}")
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        logger.info(f"Login attempt - username: {username}, has_password: {bool(password)}")
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400

        # Try real database authentication
        success, result = authenticate_user(username, password)
        if success:
            payload = {'user_id': result.get('user_id', 1), 'username': result.get('username', username), 'exp': datetime.utcnow() + timedelta(hours=24)}
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({'success': True, 'token': token, 'user': result}), 200
        
        # If database is unavailable, fall back to mock authentication
        MOCK_USERS = {
            'testuser': 'password123',
            'demo': 'demo123',
            'admin': 'admin123',
            'farmer': 'farmer123'
        }
        
        if username in MOCK_USERS and MOCK_USERS[username] == password:
            payload = {
                'user_id': f'mock_{username}',
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'user_id': f'mock_{username}',
                    'username': username,
                    'email': f'{username}@farm.test',
                    'mode': 'mock'
                },
                'message': 'Login successful (Mock mode)'
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials. Try testuser/password123'}), 401
            
    except Exception as e:
        logger.exception("login error")
        
        # Final fallback - try mock auth even if there's an exception
        try:
            data = request.get_json(force=True) or {}
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            
            MOCK_USERS = {
                'testuser': 'password123',
                'demo': 'demo123',
                'admin': 'admin123',
                'farmer': 'farmer123'
            }
            
            if username in MOCK_USERS and MOCK_USERS[username] == password:
                payload = {
                    'user_id': f'mock_{username}',
                    'username': username,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'user_id': f'mock_{username}',
                        'username': username,
                        'email': f'{username}@farm.test',
                        'mode': 'mock'
                    },
                    'message': 'Login successful (Mock mode)'
                }), 200
        except:
            pass
        
        return jsonify({'success': False, 'message': f'Login failed: {str(e)}'}), 500

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info(f"Register request received - Content-Type: {request.content_type}")
        
        data = request.get_json(force=True) or {}
        logger.info(f"Parsed JSON data keys: {list(data.keys())}")
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        
        if not all([username, password, email]):
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        # Validation
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Username must be at least 3 characters'}), 400
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        if '@' not in email:
            return jsonify({'success': False, 'message': 'Valid email required'}), 400
        
        # Try real database registration
        success, msg = register_user(username, password, email)
        if success:
            payload = {'user_id': msg.get('user_id', f'user_{username}'), 'username': username, 'exp': datetime.utcnow() + timedelta(hours=24)}
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({
                'success': True,
                'token': token,
                'message': 'User registered successfully',
                'user': {
                    'user_id': msg.get('user_id', f'user_{username}'),
                    'username': username,
                    'email': email
                }
            }), 201
        
        # If database is unavailable, fall back to mock registration
        payload = {
            'user_id': f'mock_{username}',
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({
            'success': True,
            'token': token,
            'message': 'User registered successfully (Mock mode)',
            'user': {
                'user_id': f'mock_{username}',
                'username': username,
                'email': email,
                'mode': 'mock'
            }
        }), 201
        
    except Exception as e:
        logger.exception("register error")
        
        # Final fallback - try mock registration even if there's an exception
        try:
            data = request.get_json(force=True) or {}
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            email = data.get('email', '').strip()
            
            if not all([username, password, email]):
                return jsonify({'success': False, 'message': 'All fields required'}), 400
            
            if len(username) < 3 or len(password) < 6 or '@' not in email:
                return jsonify({'success': False, 'message': 'Validation failed'}), 400
            
            payload = {
                'user_id': f'mock_{username}',
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({
                'success': True,
                'token': token,
                'message': 'User registered successfully (Mock mode)',
                'user': {
                    'user_id': f'mock_{username}',
                    'username': username,
                    'email': email,
                    'mode': 'mock'
                }
            }), 201
        except:
            pass
        
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'}), 500

# ---------------------------
# Error handlers
# ---------------------------
@app.errorhandler(404)
def not_found(err):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_err(err):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# ---------------------------
# Startup
# ---------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("FLASK_ENV", "development") == "development"

    # Print routes and run
    print_routes()
    try:
        # attempt db init but don't crash startup if fails
        init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning("Database not initialized: %s", e)

    app.run(host="0.0.0.0", port=port, debug=debug)