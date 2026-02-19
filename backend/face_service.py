import face_recognition
import numpy as np
import base64
import cv2
import json
from database_service import get_supabase_client

# System Rules
FACE_MATCH_THRESHOLD = 0.55
MIN_CONFIDENCE = 72.0

def decode_image(base64_string):
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        img_bytes = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(f"Image decode error: {e}")
        return None

def get_face_encoding(image_rgb):
    # Detect faces
    locations = face_recognition.face_locations(image_rgb, model="hog")
    if len(locations) != 1:
        return None, f"Found {len(locations)} faces. System requires exactly 1 face."
    
    encodings = face_recognition.face_encodings(image_rgb, locations)
    if not encodings:
        return None, "No face encoding found."
    
    return encodings[0], None

def register_student_face(student_id: str, image_base64: str):
    """
    Register a face for a student.
    Stores encoding in Supabase 'face_encodings' table.
    """
    image_rgb = decode_image(image_base64)
    if image_rgb is None:
        return False, "Invalid image"

    encoding, error = get_face_encoding(image_rgb)
    if error:
        return False, error

    # Prepare data
    # Convert numpy array to list for JSON serialization
    encoding_list = encoding.tolist()
    
    client = get_supabase_client()
    
    # Upsert to handle re-registration (or delete old first)
    # Using upsert on specific constraint if unique constraint on student_id exists
    try:
        data = {
            "student_id": student_id,
            "encoding": encoding_list,
            "updated_at": "now()"
        }
        # Assuming we have a unique constraint on student_id in face_encodings
        res = client.table("face_encodings").upsert(data, on_conflict="student_id").execute()
        return True, "Face registered successfully"
    except Exception as e:
        return False, str(e)

def verify_student_face(student_id: str, image_base64: str):
    """
    Verify uploaded face against stored encoding.
    """
    image_rgb = decode_image(image_base64)
    if image_rgb is None:
        return False, 0.0, "Invalid image"

    new_encoding, error = get_face_encoding(image_rgb)
    if error:
        return False, 0.0, error

    client = get_supabase_client()
    
    try:
        # Fetch stored encoding
        res = client.table("face_encodings").select("encoding").eq("student_id", student_id).execute()
        
        if not res.data:
            return False, 0.0, "Face not registered for this student"
        
        stored_data = res.data[0]['encoding']
        stored_encoding = np.array(stored_data)
        
        # Compare
        distances = face_recognition.face_distance([stored_encoding], new_encoding)
        dist = distances[0]
        confidence = (1.0 - dist) * 100
        
        is_match = dist <= FACE_MATCH_THRESHOLD and confidence >= MIN_CONFIDENCE
        
        return is_match, round(confidence, 2), "Match found" if is_match else "Face does not match"
        
    except Exception as e:
        return False, 0.0, f"Verification error: {str(e)}"

def delete_student_face(student_id: str):
    client = get_supabase_client()
    try:
        client.table("face_encodings").delete().eq("student_id", student_id).execute()
        return True, "Deleted"
    except Exception as e:
        return False, str(e)
