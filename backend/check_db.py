from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

client = create_client(url, key)

def check_db():
    print(f"Checking Supabase: {url}")
    
    # Check Face Encodings Table structure if possible via a dummy select
    try:
        res = client.table("face_encodings").select("*").limit(1).execute()
        if res.data:
            print(f"\nFace Encodings sample keys: {res.data[0].keys()}")
        else:
            print("\nFace Encodings table is empty or inaccessible.")
    except Exception as e:
        print(f"\nError checking face_encodings structure: {e}")
        
    # List all students and their registration status
    res = client.table("students").select("id, name, roll_number").execute()
    print(f"\n--- Student Registry ({len(res.data)} total) ---")
    for s in res.data:
        enc = client.table("face_encodings").select("id").eq("student_id", s['id']).execute()
        st = "✅" if enc.data else "❌"
        print(f"{st} {s['name']} (ID: {s['id']}, Roll: {s['roll_number']})")

if __name__ == "__main__":
    check_db()
