import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from export_service import generate_attendance_csv, generate_attendance_pdf
from face_service import delete_student_face

class TestAttendXServices(unittest.TestCase):
    def setUp(self):
        self.mock_records = [
            {
                "students": {"name": "Test Student", "roll_number": "101"},
                "date": "2026-02-22",
                "status": "present",
                "confidence": 85.5,
                "verified": True
            },
            {
                "students": {"name": "Another Student", "roll_number": "102"},
                "date": "2026-02-22",
                "status": "absent",
                "confidence": 0.0,
                "verified": False
            }
        ]

    def test_csv_generation(self):
        csv_data = generate_attendance_csv(self.mock_records)
        self.assertIn("Test Student", csv_data)
        self.assertIn("101", csv_data)
        self.assertIn("present", csv_data)
        self.assertIn("Another Student", csv_data)
        print("CSV Generation Test: PASSED")

    def test_pdf_generation(self):
        # This tests if it runs without error
        try:
            pdf_data = generate_attendance_pdf(self.mock_records)
            self.assertTrue(len(pdf_data) > 0)
            print("PDF Generation Test: PASSED")
        except Exception as e:
            self.fail(f"PDF generation failed: {e}")

    @patch('face_service.get_supabase_client')
    def test_delete_student_face(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table().delete().eq().execute.return_value = MagicMock(data=[])
        
        success, msg = delete_student_face("test-uuid")
        self.assertTrue(success)
        self.assertEqual(msg, "Deleted")
        print("Face Deletion Service Test: PASSED")

if __name__ == "__main__":
    unittest.main()
