import os
from datetime import datetime
from typing import Optional

from database_service import get_supabase_client


def _within_lecture_window(now: Optional[datetime] = None) -> bool:
    now = now or datetime.now()
    start_hour = int(os.environ.get("ATTENDANCE_START_HOUR", "0"))
    end_hour = int(os.environ.get("ATTENDANCE_END_HOUR", "23"))
    current_hour = now.hour
    return start_hour <= current_hour <= end_hour


def mark_student_attendance(student_id: str, confidence: float, subject: Optional[str] = None):
    """
    Mark attendance with duplicate prevention and optional subject support.
    Returns:
      (True, "ATTENDANCE_MARKED", "Attendance marked successfully.")
      (False, "<ERROR_CODE>", "<MESSAGE>")
    """
    client = get_supabase_client()
    now = datetime.now()
    today = now.date().isoformat()

    try:
        if not _within_lecture_window(now):
            return False, "OUTSIDE_TIME_WINDOW", "Attendance allowed only during lecture time."

        query = client.table("attendance").select("id").eq("student_id", student_id).eq("date", today)
        if subject:
            query = query.eq("subject", subject)
        existing = query.execute()
        if existing.data:
            return False, "DUPLICATE_ATTENDANCE", "Attendance already recorded for today."

        student_res = client.table("students").select("admin_id").eq("id", student_id).execute()
        if not student_res.data:
            return False, "INVALID_PAYLOAD", "Missing required parameters."

        admin_id = student_res.data[0].get("admin_id")
        payload = {
            "student_id": student_id,
            "admin_id": admin_id,
            "date": today,
            "status": "present",
            "verified": True,
            "confidence": float(confidence),
            "created_at": now.isoformat(),
        }
        if subject:
            payload["subject"] = subject

        client.table("attendance").insert(payload).execute()
        return True, "ATTENDANCE_MARKED", "Attendance marked successfully."
    except Exception:
        return False, "INTERNAL_ERROR", "Internal server error."


def get_attendance_history(student_id: str):
    client = get_supabase_client()
    res = (
        client.table("attendance")
        .select("*")
        .eq("student_id", student_id)
        .order("date", ascending=False)
        .limit(20)
        .execute()
    )
    return res.data
