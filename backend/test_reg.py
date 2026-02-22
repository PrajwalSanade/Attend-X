from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

client = create_client(url, key)

def test_registration():
    # Attempt to register a dummy encoding for a student
    # Get a student ID first
    res = client.table("students").select("id, name").execute()
    if not res.data:
        print("No students found to test with.")
        return
    
    student = res.data[0]
    print(f"Testing registration for: {student['name']} ({student['id']})")
    
    data = {
        "student_id": student['id'],
        "encoding": [0.1, 0.2, 0.3],
        "updated_at": "now()"
    }
    
    try:
        # Check if we can write
        res = client.table("face_encodings").upsert(data, on_conflict="student_id").execute()
        print("\nSupabase Response:")
        print(f"Data: {res.data}")
        # In modern supabase-py, it might not have .error if it succeeded or raised.
        # But let's check.
    except Exception as e:
        print(f"\n❌ Exception caught: {e}")

if __name__ == "__main__":
    test_registration()
