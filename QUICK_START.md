# ⚡ AttendX Quick Start

## 🚀 One Command Setup

### Windows
```bash
start-dev.bat
```

### Linux/Mac
```bash
chmod +x start-dev.sh
./start-dev.sh
```

## 📍 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main application |
| Backend | http://localhost:5000 | API server |
| API Docs | http://localhost:5000/docs | Interactive API documentation |
| ReDoc | http://localhost:5000/redoc | Alternative API docs |

## 🔧 Manual Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
python start.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📦 What You Need

- Python 3.8+
- Node.js 16+
- Supabase account (free tier works!)
- Webcam for face recognition

## 🎯 First Time Setup

1. **Database**: Run `backend/FINAL_DATABASE_SETUP.sql` in Supabase SQL Editor
2. **Backend**: Install Python dependencies
3. **Frontend**: Install Node dependencies
4. **Run**: Use `start-dev.bat` or `start-dev.sh`

## 💡 Tips

- Backend auto-reloads on code changes
- Frontend has hot module replacement (HMR)
- Check browser console for frontend errors
- Check terminal for backend errors
- Use Chrome for best camera support

## 🆘 Common Issues

**Port already in use?**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

**Dependencies not installing?**
```bash
# Python
pip install --upgrade pip
pip install -r requirements.txt

# Node
npm cache clean --force
npm install
```

**Camera not working?**
- Use HTTPS or localhost
- Check browser permissions
- Try Chrome browser

## 📚 Documentation

- `README.md` - Full project documentation
- `backend/UVICORN_SETUP.md` - Backend setup guide
- `frontend/README.md` - Frontend setup guide
- `SETUP_GUIDE.html` - Visual setup guide (open in browser)

## 🎉 You're Ready!

Once both servers are running:
1. Open http://localhost:3000
2. Click "Admin Login"
3. Create an account or login
4. Start marking attendance!
