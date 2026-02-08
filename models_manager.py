"""
Machine Learning models management
"""
import json
import joblib
from pathlib import Path
from functools import lru_cache
from logger import get_logger

logger = get_logger(__name__)

class ModelManager:
    """Manages ML models loading and caching"""
    
    def __init__(self, models_config):
        self.config = models_config
        self.suitability_model = None
        self.yield_model = None
        self.metadata = None
        self.loaded = False
    
    def load_models(self):
        """Load ML models from disk"""
        try:
            suitability_path = Path(self.config['suitability_model'])
            yield_path = Path(self.config['yield_model'])
            metadata_path = Path(self.config['metadata'])
            
            # Check if files exist
            if not suitability_path.exists():
                logger.warning("Suitability model not found", path=str(suitability_path))
                return False
            
            if not yield_path.exists():
                logger.warning("Yield model not found", path=str(yield_path))
                return False
            
            if not metadata_path.exists():
                logger.warning("Metadata file not found", path=str(metadata_path))
                return False
            
            # Load models
            self.suitability_model = joblib.load(suitability_path)
            self.yield_model = joblib.load(yield_path)
            self.metadata = json.loads(metadata_path.read_text())
            
            self.loaded = True
            logger.info("Models loaded successfully",
                       suitability_model=str(suitability_path),
                       yield_model=str(yield_path),
                       metadata=str(metadata_path))
            return True
            
        except Exception as e:
            logger.error("Failed to load models", error=str(e))
            return False
    
    def predict_suitability(self, features):
        """Predict crop suitability"""
        try:
            if not self.loaded:
                raise Exception("Models not loaded")
            prediction = self.suitability_model.predict([features])
            probability = self.suitability_model.predict_proba([features])
            
            return {
                'prediction': prediction[0],
                'probability': float(probability[0][1]),
                'confidence': float(max(probability[0]))
            }
        except Exception as e:
            logger.error("Failed to predict suitability", error=str(e))
            return None
    
    def predict_yield(self, features):
        """Predict crop yield"""
        try:
            if not self.loaded:
                raise Exception("Models not loaded")
            prediction = self.yield_model.predict([features])
            
            return {
                'predicted_yield': float(prediction[0]),
                'confidence': 0.85  # Can be enhanced with model uncertainty
            }
        except Exception as e:
            logger.error("Failed to predict yield", error=str(e))
            return None
    
    def get_feature_importance(self):
        """Get feature importance from models"""
        try:
            if not self.loaded:
                return None
            
            # Extract feature importance if available
            feature_importance = {}
            
            if hasattr(self.suitability_model, 'feature_importances_'):
                feature_importance['suitability'] = self.suitability_model.feature_importances_.tolist()
            
            if hasattr(self.yield_model, 'feature_importances_'):
                feature_importance['yield'] = self.yield_model.feature_importances_.tolist()
            
            return feature_importance if feature_importance else None
        except Exception as e:
            logger.error("Failed to get feature importance", error=str(e))
            return None
    
    def get_metadata(self):
        """Get model metadata"""
        return self.metadata
    
    def is_loaded(self):
        """Check if models are loaded"""
        return self.loaded
