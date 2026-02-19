// ============================================
// LOGIN.JS - Authentication Logic
// ============================================
// Handles Admin Login, Create Admin Account, and Student Login
// Uses Supabase for backend
// ============================================

import { supabase } from './supabaseClient.js';
import { isStudentAuthEnabled } from './authControl.js';

const USER_STORAGE_KEY = 'attend_x_user';
const LEGACY_USER_STORAGE_KEY = 'attendr_user';

// ============================================
// GLOBAL VARIABLES
// ============================================
let currentUser = null;
let currentUserType = null;

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', function() {
  console.log('✅ Login system initialized');
  
  // Check if user is already logged in
  checkExistingSession();
  
  // Setup event listeners
  setupEventListeners();
  
  // Set default active tab (Admin Login)
  showAdminLoginForm();
});

// ============================================
// EVENT LISTENERS SETUP
// ============================================
function setupEventListeners() {
  // Tab buttons
  document.getElementById('adminLoginTab').addEventListener('click', showAdminLoginForm);
  document.getElementById('createAdminTab').addEventListener('click', showCreateAdminForm);
  document.getElementById('studentLoginTab').addEventListener('click', showStudentLoginForm);
  
  // Login buttons
  document.getElementById('adminLoginBtn').addEventListener('click', handleAdminLogin);
  document.getElementById('createAdminBtn').addEventListener('click', handleCreateAdmin);
  document.getElementById('studentLoginBtn').addEventListener('click', handleStudentLogin);
  
  // Logout buttons
  document.getElementById('logoutAdmin').addEventListener('click', handleLogout);
  document.getElementById('logoutStudent').addEventListener('click', handleLogout);
  
  // Enter key support
  document.getElementById('adminEmail').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleAdminLogin();
  });
  
  document.getElementById('adminPassword').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleAdminLogin();
  });
  
  document.getElementById('student_id').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleStudentLogin();
  });
  
  document.getElementById('newAdminPassword').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleCreateAdmin();
  });
}

// ============================================
// TAB SWITCHING FUNCTIONS
// ============================================

/**
 * Show Admin Login Form
 */
function showAdminLoginForm() {
  // Hide all forms
  document.getElementById('adminLoginForm').classList.remove('hidden');
  document.getElementById('createAdminForm').classList.add('hidden');
  document.getElementById('studentLoginForm').classList.add('hidden');
  
  // Update tab button states
  document.getElementById('adminLoginTab').classList.add('active');
  document.getElementById('createAdminTab').classList.remove('active');
  document.getElementById('studentLoginTab').classList.remove('active');
  
  // Clear message
  clearMessage();
  
  console.log('📋 Showing Admin Login form');
}

/**
 * Show Create Admin Account Form
 */
function showCreateAdminForm() {
  // Hide all forms
  document.getElementById('adminLoginForm').classList.add('hidden');
  document.getElementById('createAdminForm').classList.remove('hidden');
  document.getElementById('studentLoginForm').classList.add('hidden');
  
  // Update tab button states
  document.getElementById('adminLoginTab').classList.remove('active');
  document.getElementById('createAdminTab').classList.add('active');
  document.getElementById('studentLoginTab').classList.remove('active');
  
  // Clear message
  clearMessage();
  
  console.log('📋 Showing Create Admin Account form');
}

/**
 * Show Student Login Form
 */
function showStudentLoginForm() {
  // Hide all forms
  document.getElementById('adminLoginForm').classList.add('hidden');
  document.getElementById('createAdminForm').classList.add('hidden');
  document.getElementById('studentLoginForm').classList.remove('hidden');
  
  // Update tab button states
  document.getElementById('adminLoginTab').classList.remove('active');
  document.getElementById('createAdminTab').classList.remove('active');
  document.getElementById('studentLoginTab').classList.add('active');
  
  // Clear message
  clearMessage();
  
  console.log('📋 Showing Student Login form');
}

// ============================================
// ADMIN ACCOUNT CREATION
// ============================================

/**
 * Handle Create Admin Account
 */
