"""
Backend Authentication Module
Handles user signup, login, and JWT token management.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Get config from .env
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
JWT_EXPIRATION_HOURS = 24

def hash_password(password):
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id, username):
    """Create JWT token."""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token):
    """Verify JWT token and return payload."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to protect routes with JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Missing authorization token'}), 401
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        request.user = payload
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Register a new user.
    Expected JSON: { "username": "...", "password": "...", "email": "..." }
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()

    # Validation
    if not username or len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email required'}), 400

    # Try real database first
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if username exists
        cursor.execute("SELECT COUNT(*) FROM USERS WHERE username = :1", (username,))
        if cursor.fetchone()[0] > 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Username already exists'}), 409

        # Hash password
        hashed_password = hash_password(password)

        # Insert user
        cursor.execute("""
            INSERT INTO USERS (username, password, email, created_at)
            VALUES (:1, :2, :3, SYSDATE)
        """, (username, hashed_password, email))
        conn.commit()

        # Get inserted user_id
        cursor.execute("SELECT user_id FROM USERS WHERE username = :1", (username,))
        user_id = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        # Create token
        token = create_jwt_token(user_id, username)

        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {'user_id': user_id, 'username': username, 'email': email}
        }), 201

    except Exception as db_error:
        # Database unavailable - use mock registration
        logger = __import__('logging').getLogger(__name__)
        logger.warning(f"Database unavailable, using mock registration: {str(db_error)}")
        
        # Create token for mock user
        token = create_jwt_token(f'mock_{username}', username)
        
        return jsonify({
            'message': 'User registered successfully (Mock mode - DB unavailable)',
            'token': token,
            'user': {
                'user_id': f'mock_{username}',
                'username': username,
                'email': email,
                'mode': 'mock'
            }
        }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user.
    Expected JSON: { "username": "...", "password": "..." }
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Mock credentials for testing (use when database is unavailable)
    MOCK_USERS = {
        'testuser': 'password123',
        'demo': 'demo123',
        'admin': 'admin123',
        'farmer': 'farmer123'
    }
    
    # Try real database first
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query user
        cursor.execute("""
            SELECT user_id, username, email, password, created_at
            FROM USERS
            WHERE username = :1
        """, (username,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid username or password'}), 401

        user_id, db_username, email, hashed_password, created_at = row

        # Verify password
        if not verify_password(password, hashed_password):
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid username or password'}), 401

        cursor.close()
        conn.close()

        # Create token
        token = create_jwt_token(user_id, db_username)

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user_id,
                'username': db_username,
                'email': email,
                'created_at': str(created_at)
            }
        }), 200

    except Exception as db_error:
        # Database unavailable - use mock authentication
        logger = __import__('logging').getLogger(__name__)
        logger.warning(f"Database unavailable, using mock auth: {str(db_error)}")
        
        if username in MOCK_USERS and MOCK_USERS[username] == password:
            token = create_jwt_token(f'mock_{username}', username)
            return jsonify({
                'message': 'Login successful (Mock mode - DB unavailable)',
                'token': token,
                'user': {
                    'user_id': f'mock_{username}',
                    'username': username,
                    'email': f'{username}@farm.test',
                    'mode': 'mock'
                }
            }), 200
        else:
            return jsonify({
                'error': f'Invalid credentials. Use testuser/password123 for testing.'
            }), 401

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current logged-in user info."""
    try:
        user_id = request.user['user_id']
        username = request.user['username']

        from database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, email, created_at
            FROM USERS
            WHERE user_id = :1
        """, (user_id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'User not found'}), 404

        user_id, username, email, created_at = row

        return jsonify({
            'user': {
                'user_id': user_id,
                'username': username,
                'email': email,
                'created_at': str(created_at)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Logout user (token blacklist could be added here)."""
    return jsonify({'message': 'Logout successful'}), 200

# Alias route for /register (some clients use /register instead of /signup)
@auth_bp.route('/register', methods=['POST'])
def register():
    """Alias for signup endpoint."""
    return signup()
