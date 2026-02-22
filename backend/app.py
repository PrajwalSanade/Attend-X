import logging
import os
from typing import Optional, Tuple

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from attendance_service import mark_student_attendance
from auth_service import require_auth
from database_service import get_supabase_client
from export_service import generate_attendance_csv, generate_attendance_pdf
from face_service import delete_student_face, register_student_face, verify_student_face

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AttendX")

app = FastAPI(title="AttendX Backend", version="2.1")

default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
origins_env = os.environ.get("FRONTEND_ORIGINS", "")
allow_origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()] or default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
async def on_startup():
    port = int(os.environ.get("PORT", 5000))
    logger.info("Attend-X backend listening on http://0.0.0.0:%s", port)
    logger.info("Health check: http://0.0.0.0:%s/api/v1/health", port)


def _resolve_admin_context(user) -> Tuple[object, str]:
    client = get_supabase_client()
    user_id = getattr(user, "id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    admin_res = client.table("admins").select("id").eq("user_id", user_id).limit(1).execute()
    if not admin_res.data:
        raise HTTPException(status_code=404, detail="Admin profile not found")

    return client, admin_res.data[0]["id"]


def _get_admin_attendance_records(client, admin_id: str):
    attendance_res = (
        client.table("attendance")
        .select("id, student_id, date, status, confidence, verified, admin_id, created_at")
        .eq("admin_id", admin_id)
        .order("date", desc=False)
        .execute()
    )
    attendance = attendance_res.data or []
    if not attendance:
        return []

    student_ids = sorted({row.get("student_id") for row in attendance if row.get("student_id")})
    students_by_id = {}

    if student_ids:
        students_res = client.table("students").select("id, name, roll_number").in_("id", student_ids).execute()
        students_by_id = {row["id"]: row for row in (students_res.data or [])}

    records = []
    for row in attendance:
        student = students_by_id.get(row.get("student_id"), {})
        normalized = dict(row)
        normalized["students"] = {
            "name": student.get("name", "N/A"),
            "roll_number": student.get("roll_number", "N/A"),
        }
        records.append(normalized)

    return records


def _build_csv_response(records):
    csv_content = generate_attendance_csv(records)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_report.csv"},
        status_code=200,
    )


def _build_pdf_response(records):
    pdf_content = generate_attendance_pdf(records)
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=attendance_report.pdf"},
        status_code=200,
    )


@app.get("/health")
@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "service": "AttendX Backend", "version": "2.1"}


@app.post("/register_face")
@app.post("/register-face")
@app.post("/api/v1/register_face")
@app.post("/api/v1/register-face")
async def register_face(request: RegisterFaceRequest, user=Depends(require_auth)):
    if not request.student_id or not request.image:
        raise HTTPException(status_code=400, detail="Missing student_id or image")

    success, message = register_student_face(request.student_id, request.image)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@app.post("/verify_face")
@app.post("/verify-face")
@app.post("/api/v1/verify_face")
@app.post("/api/v1/verify-face")
async def verify_face(request: VerifyFaceRequest):
    if not request.student_id or not request.image:
        raise HTTPException(status_code=400, detail="Missing parameters")

    match, confidence, message = verify_student_face(request.student_id, request.image)
    return {"success": match, "match": match, "confidence": confidence, "message": message}


@app.post("/mark_attendance")
@app.post("/mark-attendance")
@app.post("/api/v1/mark_attendance")
@app.post("/api/v1/mark-attendance")
async def mark_attendance(request: MarkAttendanceRequest):
    if not request.student_id or not request.image:
        raise HTTPException(status_code=400, detail="Missing parameters")

    match, confidence, message = verify_student_face(request.student_id, request.image)
    if not match:
        raise HTTPException(status_code=400, detail=f"Face verification failed: {message}")

    marked, mark_message = mark_student_attendance(request.student_id, confidence)
    if not marked:
        raise HTTPException(status_code=400, detail=mark_message)

    return {"success": True, "message": "Attendance marked successfully", "confidence": confidence}


