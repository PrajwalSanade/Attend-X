"""
Uvicorn startup script for AttendX Backend
"""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Auto-reload on code changes (disable in production)
        log_level="info"
    )
