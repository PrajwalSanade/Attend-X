# Troubleshooting Guide

This document consolidates all troubleshooting information for the Attend-X project.

## Table of Contents
1. [Student Authentication Toggle Issues](#student-authentication-toggle)
2. [RLS Policy Errors](#rls-policy-errors)
3. [Face Recognition Issues](#face-recognition-issues)
4. [Database Setup](#database-setup)
5. [Common Errors](#common-errors)

---

## Student Authentication Toggle

### Problem: Toggle Not Responding
**Symptoms:**
- Toggle doesn't change state when clicked
- No visual feedback
- State doesn't persist

**Solution:**
1. Run `backend/COMPLETE_FIX.sql` in Supabase SQL Editor
2. Clear browser cache (Ctrl+Shift+Delete)
3. Hard refresh (Ctrl+F5)
4. Login again as admin

**Files:**
- `backend/COMPLETE_FIX.sql` - Complete database fix
- `backend/create_system_settings.sql` - System settings table

---

## RLS Policy Errors

### Error: "new row violates row-level security policy"

**Cause:** Incorrect RLS policy syntax in Supabase

**Quick Fix:**
```sql
DROP POLICY "Authenticated users can update system settings" ON system_settings;

CREATE POLICY "Authenticated users can update system settings" 
ON system_settings FOR UPDATE 
USING (auth.uid() IS NOT NULL) 
WITH CHECK (auth.uid() IS NOT NULL);
```

**Detailed Fix:**
Run `backend/COMPLETE_FIX.sql` in Supabase SQL Editor

---

## Face Recognition Issues

### Error: "operands could not be broadcast together with shapes"

**Cause:** Corrupted face encodings in database

**Solution:**
```bash
cd backend
python fix_encodings.py
```

This will identify students with invalid encodings who need to re-register.

**Prevention:**
The updated code validates encoding shapes during registration.

---

## Database Setup

### Initial Setup
1. Open Supabase SQL Editor
2. Run `backend/FINAL_DATABASE_SETUP.sql`
3. Run `backend/create_system_settings.sql`
4. Verify tables created successfully

### Verify Setup
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check system_settings
SELECT * FROM system_settings;

-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'system_settings';
```

---

## Common Errors

### Port Already in Use

**Windows:**
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -ti:5000 | xargs kill -9
```

### Camera Not Working
- Ensure HTTPS or localhost
- Check browser permissions
- Try Chrome browser
- Check if camera is in use by another app

### Backend Won't Start
- Check Python version (3.8+)
- Verify virtual environment activated
- Install dependencies: `pip install -r requirements.txt`
- Check `.env` file exists with correct credentials

### Frontend Won't Start
- Check Node.js version (16+)
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Check port 3000 is available

### Students Can't Login
- Check Student Authentication toggle is ON
- Verify student exists in database
- Check roll number is correct
- Clear browser cache

### Face Verification Fails
- Ensure good lighting
- Face should be clearly visible
- Only one face in frame
- Re-register if needed

---

## Getting Help

1. Check browser console (F12) for errors
2. Check backend terminal for errors
3. Verify database connection
4. Review this troubleshooting guide
5. Check main README.md for setup instructions

---

## Quick Commands

```bash
# Test backend
cd backend
python test_auth_toggle.py

# Check database
python check_db.py

# Fix encodings
python fix_encodings.py

# Start development
cd ..
start-dev.bat  # Windows
./start-dev.sh # Linux/Mac
```

---

For detailed setup instructions, see `README.md` and `QUICK_START.md`.