@app.post("/delete_face")
@app.post("/delete-face")
@app.post("/delete_student_data")
@app.post("/api/v1/delete_face")
@app.post("/api/v1/delete-face")
@app.post("/api/v1/delete_student_data")
async def delete_face(request: DeleteFaceRequest, user=Depends(require_auth)):
    if request.student_id:
        success, message = delete_student_face(request.student_id)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    if request.student_roll:
        raise HTTPException(status_code=400, detail="Deletion by roll number is not supported")

    raise HTTPException(status_code=400, detail="Missing student_id")


@app.get("/api/v1/export/csv")
async def export_attendance_csv(user=Depends(require_auth)):
    client, admin_id = _resolve_admin_context(user)
    records = _get_admin_attendance_records(client, admin_id)
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found")
    return _build_csv_response(records)


@app.get("/api/v1/export/pdf")
async def export_attendance_pdf(user=Depends(require_auth)):
    client, admin_id = _resolve_admin_context(user)
    records = _get_admin_attendance_records(client, admin_id)
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found")
    return _build_pdf_response(records)


@app.post("/export_attendance")
@app.post("/api/v1/export")
async def export_attendance(request: ExportRequest, user=Depends(require_auth)):
    export_format = request.format.lower()
    client, admin_id = _resolve_admin_context(user)
    records = _get_admin_attendance_records(client, admin_id)
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found")

    if export_format == "csv":
        return _build_csv_response(records)
    if export_format == "pdf":
        return _build_pdf_response(records)

    raise HTTPException(status_code=400, detail="Invalid export format")


@app.post("/api/v1/repair")
async def repair_attendance(user=Depends(require_auth)):
    client, admin_id = _resolve_admin_context(user)
    attendance_res = (
        client.table("attendance")
        .select("id, student_id, date, created_at")
        .eq("admin_id", admin_id)
        .order("created_at", desc=False)
        .execute()
    )
    rows = attendance_res.data or []

    seen = set()
    duplicate_ids = []
    for row in rows:
        key = f"{row.get('student_id')}|{row.get('date')}"
        if key in seen:
            if row.get("id"):
                duplicate_ids.append(row["id"])
        else:
            seen.add(key)

    removed = 0
    for row_id in duplicate_ids:
        client.table("attendance").delete().eq("id", row_id).execute()
        removed += 1

    return {
        "success": True,
        "message": "Repair completed",
        "scanned_records": len(rows),
        "duplicates_removed": removed,
    }


@app.get("/api/v1/statistics")
async def get_statistics(user=Depends(require_auth)):
    client, admin_id = _resolve_admin_context(user)

    students_res = client.table("students").select("id, name, roll_number").eq("admin_id", admin_id).execute()
    students = students_res.data or []
    student_map = {row["id"]: row for row in students if row.get("id")}

    attendance_res = (
        client.table("attendance")
        .select("student_id, date, confidence")
        .eq("admin_id", admin_id)
        .execute()
    )
    attendance = attendance_res.data or []

    total_students = len(students)
    total_records = len(attendance)
    unique_days = len({row.get("date") for row in attendance if row.get("date")})
    avg_confidence = (
        round(sum(float(row.get("confidence") or 0.0) for row in attendance) / total_records, 2)
        if total_records
        else 0.0
    )

    attendance_by_student = {}
    for row in attendance:
        student_id = row.get("student_id")
        if not student_id:
            continue
        attendance_by_student[student_id] = attendance_by_student.get(student_id, 0) + 1

    most_regular = None
    if attendance_by_student:
        most_regular_id = max(attendance_by_student, key=attendance_by_student.get)
        student = student_map.get(most_regular_id, {})
        most_regular = {
            "student_id": most_regular_id,
            "name": student.get("name", "N/A"),
            "roll_number": student.get("roll_number", "N/A"),
            "days_present": attendance_by_student.get(most_regular_id, 0),
        }

    overall_rate = (
        round((total_records / (total_students * unique_days)) * 100, 2)
        if total_students > 0 and unique_days > 0
        else 0.0
    )

    return {
        "success": True,
        "total_students": total_students,
        "total_days": unique_days,
        "total_attendance_records": total_records,
        "average_confidence": avg_confidence,
        "overall_attendance_rate": overall_rate,
        "most_regular_student": most_regular,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True, log_level="info")
