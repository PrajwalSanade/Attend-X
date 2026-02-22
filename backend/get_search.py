from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

client = create_client(url, key)

def get_student_details(name_part):
    res = client.table("students").select("*").ilike("name", f"%{name_part}%").execute()
    print(f"\n--- Search results for '{name_part}' ({len(res.data)} found) ---")
    
    for s in res.data:
        print(f"Student: {s['name']}")
        print(f"  ID:   {s['id']}")
        print(f"  Roll: {s['roll_number']}")
        # Check encoding
        enc = client.table("face_encodings").select("*").eq("student_id", s['id']).execute()
        if enc.data:
            print(f"  ✅ Face Encoding: {enc.data[0]['id']}")
        else:
            print("  ❌ No Face Encoding found")

if __name__ == "__main__":
    get_student_details("Aditya")
    get_student_details("Prajwal")
