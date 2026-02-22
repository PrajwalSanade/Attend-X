# Uvicorn Setup Guide

## What Changed

The backend has been migrated from Flask to FastAPI with Uvicorn for better performance and modern async support.

### Key Changes:
- **Flask → FastAPI**: Modern async framework with automatic API documentation
- **Flask-CORS → FastAPI CORS Middleware**: Built-in CORS support
- **@app.route → @app.post/@app.get**: FastAPI decorators
- **request.get_json() → Pydantic models**: Type-safe request validation
- **jsonify() → return dict**: FastAPI handles JSON serialization automatically

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Running the Server

### Development Mode (with auto-reload)
```bash
# Option 1: Using the start script
python start.py

# Option 2: Direct uvicorn command
uvicorn app:app --host 0.0.0.0 --port 5000 --reload

# Option 3: Using the app directly
python app.py
```

### Production Mode (with multiple workers)
```bash
# Option 1: Using the production script
python start_production.py

# Option 2: Direct uvicorn command with workers
uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4
```

## Environment Variables

- `PORT`: Server port (default: 5000)
- `WORKERS`: Number of worker processes for production (default: 4)

## API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc
- **OpenAPI JSON**: http://localhost:5000/openapi.json

## Benefits of FastAPI + Uvicorn

1. **Performance**: 2-3x faster than Flask
2. **Async Support**: Native async/await for better concurrency
3. **Type Safety**: Pydantic models validate requests automatically
4. **Auto Documentation**: Interactive API docs out of the box
5. **Modern Standards**: Built on ASGI standard (vs WSGI)
6. **Better Error Handling**: Automatic validation errors with clear messages

## Testing the Migration

All endpoints remain the same:
- `POST /register_face` or `/register-face`
- `POST /verify_face` or `/verify-face`
- `POST /mark_attendance` or `/mark-attendance`
- `POST /delete_face` or `/delete-face`
- `POST /export_attendance`
- `GET /health`

No frontend changes required!

## Troubleshooting

### Port already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### Import errors
Make sure you're in the backend directory and virtual environment is activated:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## Performance Tips

1. **Use workers in production**: Set `WORKERS=4` or more based on CPU cores
2. **Enable access logs**: Already enabled in production script
3. **Use a reverse proxy**: Nginx or Caddy in front of Uvicorn
4. **Monitor with tools**: Use Prometheus + Grafana for metrics
