from datetime import datetime
from database_service import get_supabase_client

def mark_student_attendance(student_id: str, confidence: float):
    """
    Mark student attendance if not already marked today.
    """
    client = get_supabase_client()
    today = datetime.now().date().isoformat()
    
    try:
        # Check existing using existing table structure
        res = client.table("attendance").select("id").eq("student_id", student_id).eq("date", today).execute()
        if res.data:
            return False, "Attendance already recorded for today."
            
        # 2. Fetch admin_id for this student to ensure RLS compliance
        student_res = client.table("students").select("admin_id").eq("id", student_id).execute()
        if not student_res.data:
            return False, "Student not found in database."
        
        admin_id = student_res.data[0].get('admin_id')
            
        # 3. Insert new record
        data = {
            "student_id": student_id,
            "admin_id": admin_id,
            "date": today,
            "status": "present",
            "verified": True,
            "confidence": confidence, # Assuming validation against confidence already done
            "created_at": datetime.now().isoformat()
        }
        res = client.table("attendance").insert(data).execute()
        return True, "Attendance marked successfully."
    except Exception as e:
        return False, str(e)

def get_attendance_history(student_id: str):
    client = get_supabase_client()
    res = client.table("attendance").select("*").eq("student_id", student_id).order("date", ascending=False).limit(20).execute()
    return res.data
