# Smart Agriculture Backend API

Modern, modular Python backend for the Smart Agriculture platform with crop recommendations and yield predictions.

## Features

- ✅ **ML-Powered Predictions**: Yield prediction and crop suitability assessment
- ✅ **Modular Architecture**: Separated concerns with config, database, models, and API layers
- ✅ **Oracle Database Integration**: Connection pooling for efficient data storage
- ✅ **Structured Logging**: JSON-formatted logs for monitoring and debugging
- ✅ **Data Validation**: Marshmallow schemas for input validation
- ✅ **Standardized API Responses**: Consistent response format across all endpoints
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Feature Flags**: Enable/disable features via environment variables
- ✅ **Production Ready**: Gunicorn support, CORS configuration, environment-based config

## Project Structure

```
Backend/
├── app.py                 # Main Flask application
├── config.py              # Configuration management
├── logger.py              # Logging utilities
├── database.py            # Database manager and operations
├── models_manager.py      # ML models management
├── validators.py          # Data validation schemas
├── api_responses.py       # Standardized response builders
├── requirements.txt       # Python dependencies
├── .env.example           # Environment configuration template
└── models/                # ML model files
    ├── suitability_pipeline.joblib
    ├── yield_pipeline.joblib
    └── metadata.json
```

## Setup & Installation

### 1. Prerequisites
- Python 3.8+
- Oracle Database (optional, can run without)
- pip

### 2. Install Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run the Backend

**Development:**
```bash
python app.py
```

**Production:**
```bash
gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
```

The API will be available at `https://agriculture-backend-o46d.onrender.com`

## API Endpoints

### Health & Status

- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `GET /api/status` - Detailed status

### Crop Database

- `GET /api/crop-database` - Get all crops
- `GET /api/crop/<crop_name>` - Get crop details

### Predictions & Recommendations

- `POST /api/predict-yield` - Predict crop yield
- `POST /api/recommendations` - Get crop recommendations
- `POST /api/chat` - Chat with farming assistant

## Configuration

### Environment Variables

```env
# Flask
FLASK_ENV=development|production|testing
SECRET_KEY=your-secret-key
DEBUG=True|False
PORT=8000
HOST=0.0.0.0

# Database
ORACLE_USER=username
ORACLE_PASSWORD=password
ORACLE_DSN=hostname:port/service
ORACLE_POOL_MIN=1
ORACLE_POOL_MAX=10

# Features
ENABLE_ORACLE=true|false
ENABLE_CACHE=true|false
ENABLE_ASYNC=false|true

# Logging
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_FILE=logs/backend.log
```

### Application Config

Edit `config.py` to customize:
- Database connections
- ML model paths
- Logging configuration
- Feature flags
- CORS settings

## Example Usage

### Yield Prediction

```bash
curl -X POST https://agriculture-backend-o46d.onrender.com/api/predict-yield \
  -H "Content-Type: application/json" \
  -d '{
    "cropType": "Wheat",
    "farmArea": 10,
    "soilType": "Loamy",
    "soilPh": 6.5,
    "waterUsage": 4000,
    "fertilizer": 2.0,
    "temperature": 25,
    "humidity": 65
  }'
```

### Crop Recommendations

```bash
curl -X POST https://agriculture-backend-o46d.onrender.com/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Punjab",
    "soilType": "Loamy",
    "season": "Kharif",
    "budget": 50000,
    "farmArea": 10
  }'
```

## Database Schema

The backend expects the following tables in Oracle Database:

```sql
CREATE TABLE crop_recommendations (
    recommendation_id VARCHAR2(50) PRIMARY KEY,
    user_id VARCHAR2(50),
    location VARCHAR2(100),
    soil_type VARCHAR2(50),
    irrigation_type VARCHAR2(50),
    water_availability VARCHAR2(50),
    season VARCHAR2(50),
    budget NUMBER,
    farm_area NUMBER,
    recommendations CLOB,
    weather_data CLOB,
    created_at TIMESTAMP DEFAULT SYSDATE
);

CREATE TABLE yield_predictions (
    prediction_id VARCHAR2(50) PRIMARY KEY,
    user_id VARCHAR2(50),
    crop_type VARCHAR2(50),
    farm_area NUMBER,
    soil_type VARCHAR2(50),
    soil_ph NUMBER,
    irrigation_type VARCHAR2(50),
    water_usage NUMBER,
    fertilizer NUMBER,
    predicted_yield NUMBER,
    confidence NUMBER,
    suitability VARCHAR2(50),
    recommendations CLOB,
    profitability_data CLOB,
    created_at TIMESTAMP DEFAULT SYSDATE
);

CREATE TABLE chat_messages (
    message_id VARCHAR2(50) PRIMARY KEY,
    user_id VARCHAR2(50),
    user_message CLOB,
    assistant_response CLOB,
    source VARCHAR2(50),
    created_at TIMESTAMP DEFAULT SYSDATE
);
```

## Logging

Logs are stored in `logs/backend.log` in JSON format for easy parsing and analysis.

**Example log entry:**
```json
{
  "timestamp": "2025-11-24T10:30:45.123456",
  "level": "INFO",
  "name": "app",
  "message": "Yield prediction stored",
  "prediction_id": "YP_abc123def456"
}
```

## Error Handling

All errors follow a standardized format:

```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-11-24T10:30:45.123456"
}
```

## Performance Tips

1. **Enable Caching**: Set `ENABLE_CACHE=true` to cache model predictions
2. **Connection Pooling**: Adjust `ORACLE_POOL_MAX` based on load
3. **Async Processing**: Enable `ENABLE_ASYNC=true` for long-running operations
4. **Production Server**: Use Gunicorn with multiple workers

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

## Troubleshooting

### Database Connection Failed
- Check Oracle DSN configuration
- Verify database is running and accessible
- Check credentials in `.env`

### Models Not Loaded
- Verify model files exist in `models/` directory
- Check file permissions
- See logs for detailed error messages

### CORS Errors
- Add frontend URL to `CORS_ORIGINS` in `.env`
- Check browser console for specific CORS headers

## Contributing

1. Follow PEP 8 style guide
2. Add logging for debugging
3. Include docstrings
4. Write tests for new features

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please refer to documentation or create an issue in the repository.
