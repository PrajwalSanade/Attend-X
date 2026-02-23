import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone
from typing import Optional, Tuple

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from attendance_service import mark_student_attendance
from auth_service import require_admin, require_auth
from database_service import get_supabase_client
from export_service import generate_attendance_csv, generate_attendance_pdf
from face_service import delete_student_face, register_student_face, verify_student_face

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AttendX")

app = FastAPI(title="AttendX Backend", version="2.2")

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

FACE_TIMEOUT_SECONDS = 2.0
RATE_LIMIT_ATTEMPTS = 3
RATE_LIMIT_WINDOW_SECONDS = 60
_ATTEMPT_LOG = {}
_ATTEMPT_LOCK = threading.Lock()


class RegisterFaceRequest(BaseModel):
    student_id: Optional[str] = None
    image: Optional[str] = None


class VerifyFaceRequest(BaseModel):
    student_id: Optional[str] = None
    image: Optional[str] = None


class MarkAttendanceRequest(BaseModel):
    student_id: Optional[str] = None
    image: Optional[str] = None
    subject: Optional[str] = None


class DeleteFaceRequest(BaseModel):
    student_id: Optional[str] = None
    student_roll: Optional[str] = None


class ExportRequest(BaseModel):
    format: str = "csv"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _success(message: str, confidence: float = 0.0, **extra):
    payload = {
        "success": True,
        "message": message,
        "confidence": float(confidence),
        "timestamp": _now_iso(),
    }
    payload.update(extra)
    return payload


def _error(status_code: int, error_code: str, message: str):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error_code": error_code, "message": message},
    )


def _error_payload(error_code: str, message: str):
    return {"success": False, "error_code": error_code, "message": message}


def _map_face_failure(message: str) -> Tuple[int, str, str]:
    text = (message or "").lower()
    if "found 0 faces" in text or "no face" in text:
        return 400, "NO_FACE_DETECTED", "No face detected. Please look at the camera."
    if "found " in text and "faces" in text and "found 1 faces" not in text:
        return 400, "MULTIPLE_FACES", "Exactly one face must be visible."
    if "invalid stored encoding format" in text or "encoding format" in text:
        return 500, "ENCODING_ERROR", "Face encoding data corrupted."
    if "does not match" in text or "mismatch" in text:
        return 400, "FACE_MISMATCH", "Face does not match registered student."
    return 400, "FACE_MISMATCH", "Face does not match registered student."


