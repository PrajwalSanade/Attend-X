"""
Utility script to check and fix face encodings in the database.
Run this to validate all stored encodings have the correct shape.
"""
import numpy as np
from database_service import get_supabase_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_encodings():
    """Check all face encodings and report any issues."""
    client = get_supabase_client()
    
    try:
        # Fetch all encodings
        res = client.table("face_encodings").select("*").execute()
        
        if not res.data:
            logger.info("No face encodings found in database")
            return
        
        logger.info(f"Found {len(res.data)} face encodings to check")
        
        issues = []
        for record in res.data:
            student_id = record['student_id']
            encoding_data = record['encoding']
            
            # Convert to numpy array
            try:
                encoding = np.array(encoding_data, dtype=np.float64)
                
                # Check shape
                if encoding.shape != (128,):
                    issues.append({
                        'student_id': student_id,
                        'shape': encoding.shape,
                        'length': len(encoding_data) if isinstance(encoding_data, list) else 'N/A'
                    })
                    logger.warning(f"Student {student_id}: Invalid shape {encoding.shape}")
                else:
                    logger.info(f"Student {student_id}: OK (shape {encoding.shape})")
                    
            except Exception as e:
                issues.append({
                    'student_id': student_id,
                    'error': str(e)
                })
                logger.error(f"Student {student_id}: Error - {e}")
        
        # Summary
        if issues:
            logger.warning(f"\n{'='*50}")
            logger.warning(f"Found {len(issues)} problematic encodings:")
            for issue in issues:
                logger.warning(f"  {issue}")
            logger.warning(f"{'='*50}\n")
            logger.warning("These students need to re-register their faces.")
            
            # Print student IDs that need re-registration
            student_ids = [issue['student_id'] for issue in issues]
            logger.warning(f"Student IDs to re-register: {student_ids}")
        else:
            logger.info(f"\n{'='*50}")
            logger.info("All encodings are valid!")
            logger.info(f"{'='*50}\n")
            
    except Exception as e:
        logger.error(f"Error checking encodings: {e}")

if __name__ == "__main__":
    check_and_fix_encodings()
