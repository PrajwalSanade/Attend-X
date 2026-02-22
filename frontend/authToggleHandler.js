/**
 * Student Authentication Toggle Handler
 * Dedicated module for handling the auth toggle functionality
 */

import { supabase } from './supabaseClient.js';
import { isStudentAuthEnabled, updateStudentAuthStatus } from './authControl.js';

// State management
let isInitialized = false;
let isUpdating = false;

/**
 * Initialize the auth toggle
 * Call this when admin dashboard is shown
 */
export async function initAuthToggle() {
  if (isInitialized) {
    console.log('🔄 Auth toggle already initialized, refreshing state...');
  }
  
  const authToggle = document.getElementById('authToggle');
  if (!authToggle) {
    console.error('❌ Auth toggle element not found');
    return false;
  }
  
  try {
    // Load current state from database
    console.log('📡 Loading auth toggle state...');
    const currentState = await isStudentAuthEnabled(true); // Force refresh
    
    // Update UI
    authToggle.checked = currentState;
    authToggle.disabled = false;
    
    // Remove any existing listeners to prevent duplicates
    const newToggle = authToggle.cloneNode(true);
    authToggle.parentNode.replaceChild(newToggle, authToggle);
    
    // Add event listener
    newToggle.addEventListener('change', handleToggleChange);
    
    isInitialized = true;
    console.log('✅ Auth toggle initialized:', currentState ? 'ENABLED' : 'DISABLED');
    
    return true;
  } catch (error) {
    console.error('❌ Error initializing auth toggle:', error);
    authToggle.disabled = true;
    return false;
  }
}

/**
 * Handle toggle change event
 */
async function handleToggleChange(event) {
  const toggle = event.target;
  const newState = toggle.checked;
  
  // Prevent multiple simultaneous updates
  if (isUpdating) {
    console.warn('⚠️ Update already in progress, ignoring...');
    return;
  }
  
  isUpdating = true;
  
  try {
    console.log('🔄 Updating student auth to:', newState ? 'ENABLED' : 'DISABLED');
    
    // Disable toggle during update
    toggle.disabled = true;
    
    // Get current admin user
    const { data: { session } } = await supabase.auth.getSession();
    const adminId = session?.user?.id;
    
    if (!adminId) {
      throw new Error('Admin session not found');
    }
    
    // Update in database
    await updateStudentAuthStatus(newState, adminId);
    
    // Show success message
    const message = newState 
      ? '✅ Student authentication enabled' 
      : '🚫 Student authentication disabled';
    
    showToggleMessage(message, 'success');
    
    console.log('✅ Auth toggle updated successfully');
    
  } catch (error) {
    console.error('❌ Error updating auth toggle:', error);
    
    // Revert toggle on error
    toggle.checked = !newState;
    
    showToggleMessage('❌ Failed to update: ' + error.message, 'error');
  } finally {
    // Re-enable toggle
    toggle.disabled = false;
    isUpdating = false;
  }
}

/**
 * Show message near the toggle
 */
function showToggleMessage(message, type) {
  // Try to find or create message container
  let messageEl = document.getElementById('authToggleMessage');
  
  if (!messageEl) {
    // Create message element
    messageEl = document.createElement('div');
    messageEl.id = 'authToggleMessage';
    messageEl.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      border-radius: 8px;
      font-weight: 500;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      animation: slideIn 0.3s ease-out;
    `;
    document.body.appendChild(messageEl);
  }
  
  // Set message and style
  messageEl.textContent = message;
  messageEl.style.backgroundColor = type === 'success' ? '#48bb78' : '#f56565';
  messageEl.style.color = 'white';
  messageEl.style.display = 'block';
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    messageEl.style.display = 'none';
  }, 3000);
}

/**
 * Get current toggle state
 */
export function getToggleState() {
  const authToggle = document.getElementById('authToggle');
  return authToggle ? authToggle.checked : null;
}

/**
 * Manually refresh toggle state
 */
export async function refreshToggleState() {
  console.log('🔄 Manually refreshing toggle state...');
  return await initAuthToggle();
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
`;
document.head.appendChild(style);

console.log('✅ Auth Toggle Handler module loaded');
