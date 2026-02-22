import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

class TestAttendXApi(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'healthy')
        print("API Health Check: PASSED")

    @patch('auth_service.get_current_user')
    def test_delete_face_no_id(self, mock_get_user):
        # Mock auth to pass
        mock_get_user.return_value = (MagicMock(id="admin-123"), None)
        
        response = self.app.post('/delete_face', 
                                json={}, 
                                headers={"Authorization": "Bearer fake-token"})
        self.assertEqual(response.status_code, 400)
        print("API Delete Face (Missing ID): PASSED (Returned 400)")

    @patch('app.get_supabase_client')
    @patch('auth_service.get_current_user')
    def test_export_attendance_no_records(self, mock_get_user, mock_get_supabase):
        # Mock auth to pass
        mock_user = MagicMock()
        mock_user.id = "admin-123"
        mock_get_user.return_value = (mock_user, None)
        
        # Mock Supabase
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        
        # Mock admin resolve
        mock_client.table("admins").select().eq().execute.return_value = MagicMock(data=[{"id": "uuid-1"}])
        # Mock attendance fetch (return empty)
        mock_client.table("attendance").select().eq().order().execute.return_value = MagicMock(data=[])
        
        response = self.app.post('/export_attendance', 
                                json={"format": "csv"}, 
                                headers={"Authorization": "Bearer fake-token"})
        self.assertEqual(response.status_code, 404)
        print("API Export (No Records): PASSED (Returned 404)")

    @patch('app.get_supabase_client')
    @patch('auth_service.get_current_user')
    @patch('app.generate_attendance_csv')
    def test_export_attendance_csv(self, mock_gen_csv, mock_get_user, mock_get_supabase):
        # Mock auth
        mock_user = MagicMock()
        mock_user.id = "admin-123"
        mock_get_user.return_value = (mock_user, None)
        
        # Mock Supabase
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table("admins").select().eq().execute.return_value = MagicMock(data=[{"id": "uuid-1"}])
        mock_client.table("attendance").select().eq().order().execute.return_value = MagicMock(data=[{"any": "data"}])
        
        # Mock CSV generation
        mock_gen_csv.return_value = "name,roll\nTest,101"
        
        response = self.app.post('/export_attendance', 
                                json={"format": "csv"}, 
                                headers={"Authorization": "Bearer fake-token"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attendance_report.csv", response.headers["Content-Disposition"])
        print("API Export CSV: PASSED")

if __name__ == "__main__":
    unittest.main()
