from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from typing import Optional
from auth_service import require_auth
from face_service import register_student_face, verify_student_face, delete_student_face
from attendance_service import mark_student_attendance
from export_service import generate_attendance_csv, generate_attendance_pdf
from database_service import get_supabase_client

app = FastAPI(title="AttendX Backend", version="2.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AttendX")

# Pydantic models
class RegisterFaceRequest(BaseModel):
    student_id: str
    image: str

class VerifyFaceRequest(BaseModel):
    student_id: str
    image: str

class MarkAttendanceRequest(BaseModel):
    student_id: str
    image: str

class DeleteFaceRequest(BaseModel):
    student_id: Optional[str] = None
    student_roll: Optional[str] = None

class ExportRequest(BaseModel):
    format: str = "csv"

@app.get('/health')
async def health():
    return {"status": "healthy", "service": "AttendX Backend", "version": "2.0"}

@app.post('/register_face')
@app.post('/register-face')
async def register_face(request: RegisterFaceRequest, user=Depends(require_auth)):
    """
    Registers a face for a student.
    Requires Admin Authentication (JWT).
    """
    logger.info(f"Received register_face for student_id: {request.student_id}")
    
    if not request.student_id or not request.image:
        raise HTTPException(status_code=400, detail="Missing student_id or image")

    success, message = register_student_face(request.student_id, request.image)
    
    if success:
        return {"success": True, "message": message}
    raise HTTPException(status_code=400, detail=message)

@app.post('/verify_face')
@app.post('/verify-face')
async def verify_face(request: VerifyFaceRequest):
    """
    Verifies a face.
    Used for testing or pre-check.
    """
    if not request.student_id or not request.image:
        raise HTTPException(status_code=400, detail="Missing parameters")

    match, confidence, message = verify_student_face(request.student_id, request.image)
    
    return {
        "success": match,
        "match": match,
        "confidence": confidence,
        "message": message
    }

@app.post('/mark_attendance')
@app.post('/mark-attendance')
async def mark_attendance(request: MarkAttendanceRequest):
    """
    Verifies face AND marks attendance.
    """
    logger.info(f"Received mark_attendance for student_id: {request.student_id}")
    
    if not request.student_id or not request.image:
        raise HTTPException(status_code=400, detail="Missing parameters")

    # 1. Verify Face
    match, confidence, message = verify_student_face(request.student_id, request.image)
    
    if not match:
        raise HTTPException(
            status_code=400,
            detail=f"Face verification failed: {message}. Verification error: operands could not be broadcast together with shapes (1,3) (128,)"
        )

    # 2. Mark Attendance
    marked, msg = mark_student_attendance(request.student_id, confidence)
    
    if marked:
        return {
            "success": True,
            "message": "Attendance marked successfully",
            "confidence": confidence
        }
    else:
        raise HTTPException(status_code=400, detail=msg)

@app.post('/delete_face')
@app.post('/delete-face')
@app.post('/delete_student_data')
async def delete_face(request: DeleteFaceRequest, user=Depends(require_auth)):
    """
    Deletes face encoding and associated data for a student.
    """
    if request.student_id:
        success, msg = delete_student_face(request.student_id)
        return {"success": success, "message": msg}
    
    if request.student_roll:
        raise HTTPException(
            status_code=400,
            detail="Deletion by roll number not fully supported. Please use student_id."
        )

    raise HTTPException(status_code=400, detail="Missing student_id")

@app.post('/export_attendance')
async def export_attendance(request: ExportRequest, user=Depends(require_auth)):
    """
    Exports attendance data for the current admin.
    """
    export_format = request.format.lower()
    
    client = get_supabase_client()
    user_id = user.id
    
    # 1. Resolve Admin ID from auth user_id
    admin_res = client.table("admins").select("id").eq("user_id", user_id).execute()
    if not admin_res.data:
        raise HTTPException(status_code=404, detail="Admin profile not found in database")
    
    admin_id = admin_res.data[0]['id']
    
    # 2. Fetch attendance with student details
    records_res = client.table("attendance").select("*, students(*)").eq("admin_id", admin_id).order("date", desc=False).execute()
    records = records_res.data
    
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found to export")

    # 3. Generate and return file
    if export_format == 'csv':
        csv_content = generate_attendance_csv(records)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendance_report.csv"}
        )
    elif export_format == 'pdf':
        try:
            pdf_content = generate_attendance_pdf(records)
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=attendance_report.pdf"}
            )
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    raise HTTPException(status_code=400, detail="Invalid export format")

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("app:app", host='0.0.0.0', port=port, reload=True)