async function handleCreateAdmin() {
  const name = document.getElementById('newAdminName').value.trim();
  const email = document.getElementById('newAdminEmail').value.trim();
  const password = document.getElementById('newAdminPassword').value;
  const college = document.getElementById('newAdminCollege').value.trim();
  
  const createBtn = document.getElementById('createAdminBtn');
  
  // Validation
  if (!name || !email || !password || !college) {
    showMessage('Please fill in all fields', 'error');
    return;
  }
  
  if (password.length < 6) {
    showMessage('Password must be at least 6 characters long', 'error');
    return;
  }
  
  if (!isValidEmail(email)) {
    showMessage('Please enter a valid email address', 'error');
    return;
  }
  
  // Disable button during processing
  createBtn.disabled = true;
  createBtn.textContent = 'Creating Account...';
  
  try {
    console.log('📝 Creating admin account for:', email);
    
    // Step 1: Create user in Supabase Auth
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email: email,
      password: password,
    });
    
    if (authError) {
      throw new Error(authError.message);
    }
    
    console.log('✅ Auth user created:', authData.user.id);
    
    // Step 2: Store admin details in 'admins' table
    const { data: adminData, error: adminError } = await supabase
      .from('admins')
      .insert([
        {
          user_id: authData.user.id,
          name: name,
          email: email,
          college: college,
          role: 'admin',
          created_at: new Date().toISOString()
        }
      ])
      .select();
    
    if (adminError) {
      console.error('❌ Error storing admin details:', adminError);
      throw new Error('Failed to store admin details: ' + adminError.message);
    }
    
    console.log('✅ Admin details stored:', adminData);
    
    // Success!
    showMessage('Admin account created successfully! Please check your email to verify your account, then login.', 'success');
    
    // Clear form
    document.getElementById('newAdminName').value = '';
    document.getElementById('newAdminEmail').value = '';
    document.getElementById('newAdminPassword').value = '';
    document.getElementById('newAdminCollege').value = '';
    
    // Switch to login form after 3 seconds
    setTimeout(() => {
      showAdminLoginForm();
    }, 3000);
    
  } catch (error) {
    console.error('❌ Error creating admin account:', error);
    showMessage('Error: ' + error.message, 'error');
  } finally {
    createBtn.disabled = false;
    createBtn.textContent = 'Create Admin Account';
  }
}

// ============================================
// ADMIN LOGIN
// ============================================

/**
 * Handle Admin Login
 */
async function handleAdminLogin() {
  const email = document.getElementById('adminEmail').value.trim();
  const password = document.getElementById('adminPassword').value;
  
  const loginBtn = document.getElementById('adminLoginBtn');
  
  // Validation
  if (!email || !password) {
    showMessage('Please enter email and password', 'error');
    return;
  }
  
  // Disable button during processing
  loginBtn.disabled = true;
  loginBtn.textContent = 'Logging in...';
  
  try {
    console.log('🔐 Attempting admin login for:', email);
    
    // Step 1: Sign in with Supabase Auth
    const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
      email: email,
      password: password,
    });
    
    if (authError) {
      throw new Error(authError.message);
    }
    
    console.log('✅ Admin authenticated:', authData.user.id);
    
    // Step 2: Get admin details from 'admins' table
    const { data: adminData, error: adminError } = await supabase
      .from('admins')
      .select('*')
      .eq('user_id', authData.user.id)
      .single();
    
    if (adminError || !adminData) {
      throw new Error('Admin details not found. Please contact support.');
    }
    
    console.log('✅ Admin details loaded:', adminData);
    
    // Store current user info
    currentUser = {
      ...adminData,
      authUser: authData.user
    };
    currentUserType = 'admin';
    
    // Store in sessionStorage for persistence
    sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
    sessionStorage.setItem('currentUserType', 'admin');
    
    // ✅ Store login state in localStorage for auth flow
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify({
      id: currentUser.user_id,
      name: currentUser.name,
      email: currentUser.email,
      type: 'admin',
      loginTime: new Date().toISOString()
    }));
    
    // Success!
    showMessage('Login successful! Redirecting...', 'success');
    
    // ✅ DIRECT redirect to admin dashboard (stay on login.html)
    setTimeout(() => {
      showAdminDashboard();
    }, 500);
    
  } catch (error) {
    console.error('❌ Admin login error:', error);
    showMessage('Login failed: ' + error.message, 'error');
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = 'Login as Admin';
  }
}

// ============================================
// STUDENT LOGIN
// ============================================

/**
 * Handle Student Login
 */
async function handleStudentLogin() {
  const roll = document.getElementById('student_id').value.trim();
  
  const loginBtn = document.getElementById('studentLoginBtn');
  
  // Validation
  if (!roll) {
    showMessage('Please enter your roll number', 'error');
    return;
  }
  
  // Disable button during processing
  loginBtn.disabled = true;
  loginBtn.textContent = 'Checking...';
  
  try {
    console.log('🔐 Attempting student login for:', roll);
    
    // ✅ STEP 1: Check if student authentication is enabled
    const authEnabled = await isStudentAuthEnabled(true); // Force refresh
    
    if (!authEnabled) {
      console.log('🚫 Student authentication is disabled by admin');
      throw new Error('Student authentication is currently disabled by admin. Please contact your administrator.');
    }
    
    console.log('✅ Student authentication is enabled, proceeding...');
    loginBtn.textContent = 'Logging in...';
    
    // STEP 2: Find student in database - ✅ Use correct column name
    const { data: studentData, error: studentError } = await supabase
      .from('students')
      .select('*')
      .eq('roll_number', roll)
      .single();
    
    if (studentError || !studentData) {
      throw new Error('Invalid roll number or student not found');
    }
    
    console.log('✅ Student found:', studentData);
    
    // Store current user info
    currentUser = studentData;
    currentUserType = 'student';
    
    // Store in sessionStorage for persistence
    sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
    sessionStorage.setItem('currentUserType', 'student');
    
    // ✅ Store login state in localStorage (use database ID)
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify({
      id: studentData.id,  // ← Use database ID for attendance queries
      name: studentData.name,
      roll_number: studentData.roll_number,
      type: 'student',
      loginTime: new Date().toISOString()
    }));
    
    // Success!
    showMessage('Login successful! Redirecting...', 'success');
    
    // ✅ DIRECT redirect to student dashboard (stay on login.html)
    setTimeout(() => {
      showStudentDashboard();
    }, 500);
    
  } catch (error) {
    console.error('❌ Student login error:', error);
    showMessage('Login failed: ' + error.message, 'error');
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = 'Login as Student';
  }
}

