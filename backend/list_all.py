from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

client = create_client(url, key)

def list_all_students():
    res = client.table("students").select("id, name, roll_number").execute()
    print(f"Total Students: {len(res.data)}")
    for s in res.data:
        enc = client.table("face_encodings").select("id").eq("student_id", s['id']).execute()
        status = "✅ Reg" if enc.data else "❌ Unreg"
        print(f"[{status}] {s['name']} (Roll: {s['roll_number']}, ID: {s['id']})")

if __name__ == "__main__":
    list_all_students()