def _verify_face_with_timeout(student_id: str, image: str):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(verify_student_face, student_id, image)
        try:
            return future.result(timeout=FACE_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            future.cancel()
            _error(503, "FACE_TIMEOUT", "Face recognition service timeout.")


def _register_face_with_timeout(student_id: str, image: str):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(register_student_face, student_id, image)
        try:
            return future.result(timeout=FACE_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            future.cancel()
            _error(503, "FACE_TIMEOUT", "Face recognition service timeout.")


def _check_rate_limit(student_id: str):
    now = time.time()
    with _ATTEMPT_LOCK:
        attempts = _ATTEMPT_LOG.get(student_id, [])
        attempts = [ts for ts in attempts if (now - ts) <= RATE_LIMIT_WINDOW_SECONDS]
        if len(attempts) >= RATE_LIMIT_ATTEMPTS:
            _ATTEMPT_LOG[student_id] = attempts
            _error(429, "RATE_LIMIT_EXCEEDED", "Too many attempts. Try again after 1 minute.")
        attempts.append(now)
        _ATTEMPT_LOG[student_id] = attempts


def _resolve_admin_context(user) -> Tuple[object, str]:
    client = get_supabase_client()
    user_id = getattr(user, "id", None)
    if not user_id:
        _error(401, "AUTH_REQUIRED", "Authentication token required.")

    admin_res = client.table("admins").select("id").eq("user_id", user_id).limit(1).execute()
    if not admin_res.data:
        _error(403, "ACCESS_DENIED", "Unauthorized access.")

    return client, admin_res.data[0]["id"]


def _assert_student_scope(client, admin_id: str, student_id: str):
    student_res = client.table("students").select("id,admin_id").eq("id", student_id).limit(1).execute()
    if not student_res.data:
        _error(400, "INVALID_PAYLOAD", "Missing required parameters.")
    if student_res.data[0].get("admin_id") != admin_id:
        _error(403, "TENANT_ISOLATION_VIOLATION", "Access to this resource is restricted.")


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


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(_, exc: StarletteHTTPException):
    if exc.status_code == 405:
        return JSONResponse(
            status_code=405,
            content=_error_payload("METHOD_NOT_ALLOWED", "Method not allowed."),
        )
    if isinstance(exc, HTTPException):
        return await http_exception_handler(_, exc)
    return JSONResponse(status_code=exc.status_code, content=_error_payload("INTERNAL_ERROR", "Internal server error."))


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and detail.get("error_code") and detail.get("message"):
        return JSONResponse(status_code=exc.status_code, content=detail)

    code_map = {
        400: ("INVALID_PAYLOAD", "Missing required parameters."),
        401: ("AUTH_REQUIRED", "Authentication token required."),
        403: ("ACCESS_DENIED", "Unauthorized access."),
        404: ("NO_DATA", "No attendance records found."),
        405: ("METHOD_NOT_ALLOWED", "Method not allowed."),
    }
    error_code, message = code_map.get(exc.status_code, ("INTERNAL_ERROR", "Internal server error."))
    return JSONResponse(status_code=exc.status_code, content=_error_payload(error_code, message))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, __: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=_error_payload("INVALID_PAYLOAD", "Missing required parameters."),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=_error_payload("INTERNAL_ERROR", "Internal server error."),
    )


@app.on_event("startup")
async def on_startup():
    port = int(os.environ.get("PORT", 5000))
    logger.info("Attend-X backend listening on http://0.0.0.0:%s", port)
    logger.info("Health check: http://0.0.0.0:%s/api/v1/health", port)


@app.get("/health")
@app.get("/api/v1/health")
async def health():
    return _success("Service healthy.", confidence=0.0, status="healthy", service="AttendX Backend", version="2.2")


@app.post("/register_face")
@app.post("/register-face")
@app.post("/api/v1/register_face")
@app.post("/api/v1/register-face")
async def register_face(request: RegisterFaceRequest, user=Depends(require_admin)):
    if not request.student_id or not request.image:
        _error(400, "INVALID_PAYLOAD", "Missing required parameters.")

    client, admin_id = _resolve_admin_context(user)
    _assert_student_scope(client, admin_id, request.student_id)

    success, message = _register_face_with_timeout(request.student_id, request.image)
    if not success:
        status, error_code, std_message = _map_face_failure(message)
        _error(status, error_code, std_message)

    return _success("Attendance marked successfully.", confidence=100.0)


@app.post("/verify_face")
@app.post("/verify-face")
@app.post("/api/v1/verify_face")
@app.post("/api/v1/verify-face")
async def verify_face(request: VerifyFaceRequest):
    if not request.student_id or not request.image:
        _error(400, "INVALID_PAYLOAD", "Missing required parameters.")

    match, confidence, message = _verify_face_with_timeout(request.student_id, request.image)
    if not match:
        status, error_code, std_message = _map_face_failure(message)
        _error(status, error_code, std_message)

    return _success("Attendance marked successfully.", confidence=confidence, match=True)


@app.post("/mark_attendance")
@app.post("/mark-attendance")
@app.post("/api/v1/mark_attendance")
@app.post("/api/v1/mark-attendance")
async def mark_attendance(request: MarkAttendanceRequest):
    if not request.student_id or not request.image:
        _error(400, "INVALID_PAYLOAD", "Missing required parameters.")

    _check_rate_limit(request.student_id)
    match, confidence, message = _verify_face_with_timeout(request.student_id, request.image)

    if not match:
        status, error_code, std_message = _map_face_failure(message)
        _error(status, error_code, std_message)

    marked, result_code, result_message = mark_student_attendance(request.student_id, confidence, request.subject)
    if not marked:
        if result_code == "DUPLICATE_ATTENDANCE":
            _error(400, "DUPLICATE_ATTENDANCE", "Attendance already recorded for today.")
        if result_code == "OUTSIDE_TIME_WINDOW":
            _error(403, "OUTSIDE_TIME_WINDOW", "Attendance allowed only during lecture time.")
        if result_code == "INVALID_PAYLOAD":
            _error(400, "INVALID_PAYLOAD", "Missing required parameters.")
        _error(500, "INTERNAL_ERROR", "Internal server error.")

    return _success("Attendance marked successfully.", confidence=confidence)


@app.post("/delete_face")
@app.post("/delete-face")
@app.post("/delete_student_data")
@app.post("/api/v1/delete_face")
@app.post("/api/v1/delete-face")
@app.post("/api/v1/delete_student_data")
async def delete_face(request: DeleteFaceRequest, user=Depends(require_admin)):
    if not request.student_id:
        _error(400, "INVALID_PAYLOAD", "Missing required parameters.")

    client, admin_id = _resolve_admin_context(user)
    _assert_student_scope(client, admin_id, request.student_id)

    success, _ = delete_student_face(request.student_id)
    if not success:
        _error(500, "INTERNAL_ERROR", "Internal server error.")
    return _success("Attendance marked successfully.", confidence=100.0)


@app.get("/api/v1/export/csv")
async def export_attendance_csv(user=Depends(require_admin)):
    client, admin_id = _resolve_admin_context(user)
    records = _get_admin_attendance_records(client, admin_id)
    if not records:
        _error(404, "NO_DATA", "No attendance records found.")
    return _build_csv_response(records)


@app.get("/api/v1/export/pdf")
async def export_attendance_pdf(user=Depends(require_admin)):
    client, admin_id = _resolve_admin_context(user)
    records = _get_admin_attendance_records(client, admin_id)
    if not records:
        _error(404, "NO_DATA", "No attendance records found.")
    return _build_pdf_response(records)


@app.post("/export_attendance")
@app.post("/api/v1/export")
async def export_attendance(request: ExportRequest, user=Depends(require_admin)):
    export_format = request.format.lower()
    client, admin_id = _resolve_admin_context(user)
    records = _get_admin_attendance_records(client, admin_id)
    if not records:
        _error(404, "NO_DATA", "No attendance records found.")

    if export_format == "csv":
        return _build_csv_response(records)
    if export_format == "pdf":
        return _build_pdf_response(records)

    _error(400, "INVALID_PAYLOAD", "Missing required parameters.")


@app.post("/api/v1/repair")
async def repair_attendance(user=Depends(require_admin)):
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

    return _success(
        "Attendance marked successfully.",
        confidence=100.0,
        scanned_records=len(rows),
        duplicates_removed=removed,
    )


@app.get("/api/v1/statistics")
async def get_statistics(user=Depends(require_admin)):
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

    return _success(
        "Attendance marked successfully.",
        confidence=avg_confidence,
        total_students=total_students,
        total_days=unique_days,
        total_attendance_records=total_records,
        average_confidence=avg_confidence,
        overall_attendance_rate=overall_rate,
        most_regular_student=most_regular,
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True, log_level="info")
