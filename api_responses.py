"""
Standardized API response utilities
"""
from flask import jsonify
from datetime import datetime

class APIResponse:
    """Standardized API response builder"""
    
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        """Return success response"""
        response = {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        return jsonify(response), status_code
    
    @staticmethod
    def error(message="Error", error_code=None, status_code=400):
        """Return error response"""
        response = {
            "status": "error",
            "message": message,
            "error_code": error_code,
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors, status_code=422):
        """Return validation error response"""
        response = {
            "status": "error",
            "message": "Validation failed",
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(response), status_code
    
    @staticmethod
    def not_found(message="Resource not found"):
        """Return 404 response"""
        return APIResponse.error(message, status_code=404)
    
    @staticmethod
    def unauthorized(message="Unauthorized"):
        """Return 401 response"""
        return APIResponse.error(message, status_code=401)
    
    @staticmethod
    def forbidden(message="Forbidden"):
        """Return 403 response"""
        return APIResponse.error(message, status_code=403)
    
    @staticmethod
    def server_error(message="Internal server error"):
        """Return 500 response"""
        return APIResponse.error(message, status_code=500)
    
    @staticmethod
    def paginated(data, total, page, per_page, message="Success"):
        """Return paginated response"""
        response = {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        }
        return jsonify(response), 200

class ErrorHandler:
    """Error handling utilities"""
    
    @staticmethod
    def handle_validation_error(errors):
        """Handle validation errors"""
        error_messages = {}
        for field, message in errors.items():
            if isinstance(message, list):
                error_messages[field] = message[0] if message else "Invalid value"
            else:
                error_messages[field] = str(message)
        return APIResponse.validation_error(error_messages)
    
    @staticmethod
    def handle_exception(e, logger=None):
        """Handle unexpected exceptions"""
        error_message = str(e)
        if logger:
            logger.error(f"Unexpected error: {error_message}", error=error_message)
        return APIResponse.server_error(error_message)
