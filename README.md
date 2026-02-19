# Attend-X Face Attendance System

A production-ready Face Attendance System with Multi-Admin Data Isolation, Face Recognition (0.55 threshold), and secure attendance logic.

## 🚀 Quick Start

1.  **Database Setup** (Crucial)
    - Go to Supabase SQL Editor.
    - Run the script `backend/FINAL_DATABASE_SETUP.sql`.
    - This sets up tables, RLS policies, and triggers for face isolation.

2.  **Backend Setup**
    - Navigate to `backend/`.
    - Create a `.env` file with your credentials (optional, falls back to defaults for demo):
      ```env
      SUPABASE_URL=YOUR_URL
      SUPABASE_KEY=YOUR_SERVICE_ROLE_KEY
      ```
    - Install dependencies:
      ```powershell
      pip install -r requirements.txt
      ```
    - Run the server:
      ```powershell
      python app.py
      ```

3.  **Frontend Setup**
    - Simply open `frontend/login.html` in your browser (or serve via Live Server).

## 📄 Documentation

A comprehensive **Final Setup Documentation PDF** has been generated at:
`backend/final_setup.pdf`

Please refer to it for:
- Full API documentation
- Security architecture
- Database schema details
- Troubleshooting

## 🔑 Key Features
- **Multi-Admin Isolation**: Admins can only see their own students.
- **Strict Face Matching**: Using 0.55 distance threshold (72% confidence).
- **Secure Attendance**: Marking logic moved to backend `/mark_attendance`.
- **Clean Code**: Modular services (`face_service`, `auth_service`, etc.).
