# Face Verification Fix Instructions

## Problem
The error "operands could not be broadcast together with shapes (1,3) (128,)" indicates that stored face encodings in the database have incorrect shapes or formats.

## What Was Fixed

1. **Enhanced validation in `face_service.py`**:
   - Added shape validation for both stored and new encodings
   - Ensures encodings are always 128-dimensional vectors
   - Better error messages to identify the issue
   - Explicit dtype conversion to float64

2. **Created diagnostic tool `fix_encodings.py`**:
   - Checks all stored encodings in the database
   - Reports any encodings with incorrect shapes
   - Identifies which students need to re-register

## Steps to Fix

### 1. Check for corrupted encodings
```bash
cd backend
python fix_encodings.py
```

This will show you which student IDs have problematic encodings.

### 2. Re-register affected students
For any students with invalid encodings, they need to re-register their faces through the admin interface.

### 3. Test the fix
After re-registration, try marking attendance again. The system will now:
- Validate encoding shapes during registration
- Validate encoding shapes during verification
- Provide clear error messages if something is wrong

## Prevention

The updated code now prevents invalid encodings from being stored in the first place by:
- Validating encoding shape (must be 128-dimensional)
- Validating encoding length before database storage
- Adding detailed logging for troubleshooting

## If Issues Persist

If you still see shape errors after re-registration:
1. Check the backend logs for detailed error messages
2. Verify the face_recognition library is installed correctly: `pip install face_recognition`
3. Ensure images being captured are valid and contain exactly one face
