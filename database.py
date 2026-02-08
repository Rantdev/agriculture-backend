"""
Database connection and operations module
"""
import json
import uuid
from datetime import datetime
from contextlib import contextmanager
import oracledb
from logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, config):
        self.config = config
        self.pool = None
    
    def init_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = oracledb.create_pool(
                user=self.config['user'],
                password=self.config['password'],
                dsn=self.config['dsn'],
                min=self.config['min'],
                max=self.config['max'],
                increment=self.config['increment']
            )
            logger.info("Oracle Database connection pool initialized", status="success")
            return True
        except Exception as e:
            logger.error("Failed to initialize database pool", error=str(e))
            return False
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            if not self.pool:
                raise Exception("Database pool not initialized")
            connection = self.pool.acquire()
            yield connection
        except Exception as e:
            logger.error("Database connection error", error=str(e))
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                try:
                    self.pool.release(connection)
                except Exception as e:
                    logger.error("Error releasing connection", error=str(e))
    
    def store_crop_recommendation(self, user_id, form_data, recommendations, weather_data=None):
        """Store crop recommendation in database"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                recommendation_id = f"CR_{uuid.uuid4().hex[:16]}"
                
                cursor.execute("""
                    INSERT INTO crop_recommendations (
                        recommendation_id, user_id, location, soil_type, irrigation_type,
                        water_availability, season, budget, farm_area, recommendations,
                        weather_data, created_at
                    ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12)
                """, (
                    recommendation_id, user_id, form_data.get('location'),
                    form_data.get('soilType'), form_data.get('irrigationType'),
                    form_data.get('waterAvailability'), form_data.get('season'),
                    form_data.get('budget'), form_data.get('farmArea'),
                    json.dumps(recommendations),
                    json.dumps(weather_data) if weather_data else None,
                    datetime.now()
                ))
                connection.commit()
                logger.info("Crop recommendation stored", recommendation_id=recommendation_id)
                return True
        except Exception as e:
            logger.error("Failed to store crop recommendation", error=str(e))
            return False
    
    def store_yield_prediction(self, user_id, form_data, prediction):
        """Store yield prediction in database"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                prediction_id = f"YP_{uuid.uuid4().hex[:16]}"
                
                cursor.execute("""
                    INSERT INTO yield_predictions (
                        prediction_id, user_id, crop_type, farm_area, soil_type, soil_ph,
                        irrigation_type, water_usage, fertilizer, predicted_yield, confidence,
                        suitability, recommendations, profitability_data, created_at
                    ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15)
                """, (
                    prediction_id, user_id, form_data.get('cropType'),
                    form_data.get('farmArea'), form_data.get('soilType'),
                    form_data.get('soilPh'), form_data.get('irrigationType'),
                    form_data.get('waterUsage'), form_data.get('fertilizer'),
                    prediction.get('predicted_yield'), prediction.get('confidence'),
                    prediction.get('suitability'),
                    json.dumps(prediction.get('recommendations', [])),
                    json.dumps(prediction.get('profitability', {})),
                    datetime.now()
                ))
                connection.commit()
                logger.info("Yield prediction stored", prediction_id=prediction_id)
                return True
        except Exception as e:
            logger.error("Failed to store yield prediction", error=str(e))
            return False
    
    def store_chat_message(self, user_id, user_message, assistant_response, source):
        """Store chat message in database"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                message_id = f"MSG_{uuid.uuid4().hex[:16]}"
                
                cursor.execute("""
                    INSERT INTO chat_messages (
                        message_id, user_id, user_message, assistant_response,
                        source, created_at
                    ) VALUES (:1, :2, :3, :4, :5, :6)
                """, (
                    message_id, user_id, user_message,
                    assistant_response, source, datetime.now()
                ))
                connection.commit()
                logger.info("Chat message stored", message_id=message_id)
                return True
        except Exception as e:
            logger.error("Failed to store chat message", error=str(e))
            return False
    
    def get_user_predictions(self, user_id, limit=10):
        """Retrieve user's recent predictions"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT * FROM yield_predictions
                    WHERE user_id = :1
                    ORDER BY created_at DESC
                    FETCH FIRST :2 ROWS ONLY
                """, (user_id, limit))
                
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
        except Exception as e:
            logger.error("Failed to retrieve user predictions", error=str(e))
            return []
    
    def get_user_recommendations(self, user_id, limit=10):
        """Retrieve user's recent recommendations"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT * FROM crop_recommendations
                    WHERE user_id = :1
                    ORDER BY created_at DESC
                    FETCH FIRST :2 ROWS ONLY
                """, (user_id, limit))
                
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
        except Exception as e:
            logger.error("Failed to retrieve user recommendations", error=str(e))
            return []
