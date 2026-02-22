# Complete Setup Guide

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- Supabase account (free tier works)
- Webcam for face recognition

---

## Quick Setup (5 Minutes)

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd attend-x
```

### 2. Database Setup
1. Create a Supabase project at https://supabase.com
2. Go to SQL Editor
3. Run `backend/FINAL_DATABASE_SETUP.sql`
4. Run `backend/create_system_settings.sql`

### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env with your Supabase credentials
```

### 4. Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install
```

### 5. Run Application
```bash
cd ..

# Windows
start-dev.bat

# Linux/Mac
chmod +x start-dev.sh
./start-dev.sh
```

### 6. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Docs: http://localhost:5000/docs

---

## Detailed Setup

### Database Configuration

#### Tables Created:
- `admins` - Admin user profiles
- `students` - Student information
- `face_encodings` - Face recognition data
- `attendance` - Attendance records
- `system_settings` - System configuration

#### Verify Setup:
```sql
-- Check all tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check system settings
SELECT * FROM system_settings;
```

### Backend Configuration

#### Environment Variables:
Edit `backend/.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
PORT=5000
```

#### Test Backend:
```bash
cd backend
python start.py
```

Should see:
```
INFO:     Uvicorn running on http://0.0.0.0:5000
INFO:     Application startup complete
```

### Frontend Configuration

#### Supabase Client:
Edit `frontend/supabaseClient.js` if needed:
```javascript
const supabaseUrl = 'your-project-url';
const supabaseKey = 'your-anon-key';
```

#### Test Frontend:
```bash
cd frontend
npm run dev
```

Should see:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

---

## First Time Usage

### 1. Create Admin Account
1. Open http://localhost:3000
2. Click "Create Admin Account" tab
3. Fill in details:
   - Name
   - Email
   - Password (min 6 characters)
   - College name
4. Click "Create Admin Account"
5. Check email for verification link
6. Click verification link
7. Return to app and login

### 2. Add Students
1. Login as admin
2. Click "Add New Student"
3. Fill in:
   - Student name
   - Roll number
4. Take photo or upload
5. Click "Add Student"

### 3. Mark Attendance
1. Student opens app
2. Clicks "Student Login"
3. Enters roll number
4. Clicks "Mark Attendance"
5. Captures face photo
6. System verifies and marks attendance

---

## Development

### Backend Development
```bash
cd backend
python start.py  # Auto-reload enabled
```

### Frontend Development
```bash
cd frontend
npm run dev  # Hot module replacement
```

### Run Tests
```bash
cd backend
python test_auth_toggle.py
python test_services.py
```

---

## Production Deployment

### Backend
```bash
cd backend
python start_production.py
```

Or with Gunicorn:
```bash
gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Frontend
```bash
cd frontend
npm run build
```

Deploy `dist/` folder to:
- Netlify
- Vercel
- GitHub Pages
- Any static hosting

---

## Environment Variables

### Backend (.env)
```env
SUPABASE_URL=required
SUPABASE_KEY=required
PORT=5000
WORKERS=4
ENVIRONMENT=production
```

### Frontend
Update `frontend/supabaseClient.js` with production URLs.

---

## Troubleshooting

See `docs/TROUBLESHOOTING.md` for common issues and solutions.

---

## Project Structure

```
attend-x/
├── backend/          # FastAPI backend
│   ├── app.py       # Main application
│   ├── *_service.py # Service modules
│   └── *.sql        # Database scripts
├── frontend/         # Vite frontend
│   ├── *.html       # Pages
│   ├── *.js         # Scripts
│   └── models/      # Face-api.js models
└── docs/            # Documentation
```

---

## Next Steps

1. Customize branding in frontend
2. Configure email templates in Supabase
3. Set up backup strategy
4. Configure monitoring
5. Review security settings

---

For quick reference, see `QUICK_START.md`.
