"""
Data validation schemas and utilities
"""
from marshmallow import Schema, fields, ValidationError, validate, pre_load

class YieldPredictionSchema(Schema):
    """Validation schema for yield prediction"""
    cropType = fields.Str(required=True, validate=validate.OneOf([
        'Rice', 'Wheat', 'Maize', 'Cotton', 'Sugarcane'
    ]))
    farmArea = fields.Float(required=True, validate=validate.Range(min=0.1, max=1000))
    region = fields.Str(validate=validate.OneOf([
        'North', 'South', 'East', 'West', 'Central'
    ]))
    season = fields.Str(validate=validate.OneOf([
        'Kharif', 'Rabi', 'Zaid', 'Whole Year'
    ]))
    soilType = fields.Str(validate=validate.OneOf([
        'Loamy', 'Sandy', 'Clay', 'Alluvial', 'Black', 'Red'
    ]))
    soilPh = fields.Float(validate=validate.Range(min=4, max=9))
    soilMoisture = fields.Float(validate=validate.Range(min=0, max=100))
    organicContent = fields.Float(validate=validate.Range(min=0, max=10))
    irrigationType = fields.Str(validate=validate.OneOf([
        'Canal', 'Tube-well', 'Rain-fed', 'Drip', 'Sprinkler'
    ]))
    waterUsage = fields.Integer(validate=validate.Range(min=0, max=20000))
    waterQuality = fields.Str(validate=validate.OneOf([
        'Poor', 'Average', 'Good', 'Excellent'
    ]))
    rainfallExpected = fields.Float(validate=validate.Range(min=0, max=5000))
    fertilizer = fields.Float(validate=validate.Range(min=0, max=10))
    pesticide = fields.Float(validate=validate.Range(min=0, max=100))
    organicFertilizer = fields.Boolean()
    ipmApproach = fields.Boolean()
    experienceLevel = fields.Str(validate=validate.OneOf([
        'Beginner', 'Intermediate', 'Expert'
    ]))
    previousYield = fields.Float(validate=validate.Range(min=0, max=100))
    temperature = fields.Integer(validate=validate.Range(min=-10, max=50))
    humidity = fields.Integer(validate=validate.Range(min=0, max=100))
    sunlightHours = fields.Integer(validate=validate.Range(min=0, max=24))

class CropRecommendationSchema(Schema):
    """Validation schema for crop recommendation"""
    location = fields.Str(required=True)
    soilType = fields.Str(required=True, validate=validate.OneOf([
        'Loamy', 'Sandy', 'Clay', 'Alluvial', 'Black', 'Red', 'Laterite'
    ]))
    irrigationType = fields.Str(validate=validate.OneOf([
        'Canal', 'Tube-well', 'Rain-fed', 'Drip', 'Sprinkler'
    ]))
    waterAvailability = fields.Str(validate=validate.OneOf([
        'Low', 'Medium', 'High'
    ]))
    season = fields.Str(validate=validate.OneOf([
        'Kharif', 'Rabi', 'Zaid', 'Whole Year'
    ]))
    budget = fields.Float(required=True, validate=validate.Range(min=1000))
    riskTolerance = fields.Str(validate=validate.OneOf([
        'Low', 'Medium', 'High'
    ]))
    laborAvailability = fields.Str(validate=validate.OneOf([
        'Low', 'Medium', 'High'
    ]))
    farmArea = fields.Float(validate=validate.Range(min=0.1, max=1000))
    organicFarming = fields.Boolean()

class ChatMessageSchema(Schema):
    """Validation schema for chat messages"""
    user_id = fields.Str(required=True)
    message = fields.Str(required=True, validate=validate.Length(min=1, max=2000))
    context = fields.Dict()

class BatchProcessingSchema(Schema):
    """Validation schema for batch processing"""
    file_format = fields.Str(validate=validate.OneOf(['csv', 'xlsx']))
    batch_name = fields.Str(required=True)
    user_id = fields.Str(required=True)
    records = fields.List(fields.Dict(), required=True)

class Validator:
    """Centralized validation utilities"""
    
    def __init__(self):
        self.yield_schema = YieldPredictionSchema()
        self.recommendation_schema = CropRecommendationSchema()
        self.chat_schema = ChatMessageSchema()
        self.batch_schema = BatchProcessingSchema()
    
    def validate_yield_prediction(self, data):
        """Validate yield prediction data"""
        try:
            return self.yield_schema.load(data), None
        except ValidationError as err:
            return None, err.messages
    
    def validate_crop_recommendation(self, data):
        """Validate crop recommendation data"""
        try:
            return self.recommendation_schema.load(data), None
        except ValidationError as err:
            return None, err.messages
    
    def validate_chat_message(self, data):
        """Validate chat message"""
        try:
            return self.chat_schema.load(data), None
        except ValidationError as err:
            return None, err.messages
    
    def validate_batch_processing(self, data):
        """Validate batch processing data"""
        try:
            return self.batch_schema.load(data), None
        except ValidationError as err:
            return None, err.messages
