from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

client = create_client(url, key)

def dump_encodings():
    res = client.table("face_encodings").select("id, student_id").execute()
    print(f"Total Encodings: {len(res.data)}")
    for e in res.data:
        # Check if student exists
        s_res = client.table("students").select("name").eq("id", e['student_id']).execute()
        student_name = s_res.data[0]['name'] if s_res.data else "ORPHAN (Student Missing)"
        print(f"Encoding: {e['id']} -> Student ID: {e['student_id']} ({student_name})")

if __name__ == "__main__":
    dump_encodings()
