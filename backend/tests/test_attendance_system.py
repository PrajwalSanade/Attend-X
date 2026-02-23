from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app as app_module
import attendance_service
import auth_service


class FakeResponse:
    def __init__(self, data=None):
        self.data = [] if data is None else data


class FakeQuery:
    def __init__(self, table_name, tables):
        self.table_name = table_name
        self.tables = tables
        self._op = "select"
        self._eq = []
        self._in = []
        self._order = None
        self._order_desc = False
        self._limit = None
        self._payload = None

    def select(self, _fields):
        self._op = "select"
        return self

    def eq(self, field, value):
        self._eq.append((field, value))
        return self

    def in_(self, field, values):
        self._in.append((field, set(values)))
        return self

    def order(self, field, desc=False, ascending=None):
        self._order = field
        self._order_desc = (not ascending) if ascending is not None else bool(desc)
        return self

    def limit(self, n):
        self._limit = n
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def delete(self):
        self._op = "delete"
        return self

    def execute(self):
        rows = list(self.tables.get(self.table_name, []))

        def matches(row):
            if not all(row.get(k) == v for k, v in self._eq):
                return False
            for k, vals in self._in:
                if row.get(k) not in vals:
                    return False
            return True

        if self._op == "select":
            data = [dict(r) for r in rows if matches(r)]
            if self._order:
                data.sort(key=lambda x: x.get(self._order), reverse=self._order_desc)
            if self._limit is not None:
                data = data[: self._limit]
            return FakeResponse(data=data)

        if self._op == "insert":
            payload = dict(self._payload)
            self.tables.setdefault(self.table_name, []).append(payload)
            return FakeResponse(data=[payload])

        if self._op == "delete":
            kept = [r for r in rows if not matches(r)]
            removed = len(rows) - len(kept)
            self.tables[self.table_name] = kept
            return FakeResponse(data=[{"deleted": removed}])

        return FakeResponse(data=[])


class FakeSupabase:
    def __init__(self, tables=None, auth_user=None, auth_raises=False):
        self.tables = {} if tables is None else tables
        self._auth_user = auth_user
        self._auth_raises = auth_raises

        class _Auth:
            def __init__(inner_self, outer):
                inner_self.outer = outer

            def get_user(inner_self, _token):
                if inner_self.outer._auth_raises:
                    raise RuntimeError("tampered token")
                return inner_self.outer._auth_user

        self.auth = _Auth(self)

    def table(self, name):
        return FakeQuery(name, self.tables)


def _auth_user(user_id="user-1"):
    return SimpleNamespace(id=user_id)


@pytest.fixture(autouse=True)
def _reset_state():
    app_module.app.dependency_overrides = {}
    app_module._ATTEMPT_LOG.clear()
    yield
    app_module.app.dependency_overrides = {}
    app_module._ATTEMPT_LOG.clear()


@pytest.fixture()
def client():
    with TestClient(app_module.app) as c:
        yield c