// ============================================
// SESSION MANAGEMENT
// ============================================

/**
 * Check for existing session
 */
async function checkExistingSession() {
  try {
    // Check Supabase session
    const { data: { session } } = await supabase.auth.getSession();
    
    if (session) {
      console.log('✅ Existing session found');
      
      // Check sessionStorage for user type
      const storedUserType = sessionStorage.getItem('currentUserType');
      const storedUser = sessionStorage.getItem('currentUser');
      
      if (storedUserType === 'admin' && storedUser) {
        currentUser = JSON.parse(storedUser);
        currentUserType = 'admin';
        showAdminDashboard();
      }
    } else {
      // Check if student was logged in
      const storedUserType = sessionStorage.getItem('currentUserType');
      const storedUser = sessionStorage.getItem('currentUser');
      
      if (storedUserType === 'student' && storedUser) {
        currentUser = JSON.parse(storedUser);
        currentUserType = 'student';
        showStudentDashboard();
      }
    }
  } catch (error) {
    console.error('❌ Error checking session:', error);
  }
}

/**
 * Handle Logout
 */
async function handleLogout() {
  try {
    console.log('🚪 Logging out...');
    
    // ✅ Clear localStorage login state
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(LEGACY_USER_STORAGE_KEY);
    
    // Sign out from Supabase if admin
    if (currentUserType === 'admin') {
      await supabase.auth.signOut();
    }
    
    // Clear session data
    currentUser = null;
    currentUserType = null;
    sessionStorage.removeItem('currentUser');
    sessionStorage.removeItem('currentUserType');
    
    // ✅ Redirect to login page
    window.location.href = 'login.html';
    
  } catch (error) {
    console.error('❌ Logout error:', error);
  }
}

// ============================================
// DASHBOARD DISPLAY FUNCTIONS
// ============================================

// ============================================
// ADMIN DASHBOARD BUTTON HANDLERS
// ============================================

document.addEventListener('DOMContentLoaded', () => {

  // Add New Student
  const addStudentBtn = document.getElementById('addStudentBtn');
  const addStudentModal = document.getElementById('addStudentModal');

  if (addStudentBtn && addStudentModal) {
    addStudentBtn.addEventListener('click', () => {
      console.log('➕ Add Student button clicked');
      addStudentModal.style.display = 'block';
    });
  }

  // View Students
  const viewStudentsBtn = document.getElementById('viewStudentsBtn');
  const studentsListModal = document.getElementById('studentsListModal');

  if (viewStudentsBtn && studentsListModal) {
    viewStudentsBtn.addEventListener('click', () => {
      studentsListModal.style.display = 'block';
    });
  }

});


/**
 * Show Admin Dashboard
 */
function showAdminDashboard() {
  document.getElementById('loginSection').style.display = 'none';
  document.getElementById('adminDashboard').style.display = 'block';
  document.getElementById('studentDashboard').style.display = 'none';
  
  console.log('✅ Admin dashboard shown for:', currentUser.name);
  
  // Trigger dashboard data load (if function exists in script.js)
  if (typeof updateDashboard === 'function') {
    updateDashboard();
  }
}

/**
 * Show Student Dashboard
 */
function showStudentDashboard() {
  document.getElementById('loginSection').style.display = 'none';
  document.getElementById('adminDashboard').style.display = 'none';
  document.getElementById('studentDashboard').style.display = 'block';
  
  console.log('✅ Student dashboard shown for:', currentUser.name);
  
  // Trigger student dashboard data load (if function exists in script.js)
  if (typeof updateStudentDashboard === 'function') {
    updateStudentDashboard();
  }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Show message to user
 */
function showMessage(message, type) {
  const messageDiv = document.getElementById('loginMessage');
  const className = type === 'error' ? 'error-message' : 'success-message';
  messageDiv.innerHTML = `<div class="${className}">${message}</div>`;
}

/**
 * Clear message
 */
function clearMessage() {
  document.getElementById('loginMessage').innerHTML = '';
}

/**
 * Validate email format
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// ============================================
// EXPORT FOR USE IN OTHER FILES
// ============================================
window.currentUser = currentUser;
window.currentUserType = currentUserType;
window.handleLogout = handleLogout;
window.getCurrentUser = () => currentUser;
window.getCurrentUserType = () => currentUserType;

console.log('✅ Login module loaded successfully');
