import { supabase } from './supabaseClient.js';
import {
  openCamera,
  capturePhoto,
  uploadPhoto,
  stopCamera,
  clearImage,
  isCameraActive
} from './cameraModule.js';
import { isStudentAuthEnabled } from './authControl.js';

const API_BASES = ['http://127.0.0.1:5000', 'http://localhost:5000'];
const REQUEST_TIMEOUT_MS = 5000;


let currentPhotoBase64 = null;
let lastKnownApiBase = API_BASES[0];
let attendanceCameraReady = false;

document.addEventListener('DOMContentLoaded', async () => {
  console.log('[Attend-X] dashboard module init');
  setupModalHandlers();
  setupCameraHandlers();
  setupStudentFormHandlers();
  setupAdminHandlers();
  setupStudentHandlers();
  await preflightBackendHealth();
  setCurrentDate();
});

function setCurrentDate() {
  const currentDateEl = document.getElementById('currentDate');
  if (!currentDateEl) return;
  currentDateEl.textContent = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

async function preflightBackendHealth() {
  try {
    const result = await apiRequest('/health', { method: 'GET' }, { silent: true });
    if (result?.ok) {
      console.log(`[Attend-X] backend healthy on ${lastKnownApiBase}`);
      return;
    }
  } catch (error) {
    console.warn('[Attend-X] backend health check failed:', error.message);
  }
  console.warn('[Attend-X] backend unavailable. Add/verify face APIs will fail until Python server starts.');
}

async function apiRequest(path, options = {}, behavior = {}) {
  const { silent = false } = behavior;
  let lastError = null;

  for (const base of API_BASES) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

      const response = await fetch(`${base}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(await getAuthHeaders()),
          ...(options.headers || {})
        },
        signal: controller.signal
      });
      clearTimeout(timeout);

      let payload = {};
      try {
        payload = await response.json();
      } catch {
        payload = {};
      }

      if (!response.ok) {
        const message = payload?.message || payload?.error || `HTTP ${response.status}`;
        throw new Error(message);
      }

      lastKnownApiBase = base;
      return payload;
    } catch (error) {
      lastError = error;
      if (!silent) {
        console.warn(`[Attend-X] API request failed on ${base}${path}:`, error.message);
      }
    }
  }

  throw new Error(`Unable to reach backend (${path}). Start python backend on port 5000. Last error: ${lastError?.message || 'Unknown'}`);
}

function setupCameraHandlers() {
  const takePhotoBtn = document.getElementById('takePhotoBtn');
  const uploadFromPC = document.getElementById('uploadFromPC');
  const photoInput = document.getElementById('photoInput');
  const capturePhotoBtn = document.getElementById('capturePhotoBtn');
  const cancelCameraBtn = document.getElementById('cancelCameraBtn');
  const removePhotoBtn = document.getElementById('removePhotoBtn');
  const cameraContainer = document.getElementById('cameraContainer');
  const photoPreview = document.getElementById('photoPreview');
  const cameraVideo = document.getElementById('cameraVideo');
  const cameraCanvas = document.getElementById('cameraCanvas');
  const previewImage = document.getElementById('previewImage');

  if (!takePhotoBtn || !cameraVideo || !cameraCanvas) {
    console.error('[Attend-X] camera elements missing');
    return;
  }

  takePhotoBtn.addEventListener('click', async () => {
    try {
      takePhotoBtn.disabled = true;
      takePhotoBtn.textContent = 'Opening Camera...';
      photoPreview?.classList.add('hidden');
      clearImage();
      currentPhotoBase64 = null;
      cameraContainer?.classList.remove('hidden');
      await openCamera(cameraVideo, capturePhotoBtn);
    } catch (error) {
      showMessage(error.message || 'Failed to open camera', 'error', 'addStudentMessage');
      cameraContainer?.classList.add('hidden');
    } finally {
      takePhotoBtn.disabled = false;
      takePhotoBtn.textContent = 'Take Photo';
    }
  });

  capturePhotoBtn?.addEventListener('click', () => {
    try {
      currentPhotoBase64 = capturePhoto(cameraVideo, cameraCanvas);
      cameraContainer?.classList.add('hidden');
      if (previewImage && photoPreview) {
        previewImage.src = currentPhotoBase64;
        photoPreview.classList.remove('hidden');
      }
    } catch (error) {
      showMessage(error.message || 'Failed to capture photo', 'error', 'addStudentMessage');
    }
  });

  cancelCameraBtn?.addEventListener('click', () => {
    stopCamera();
    cameraContainer?.classList.add('hidden');
  });

  uploadFromPC?.addEventListener('click', () => photoInput?.click());

  photoInput?.addEventListener('change', async (event) => {
    try {
      const file = event.target.files?.[0];
      if (!file) return;
      if (isCameraActive()) stopCamera();
      cameraContainer?.classList.add('hidden');
      currentPhotoBase64 = await uploadPhoto(file);
      if (previewImage && photoPreview) {
        previewImage.src = currentPhotoBase64;
        photoPreview.classList.remove('hidden');
      }
    } catch (error) {
      showMessage(error.message || 'Failed to upload photo', 'error', 'addStudentMessage');
    }
  });

  removePhotoBtn?.addEventListener('click', () => {
    clearImage();
    currentPhotoBase64 = null;
    if (photoPreview) photoPreview.classList.add('hidden');
    if (previewImage) previewImage.src = '';
    if (photoInput) photoInput.value = '';
  });
}

function setupStudentFormHandlers() {
  const saveStudentBtn = document.getElementById('saveStudentBtn');
  if (!saveStudentBtn) return;
  saveStudentBtn.addEventListener('click', handleAddStudent);
}

function setupAdminHandlers() {
  document.getElementById('viewStudentsBtn')?.addEventListener('click', async () => {
    document.getElementById('studentsListModal').style.display = 'block';
    await renderStudentsList();
  });

  document.getElementById('viewAttendanceDetailsBtn')?.addEventListener('click', async () => {
    const details = document.getElementById('attendanceDetails');
    if (!details) return;
    details.classList.toggle('hidden');
    if (!details.classList.contains('hidden')) {
      await renderAttendanceLists();
    }
  });

  document.getElementById('refreshDashboardBtn')?.addEventListener('click', refreshDashboardData);
}

function setupStudentHandlers() {
  document.getElementById('markAttendanceBtn')?.addEventListener('click', openAttendanceCamera);
  document.getElementById('captureAttendanceBtn')?.addEventListener('click', captureAndVerifyAttendance);
}

async function handleAddStudent() {
  const studentName = document.getElementById('studentNameInput')?.value?.trim();
  const rollNumber = document.getElementById('student_idInput')?.value?.trim();
  const saveBtn = document.getElementById('saveStudentBtn');

  if (!studentName) return showMessage('Please enter student name', 'error', 'addStudentMessage');
  if (!rollNumber) return showMessage('Please enter roll number', 'error', 'addStudentMessage');
  if (!currentPhotoBase64) return showMessage('Please take or upload a photo', 'error', 'addStudentMessage');

  saveBtn.disabled = true;
  saveBtn.textContent = 'Adding Student...';

  try {
    const existing = await supabase.from('students').select('id').eq('roll_number', rollNumber).maybeSingle();
    if (existing.data) throw new Error('Roll number already exists');
    if (existing.error) throw new Error(existing.error.message);

    const currentUser = getCurrentUserSafe();

    // Add admin_id to student record via REST API logic if needed, but standard flow inserts directly to Supabase.
    // However, API call below creates face encoding. We should pass admin_id here too if backend needs it.

    const { data: insertedStudent, error: insertError } = await supabase
      .from('students')
      .insert([{
        name: studentName,
        roll_number: rollNumber,
        photo_url: currentPhotoBase64,
        face_registered: true,
        admin_id: currentUser?.id,
        created_at: new Date().toISOString()
      }])
      .select()
      .single();

    if (insertError) throw new Error(insertError.message);

    try {
      const faceResult = await apiRequest('/register_face', {
        method: 'POST',
        headers: await getAuthHeaders(),
        body: JSON.stringify({
          student_id: insertedStudent.id,
          student_roll: rollNumber,
          image: currentPhotoBase64
        })
      });

      if (!faceResult?.success) {
        throw new Error(faceResult?.message || 'Face registration failed');
      }

      console.log('[Attend-X] student added:', insertedStudent.roll_number);
      showMessage('Student added successfully', 'success', 'addStudentMessage');
      resetAddStudentForm();
      await updateDashboard();

    } catch (faceError) {
      // Rollback: Delete student record if face registration failed
      await supabase.from('students').delete().eq('id', insertedStudent.id);
      throw faceError;
    }
  } catch (error) {
    console.error('[Attend-X] add student failed:', error);
    showMessage(`Error: ${error.message}`, 'error', 'addStudentMessage');
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Add Student';
  }
}

function resetAddStudentForm() {
  const nameInput = document.getElementById('studentNameInput');
  const rollInput = document.getElementById('student_idInput');
  const photoPreview = document.getElementById('photoPreview');
  const previewImage = document.getElementById('previewImage');
  const photoInput = document.getElementById('photoInput');
  if (nameInput) nameInput.value = '';
  if (rollInput) rollInput.value = '';
  if (photoPreview) photoPreview.classList.add('hidden');
  if (previewImage) previewImage.src = '';
  if (photoInput) photoInput.value = '';
  clearImage();
  currentPhotoBase64 = null;
}

async function renderStudentsList() {
  const listEl = document.getElementById('studentsList');
  if (!listEl) return;
  listEl.innerHTML = '<p>Loading students...</p>';

  const { data, error } = await supabase
    .from('students')
    .select('id,name,roll_number,photo_url,created_at')
    .order('created_at', { ascending: false });

  if (error) {
    listEl.innerHTML = `<p class="error-message">${error.message}</p>`;
    return;
  }

  if (!data || !data.length) {
    listEl.innerHTML = '<p>No students available.</p>';
    return;
  }

  listEl.innerHTML = data.map(student => `
    <div class="student-card">
      <img class="student-photo" src="${student.photo_url || ''}" alt="${escapeHtml(student.name)}" onerror="this.src='https://via.placeholder.com/80?text=No+Photo'" />
      <h4>${escapeHtml(student.name)}</h4>
      <p>${escapeHtml(student.roll_number)}</p>
      <button class="btn btn-danger" data-student-delete="${student.id}" data-student-roll="${student.roll_number}">Delete</button>
    </div>
  `).join('');

  listEl.querySelectorAll('[data-student-delete]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const studentId = btn.getAttribute('data-student-delete');
      const roll = btn.getAttribute('data-student-roll');
      await handleDeleteStudent(studentId, roll);
    });
  });
}

async function handleDeleteStudent(studentId, rollNumber) {
  if (!confirm(`Delete student ${rollNumber}? This will also remove face data and attendance history.`)) return;

  try {
    const backendResult = await apiRequest('/delete_student_data', {
      method: 'POST',
      body: JSON.stringify({ student_id: studentId })
    });

    if (!backendResult.success) {
      throw new Error(backendResult.message || 'Face cleanup failed');
    }

    const attendanceDelete = await supabase.from('attendance').delete().eq('student_id', studentId);
    if (attendanceDelete.error) throw new Error(attendanceDelete.error.message);

    const studentDelete = await supabase.from('students').delete().eq('id', studentId);
    if (studentDelete.error) throw new Error(studentDelete.error.message);

    showMessage(`Student ${rollNumber} deleted successfully`, 'success', 'addStudentMessage');
    await renderStudentsList();
    await updateDashboard();
  } catch (error) {
    console.error('[Attend-X] delete student failed:', error);
    showMessage(`Delete failed: ${error.message}`, 'error', 'addStudentMessage');
  }
}

async function updateDashboard() {
  try {
    const studentsQuery = supabase.from('students').select('id,roll_number');
    const attendanceQuery = supabase.from('attendance').select('id,student_id,date');
    const [studentsResult, attendanceResult] = await Promise.all([studentsQuery, attendanceQuery]);

    if (studentsResult.error) throw new Error(studentsResult.error.message);
    if (attendanceResult.error) throw new Error(attendanceResult.error.message);

    const students = studentsResult.data || [];
    const attendance = attendanceResult.data || [];
    const today = new Date().toISOString().split('T')[0];
    const todayAttendance = attendance.filter(a => normalizeDateString(a.date) === today);

    const total = students.length;
    const present = new Set(todayAttendance.map(a => a.student_id)).size;
    const absent = Math.max(total - present, 0);

    setText('totalStudents', String(total));
    setText('presentToday', String(present));
    setText('absentToday', String(absent));

    await renderAttendanceLists(students, todayAttendance);
  } catch (error) {
    console.error('[Attend-X] dashboard update failed:', error);
  }
}

async function renderAttendanceLists(studentsParam, todayAttendanceParam) {
  const presentList = document.getElementById('presentList');
  const absentList = document.getElementById('absentList');
  if (!presentList || !absentList) return;

  let students = studentsParam;
  let todayAttendance = todayAttendanceParam;

  if (!students || !todayAttendance) {
    const today = new Date().toISOString().split('T')[0];
    const [studentsResult, attendanceResult] = await Promise.all([
      supabase.from('students').select('id,name,roll_number'),
      supabase.from('attendance').select('student_id,date,confidence').eq('date', today)
    ]);
    if (studentsResult.error) throw new Error(studentsResult.error.message);
    if (attendanceResult.error) throw new Error(attendanceResult.error.message);
    students = studentsResult.data || [];
    todayAttendance = attendanceResult.data || [];
  } else {
    const map = new Map((await supabase.from('students').select('id,name,roll_number')).data?.map(s => [s.id, s]) || []);
    students = students.map(s => map.get(s.id) || s);
  }

  const presentIds = new Set(todayAttendance.map(a => a.student_id));
  const presentStudents = students.filter(s => presentIds.has(s.id));
  const absentStudents = students.filter(s => !presentIds.has(s.id));

  presentList.innerHTML = presentStudents.length
    ? presentStudents.map(s => `<div class="student-item">${escapeHtml(s.name)} (${escapeHtml(s.roll_number)})</div>`).join('')
    : '<p>No students marked present today.</p>';

  absentList.innerHTML = absentStudents.length
    ? absentStudents.map(s => `<div class="student-item">${escapeHtml(s.name)} (${escapeHtml(s.roll_number)})</div>`).join('')
    : '<p>No absent students.</p>';
}

async function updateStudentDashboard() {
  const activeUser = getCurrentUserSafe();
  if (!activeUser?.id) return;

  setText('studentName', activeUser.name || '-');

  try {
    const { data, error } = await supabase
      .from('attendance')
      .select('date,confidence,verified')
      .eq('student_id', activeUser.id)
      .order('date', { ascending: false });

    if (error) throw new Error(error.message);

    const totalDays = data.length;
    const presentDays = data.filter(d => d.verified !== false).length;
    const percentage = totalDays === 0 ? 0 : ((presentDays / totalDays) * 100).toFixed(1);

    setText('totalDays', String(totalDays));
    setText('presentDays', String(presentDays));
    setText('attendancePercentage', `${percentage}%`);

    const history = document.getElementById('studentAttendanceHistory');
    if (history) {
      history.innerHTML = data.length
        ? data.slice(0, 15).map(item => `
          <div class="history-item">
            Date: ${escapeHtml(normalizeDateString(item.date))}<br/>
            Verified: ${item.verified ? 'Yes' : 'No'}<br/>
            Confidence: ${item.confidence || 0}%
          </div>
        `).join('')
        : '<p>No attendance records yet.</p>';
    }
  } catch (error) {
    console.error('[Attend-X] student dashboard update failed:', error);
  }
}

async function openAttendanceCamera() {
  const activeUser = getCurrentUserSafe();
  if (!activeUser?.id || !activeUser?.roll_number) {
    showMessage('Unable to find logged-in student details', 'error', 'attendanceMessage');
    return;
  }

  const authEnabled = await isStudentAuthEnabled();
  if (!authEnabled) {
    showMessage('Student authentication is disabled by admin', 'error', 'attendanceStatus');
    return;
  }

  const today = new Date().toISOString().split('T')[0];
  const existing = await supabase
    .from('attendance')
    .select('id')
    .eq('student_id', activeUser.id)
    .eq('date', today)
    .maybeSingle();

  if (existing.data) {
    showMessage('Attendance already marked for today', 'success', 'attendanceStatus');
    return;
  }
  if (existing.error) {
    showMessage(`Failed to check existing attendance: ${existing.error.message}`, 'error', 'attendanceStatus');
    return;
  }

  const modal = document.getElementById('attendanceCameraModal');
  const video = document.getElementById('attendanceVideo');
  const captureBtn = document.getElementById('captureAttendanceBtn');
  if (!modal || !video || !captureBtn) return;

  try {
    modal.style.display = 'block';
    await openCamera(video, captureBtn);
    attendanceCameraReady = true;
    showMessage('Camera ready. Capture your face to verify.', 'success', 'attendanceMessage');
  } catch (error) {
    attendanceCameraReady = false;
    showMessage(error.message || 'Failed to open attendance camera', 'error', 'attendanceMessage');
  }
}

async function captureAndVerifyAttendance() {
  const activeUser = getCurrentUserSafe();
  if (!activeUser?.id || !activeUser?.roll_number) {
    showMessage('Student session not found', 'error', 'attendanceMessage');
    return;
  }
  if (!attendanceCameraReady) {
    showMessage('Camera is not ready', 'error', 'attendanceMessage');
    return;
  }

  const video = document.getElementById('attendanceVideo');
  const canvas = document.getElementById('attendanceCanvas');
  const captureBtn = document.getElementById('captureAttendanceBtn');

  try {
    captureBtn.disabled = true;
    captureBtn.textContent = 'Verifying & Marking...';
    const faceImage = capturePhoto(video, canvas);
    attendanceCameraReady = false;

    // Call backend to verify face AND mark attendance securely
    const verifyResult = await apiRequest('/mark_attendance', {
      method: 'POST',
      body: JSON.stringify({
        student_roll: activeUser.roll_number,
        student_id: activeUser.id,
        image: faceImage
      })
    });

    if (!verifyResult?.success) {
      throw new Error(verifyResult?.message || 'Attendance failed');
    }

    showMessage(`Attendance marked! Confidence: ${verifyResult.confidence || 0}%`, 'success', 'attendanceStatus');

    closeModal('attendanceCameraModal');
    await updateStudentDashboard();
    await updateDashboard();
  } catch (error) {
    console.error('[Attend-X] attendance verification failed:', error);
    showMessage(`Attendance failed: ${error.message}`, 'error', 'attendanceMessage');
  } finally {
    captureBtn.disabled = false;
    captureBtn.textContent = 'Capture & Verify';
  }
}

function setupModalHandlers() {
  const closeButtons = document.querySelectorAll('.close');
  closeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-close');
      if (modalId) closeModal(modalId);
    });
  });

  window.addEventListener('click', (event) => {
    if (event.target.classList?.contains('modal')) {
      closeModal(event.target.id);
    }
  });

  document.querySelectorAll('[data-close]').forEach(btn => {
    if (!btn.classList.contains('close')) {
      btn.addEventListener('click', () => {
        const modalId = btn.getAttribute('data-close');
        if (modalId) closeModal(modalId);
      });
    }
  });
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = 'none';
  stopCamera();
  attendanceCameraReady = false;
}

function getCurrentUserSafe() {
  try {
    const session = sessionStorage.getItem('currentUser');
    if (session) return JSON.parse(session);
  } catch (error) {
    console.warn('[Attend-X] failed to parse current user from session', error);
  }
  return null;
}

function normalizeDateString(value) {
  if (!value) return '';
  if (typeof value === 'string' && value.length >= 10) {
    return value.slice(0, 10);
  }
  return new Date(value).toISOString().slice(0, 10);
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escapeHtml(input) {
  return String(input ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function showMessage(message, type, elementId) {
  const messageDiv = document.getElementById(elementId);
  if (!messageDiv) return;
  const className = type === 'error' ? 'error-message' : 'success-message';
  messageDiv.innerHTML = `<div class="${className}">${escapeHtml(message)}</div>`;
  setTimeout(() => {
    if (messageDiv.innerHTML.includes(message)) {
      messageDiv.innerHTML = '';
    }
  }, 5000);
}

async function refreshDashboardData() {
  await updateDashboard();
  showMessage('Dashboard refreshed', 'success', 'addStudentMessage');
}

function exportAttendanceData() {
  showMessage('Export helper not configured in this build.', 'error', 'addStudentMessage');
}
function repairAttendanceData() {
  showMessage('Repair helper not configured in this build.', 'error', 'addStudentMessage');
}
function showAttendanceStatistics() {
  showMessage('Statistics view not configured in this build.', 'error', 'addStudentMessage');
}
function debugAttendanceData() {
  updateDashboard();
  showMessage(`Debug: backend=${lastKnownApiBase}`, 'success', 'addStudentMessage');
}
function fixDateFormats() {
  showMessage('Date format fix is not required with current schema.', 'success', 'addStudentMessage');
}
async function downloadAttendanceList() {
  try {
    // We use fetch directly instead of apiRequest because we need the blob response
    const response = await fetch(`${lastKnownApiBase}/export_attendance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(await getAuthHeaders())
      },
      body: JSON.stringify({ format: 'csv' })
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.message || `HTTP ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    showMessage('CSV Export started', 'success', 'addStudentMessage');
  } catch (error) {
    console.error('[Attend-X] CSV export failed:', error);
    showMessage(`CSV Export failed: ${error.message}`, 'error', 'addStudentMessage');
  }
}
async function downloadAttendanceListPDF() {
  try {
    const response = await fetch(`${lastKnownApiBase}/export_attendance`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(await getAuthHeaders())
      },
      body: JSON.stringify({ format: 'pdf' })
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.message || `HTTP ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_${new Date().toISOString().split('T')[0]}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    showMessage('PDF Export started', 'success', 'addStudentMessage');
  } catch (error) {
    console.error('[Attend-X] PDF export failed:', error);
    showMessage(`PDF Export failed: ${error.message}`, 'error', 'addStudentMessage');
  }
}
function forceReloadAttendanceData() {
  refreshDashboardData();
}
function testAttendanceSystem() {
  preflightBackendHealth();
  showMessage('Attendance health check triggered. See console logs.', 'success', 'addStudentMessage');
}
async function clearAllAttendanceData() {
  if (!confirm('Delete ALL attendance records?')) return;
  const { error } = await supabase.from('attendance').delete().neq('id', '00000000-0000-0000-0000-000000000000');
  if (error) {
    showMessage(`Failed to clear attendance: ${error.message}`, 'error', 'addStudentMessage');
    return;
  }
  await updateDashboard();
  showMessage('All attendance data cleared', 'success', 'addStudentMessage');
}

window.updateDashboard = updateDashboard;
window.updateStudentDashboard = updateStudentDashboard;
window.closeModal = closeModal;
window.refreshDashboardData = refreshDashboardData;
window.exportAttendanceData = exportAttendanceData;
window.repairAttendanceData = repairAttendanceData;
window.showAttendanceStatistics = showAttendanceStatistics;
window.debugAttendanceData = debugAttendanceData;
window.fixDateFormats = fixDateFormats;
window.downloadAttendanceList = downloadAttendanceList;
window.downloadAttendanceListPDF = downloadAttendanceListPDF;
window.forceReloadAttendanceData = forceReloadAttendanceData;
window.testAttendanceSystem = testAttendanceSystem;
window.clearAllAttendanceData = clearAllAttendanceData;


// Helper to get auth headers
async function getAuthHeaders() {
  const { data } = await supabase.auth.getSession();
  if (data?.session?.access_token) {
    return { 'Authorization': `Bearer ${data.session.access_token}` };
  }
  return {};
}