def test_mark_attendance_success_200(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_student_face", lambda *_: (True, 93.2, "Match found"))
    monkeypatch.setattr(
        app_module,
        "mark_student_attendance",
        lambda *_: (True, "ATTENDANCE_MARKED", "Attendance marked successfully."),
    )
    resp = client.post("/mark_attendance", json={"student_id": "stu-1", "image": "live-frame"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["message"] == "Attendance marked successfully."
    assert body["confidence"] == 93.2
    assert "timestamp" in body


def test_mark_attendance_face_mismatch_400(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_student_face", lambda *_: (False, 0.0, "Face does not match"))
    resp = client.post("/mark_attendance", json={"student_id": "stu-1", "image": "frame"})
    assert resp.status_code == 400
    assert resp.json() == {
        "success": False,
        "error_code": "FACE_MISMATCH",
        "message": "Face does not match registered student.",
    }


def test_mark_attendance_multiple_faces_400(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "verify_student_face",
        lambda *_: (False, 0.0, "Found 2 faces. System requires exactly 1 face."),
    )
    resp = client.post("/mark_attendance", json={"student_id": "stu-1", "image": "frame"})
    assert resp.status_code == 400
    assert resp.json() == {
        "success": False,
        "error_code": "MULTIPLE_FACES",
        "message": "Exactly one face must be visible.",
    }


def test_mark_attendance_no_face_400(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_student_face", lambda *_: (False, 0.0, "No face encoding found."))
    resp = client.post("/mark_attendance", json={"student_id": "stu-1", "image": "frame"})
    assert resp.status_code == 400
    assert resp.json() == {
        "success": False,
        "error_code": "NO_FACE_DETECTED",
        "message": "No face detected. Please look at the camera.",
    }


def test_mark_attendance_encoding_error_500(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "verify_student_face",
        lambda *_: (False, 0.0, "Invalid stored encoding format. Expected (128,), got (127,)"),
    )
    resp = client.post("/mark_attendance", json={"student_id": "stu-1", "image": "frame"})
    assert resp.status_code == 500
    assert resp.json() == {
        "success": False,
        "error_code": "ENCODING_ERROR",
        "message": "Face encoding data corrupted.",
    }


def test_mark_attendance_duplicate_400(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_student_face", lambda *_: (True, 91.0, "Match found"))
    monkeypatch.setattr(
        app_module,
        "mark_student_attendance",
        lambda *_: (False, "DUPLICATE_ATTENDANCE", "Attendance already recorded for today."),
    )
    resp = client.post("/mark_attendance", json={"student_id": "stu-1", "image": "frame"})
    assert resp.status_code == 400
    assert resp.json() == {
        "success": False,
        "error_code": "DUPLICATE_ATTENDANCE",
        "message": "Attendance already recorded for today.",
    }


def test_mark_attendance_outside_time_window_403(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_student_face", lambda *_: (True, 91.0, "Match found"))
    monkeypatch.setattr(
        app_module,
        "mark_student_attendance",
        lambda *_: (False, "OUTSIDE_TIME_WINDOW", "Attendance allowed only during lecture time."),
    )
    resp = client.post("/mark_attendance", json={"student_id": "stu-1", "image": "frame"})
    assert resp.status_code == 403
    assert resp.json() == {
        "success": False,
        "error_code": "OUTSIDE_TIME_WINDOW",
        "message": "Attendance allowed only during lecture time.",
    }


def test_mark_attendance_rate_limit_429(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_student_face", lambda *_: (True, 92.0, "Match found"))
    monkeypatch.setattr(
        app_module,
        "mark_student_attendance",
        lambda *_: (True, "ATTENDANCE_MARKED", "Attendance marked successfully."),
    )

    payload = {"student_id": "stu-rate", "image": "frame"}
    for _ in range(3):
        assert client.post("/mark_attendance", json=payload).status_code == 200
    blocked = client.post("/mark_attendance", json=payload)
    assert blocked.status_code == 429
    assert blocked.json() == {
        "success": False,
        "error_code": "RATE_LIMIT_EXCEEDED",
        "message": "Too many attempts. Try again after 1 minute.",
    }


def test_mark_attendance_different_subject_same_day_200(client, monkeypatch):
    monkeypatch.setattr(app_module, "verify_student_face", lambda *_: (True, 90.0, "Match found"))
    monkeypatch.setattr(
        app_module,
        "mark_student_attendance",
        lambda *_: (True, "ATTENDANCE_MARKED", "Attendance marked successfully."),
    )
    resp = client.post(
        "/mark_attendance",
        json={"student_id": "stu-1", "image": "frame", "subject": "Math"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Attendance marked successfully."


def test_mark_attendance_invalid_payload_400(client):
    resp = client.post("/mark_attendance", json={"student_id": "stu-1"})
    assert resp.status_code == 400
    assert resp.json() == {
        "success": False,
        "error_code": "INVALID_PAYLOAD",
        "message": "Missing required parameters.",
    }


def test_mark_attendance_method_not_allowed_405(client):
    resp = client.get("/mark_attendance")
    assert resp.status_code == 405
    assert resp.json() == {
        "success": False,
        "error_code": "METHOD_NOT_ALLOWED",
        "message": "Method not allowed.",
    }


def test_mark_attendance_face_timeout_503(client, monkeypatch):
    def _slow(*_):
        time.sleep(2.1)
        return True, 90.0, "Match found"

    monkeypatch.setattr(app_module, "verify_student_face", _slow)
    resp = client.post("/mark_attendance", json={"student_id": "stu-1", "image": "frame"})
    assert resp.status_code == 503
    assert resp.json() == {
        "success": False,
        "error_code": "FACE_TIMEOUT",
        "message": "Face recognition service timeout.",
    }


def test_export_missing_jwt_401(client):
    resp = client.get("/api/v1/export/csv")
    assert resp.status_code == 401
    assert resp.json() == {
        "success": False,
        "error_code": "AUTH_REQUIRED",
        "message": "Authentication token required.",
    }


def test_export_expired_jwt_401(client, monkeypatch):
    fake = FakeSupabase(auth_user=SimpleNamespace(user=None))
    monkeypatch.setattr(auth_service, "get_supabase_client", lambda: fake)
    resp = client.get("/api/v1/export/csv", headers={"Authorization": "Bearer expired"})
    assert resp.status_code == 401
    assert resp.json() == {
        "success": False,
        "error_code": "TOKEN_EXPIRED",
        "message": "Session expired. Please login again.",
    }


def test_export_tampered_jwt_401(client, monkeypatch):
    fake = FakeSupabase(auth_raises=True)
    monkeypatch.setattr(auth_service, "get_supabase_client", lambda: fake)
    resp = client.get("/api/v1/export/csv", headers={"Authorization": "Bearer tampered"})
    assert resp.status_code == 401
    assert resp.json() == {
        "success": False,
        "error_code": "INVALID_TOKEN",
        "message": "Invalid authentication token.",
    }


def test_student_attempting_direct_call_403(client, monkeypatch):
    fake = FakeSupabase(
        tables={"admins": []},
        auth_user=SimpleNamespace(user=SimpleNamespace(id="student-user-1")),
    )
    monkeypatch.setattr(auth_service, "get_supabase_client", lambda: fake)
    resp = client.get("/api/v1/export/csv", headers={"Authorization": "Bearer valid"})
    assert resp.status_code == 403
    assert resp.json() == {
        "success": False,
        "error_code": "ACCESS_DENIED",
        "message": "Unauthorized access.",
    }


def test_tenant_isolation_violation_403(client, monkeypatch):
    tables = {
        "admins": [{"id": "admin-a", "user_id": "user-1"}],
        "students": [{"id": "stu-2", "admin_id": "admin-b"}],
    }
    fake = FakeSupabase(
        tables=tables,
        auth_user=SimpleNamespace(user=SimpleNamespace(id="user-1")),
    )
    monkeypatch.setattr(auth_service, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(app_module, "get_supabase_client", lambda: fake)
    monkeypatch.setattr(app_module, "register_student_face", lambda *_: (True, "ok"))

    resp = client.post(
        "/api/v1/register_face",
        headers={"Authorization": "Bearer valid"},
        json={"student_id": "stu-2", "image": "frame"},
    )
    assert resp.status_code == 403
    assert resp.json() == {
        "success": False,
        "error_code": "TENANT_ISOLATION_VIOLATION",
        "message": "Access to this resource is restricted.",
    }


def test_export_empty_dataset_404(client, monkeypatch):
    app_module.app.dependency_overrides[app_module.require_admin] = lambda: _auth_user("user-1")
    fake = FakeSupabase(
        tables={"admins": [{"id": "admin-a", "user_id": "user-1"}], "attendance": [], "students": []}
    )
    monkeypatch.setattr(app_module, "get_supabase_client", lambda: fake)

    resp = client.get("/api/v1/export/csv")
    assert resp.status_code == 404
    assert resp.json() == {
        "success": False,
        "error_code": "NO_DATA",
        "message": "No attendance records found.",
    }


def test_attendance_service_duplicate_same_day(monkeypatch):
    today = time.strftime("%Y-%m-%d")
    fake = FakeSupabase(
        tables={
            "attendance": [{"id": "a1", "student_id": "stu-1", "date": today}],
            "students": [{"id": "stu-1", "admin_id": "admin-a"}],
        }
    )
    monkeypatch.setattr(attendance_service, "get_supabase_client", lambda: fake)
    ok, code, message = attendance_service.mark_student_attendance("stu-1", 88.0)
    assert ok is False
    assert code == "DUPLICATE_ATTENDANCE"
    assert message == "Attendance already recorded for today."
