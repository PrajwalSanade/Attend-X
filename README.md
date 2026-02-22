# Attend-X - Face Recognition Attendance System

A production-ready face attendance system with multi-admin data isolation, face recognition (72% confidence threshold), and secure attendance management.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![Node](https://img.shields.io/badge/Node-16+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 👤 **Multi-Admin Isolation** - Each admin manages their own students
- 🎯 **Face Recognition** - 72% confidence threshold for accurate verification
- 🔒 **Secure Authentication** - JWT-based admin auth, face-based student auth
- 📊 **Real-time Dashboard** - Live attendance tracking and statistics
- 📱 **Responsive Design** - Works on desktop and mobile
- 🌓 **Dark/Light Theme** - User preference support
- 📥 **Export Data** - CSV and PDF export functionality
- 🔄 **Auto-reload** - Hot reload for development

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Supabase account (free tier)
- Webcam

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd attend-x

# Setup database (see docs/SETUP.md)
# Run backend/FINAL_DATABASE_SETUP.sql in Supabase

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # Edit with your Supabase credentials

# Frontend setup
cd ../frontend
npm install

# Run application
cd ..
./start-dev.sh  # or start-dev.bat on Windows
```

### Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Docs: http://localhost:5000/docs

## 📖 Documentation

- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [Complete Setup](docs/SETUP.md) - Detailed setup instructions
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [API Documentation](http://localhost:5000/docs) - Interactive API docs (when running)

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **Uvicorn** - Lightning-fast ASGI server
- **face_recognition** - Face detection and recognition
- **Supabase** - Database and authentication
- **OpenCV** - Image processing

### Frontend
- **Vite** - Next-generation frontend tooling
- **face-api.js** - Browser-based face detection
- **Vanilla JavaScript** - No framework overhead
- **Supabase Client** - Real-time database access

## 📁 Project Structure

```
attend-x/
├── backend/              # FastAPI backend
│   ├── app.py           # Main application
│   ├── *_service.py     # Service modules
│   ├── requirements.txt # Python dependencies
│   └── *.sql            # Database scripts
├── frontend/             # Vite frontend
│   ├── *.html           # Pages
│   ├── *.js             # Scripts
│   ├── package.json     # Node dependencies
│   └── models/          # Face-api.js models
├── docs/                 # Documentation
├── README.md            # This file
└── QUICK_START.md       # Quick start guide
```

## 🔧 Development

```bash
# Backend (with auto-reload)
cd backend
python start.py

# Frontend (with HMR)
cd frontend
npm run dev

# Run tests
cd backend
python test_auth_toggle.py
```

## 🚦 Production Deployment

### Backend
```bash
cd backend
python start_production.py
# Or with Gunicorn
gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Frontend
```bash
cd frontend
npm run build
# Deploy dist/ folder to Netlify, Vercel, or any static hosting
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [face_recognition](https://github.com/ageitgey/face_recognition) - Face recognition library
- [face-api.js](https://github.com/justadudewhohacks/face-api.js) - Browser face detection
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Supabase](https://supabase.com/) - Open source Firebase alternative

## 📧 Support

For issues and questions:
- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Open an issue on GitHub
- Review [Setup Documentation](docs/SETUP.md)

---

**Made with ❤️ for efficient attendance management**

## 🚀 Quick Start

### Option 1: Run Everything at Once (Recommended)

**Windows:**
```bash
start-dev.bat
```

**Linux/Mac:**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

This will start both backend (port 5000) and frontend (port 3000) automatically!

### Option 2: Manual Setup

1.  **Database Setup** (Crucial - Do this first!)
    - Go to Supabase SQL Editor
    - Run the main setup script: `backend/FINAL_DATABASE_SETUP.sql`
    - Run the system settings script: `backend/create_system_settings.sql`
    - This sets up tables, RLS policies, triggers, and student auth toggle

2.  **Backend Setup**
    - Navigate to `backend/`
    - Create a `.env` file with your credentials (optional, falls back to defaults):
      ```env
      SUPABASE_URL=YOUR_URL
      SUPABASE_KEY=YOUR_SERVICE_ROLE_KEY
      ```
    - Install dependencies:
      ```bash
      pip install -r requirements.txt
      ```
    - Run the server:
      ```bash
      python start.py
      ```
    - Backend will be available at `http://localhost:5000`
    - API docs at `http://localhost:5000/docs`

3.  **Frontend Setup**
    - Navigate to `frontend/`
    - Install dependencies:
      ```bash
      npm install
      ```
    - Run development server:
      ```bash
      npm run dev
      ```
    - Frontend will open at `http://localhost:3000`

## 📄 Documentation

Comprehensive documentation available:
- **Backend Setup**: `backend/UVICORN_SETUP.md` - FastAPI + Uvicorn configuration
- **Frontend Setup**: `frontend/README.md` - Vite development server setup
- **Final Setup PDF**: `backend/final_setup.pdf` - Full system documentation
- **API Documentation**: `http://localhost:5000/docs` (when backend is running)

## 🔑 Key Features
- **Multi-Admin Isolation**: Admins can only see their own students
- **Strict Face Matching**: Using 0.55 distance threshold (72% confidence)
- **Secure Attendance**: Marking logic moved to backend `/mark_attendance`
- **Clean Code**: Modular services (`face_service`, `auth_service`, etc.)
- **Modern Stack**: FastAPI + Uvicorn backend, Vite frontend dev server
- **Auto Documentation**: Interactive API docs with Swagger UI
- **Hot Reload**: Both frontend and backend support live reloading

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern async Python web framework
- **Uvicorn**: Lightning-fast ASGI server
- **face_recognition**: Face detection and recognition
- **Supabase**: Database and authentication
- **OpenCV**: Image processing

### Frontend
- **Vite**: Next-generation frontend tooling
- **face-api.js**: Browser-based face detection
- **Vanilla JavaScript**: No framework overhead
- **Supabase Client**: Real-time database access

## 📦 Project Structure

```
attend-x/
├── backend/
│   ├── app.py                    # FastAPI application
│   ├── start.py                  # Development server
│   ├── start_production.py       # Production server
│   ├── face_service.py           # Face recognition logic
│   ├── auth_service.py           # Authentication
│   ├── attendance_service.py     # Attendance marking
│   ├── database_service.py       # Supabase client
│   ├── requirements.txt          # Python dependencies
│   └── UVICORN_SETUP.md         # Backend documentation
├── frontend/
│   ├── startup.html              # Landing page
│   ├── login.html                # Admin login
│   ├── index.html                # Main app
│   ├── package.json              # Node dependencies
│   ├── vite.config.js            # Vite configuration
│   └── README.md                 # Frontend documentation
├── start-dev.bat                 # Windows dev launcher
├── start-dev.sh                  # Linux/Mac dev launcher
└── README.md                     # This file
```

## 🚦 Available Commands

### Backend
```bash
cd backend
python start.py              # Development with auto-reload
python start_production.py   # Production with workers
python fix_encodings.py      # Check face encoding integrity
```

### Frontend
```bash
cd frontend
npm run dev      # Development server (port 3000)
npm run build    # Production build
npm run preview  # Preview production build
```

## 🔧 Troubleshooting

### Backend won't start
- Check if port 5000 is available
- Verify Python dependencies: `pip install -r requirements.txt`
- Check `.env` file for correct Supabase credentials

### Frontend won't start
- Install Node.js (v16 or higher)
- Run `npm install` in frontend directory
- Check if port 3000 is available

### Face verification errors
- Run `python backend/fix_encodings.py` to check encoding integrity
- Re-register affected students
- Check backend logs for detailed error messages

### Camera not working
- Ensure HTTPS or localhost (required for camera access)
- Check browser permissions
- Try a different browser (Chrome recommended)

### Student Authentication toggle not working
- Run `backend/create_system_settings.sql` in Supabase SQL Editor
- Test with `python backend/test_auth_toggle.py`
- Check browser console for errors
- See `STUDENT_AUTH_TOGGLE_FIX.md` for details
