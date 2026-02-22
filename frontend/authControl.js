// ============================================
// AUTH CONTROL MODULE
// ============================================
// Centralized student authentication control
// Checks Supabase system_settings table
// ============================================

import { supabase } from './supabaseClient.js';

// ============================================
// CACHE FOR PERFORMANCE
// ============================================
let authStatusCache = {
  enabled: true,
  lastChecked: null,
  cacheDuration: 30000 // 30 seconds cache
};

// ============================================
// CHECK IF STUDENT AUTH IS ENABLED
// ============================================
/**
 * Check if student authentication is currently enabled
 * Uses cache to reduce database queries
 * @param {boolean} forceRefresh - Force refresh from database
 * @returns {Promise<boolean>} - true if enabled, false if disabled
 */
export async function isStudentAuthEnabled(forceRefresh = false) {
  try {
    const now = Date.now();
    
    // Use cache if valid and not forcing refresh
    if (!forceRefresh && 
        authStatusCache.lastChecked && 
        (now - authStatusCache.lastChecked) < authStatusCache.cacheDuration) {
      console.log('📦 Using cached auth status:', authStatusCache.enabled);
      return authStatusCache.enabled;
    }
    
    // Fetch from database
    console.log('🔍 Checking student auth status from database...');
    const { data, error } = await supabase
      .from('system_settings')
      .select('student_auth_enabled')
      .eq('id', 1)
      .single();
    
    if (error) {
      console.error('❌ Error checking auth status:', error);
      // Default to enabled on error (fail-safe)
      return true;
    }
    
    const isEnabled = data?.student_auth_enabled ?? true;
    
    // Update cache
    authStatusCache = {
      enabled: isEnabled,
      lastChecked: now,
      cacheDuration: 30000
    };
    
    console.log('✅ Student auth status:', isEnabled ? 'ENABLED' : 'DISABLED');
    return isEnabled;
    
  } catch (error) {
    console.error('❌ Exception checking auth status:', error);
    // Default to enabled on error (fail-safe)
    return true;
  }
}

// ============================================
// UPDATE STUDENT AUTH STATUS (ADMIN ONLY)
// ============================================
/**
 * Update student authentication status
 * Should only be called by admin
 * @param {boolean} enabled - true to enable, false to disable
 * @param {string} adminId - ID of admin making the change
 * @returns {Promise<boolean>} - true if successful
 */
export async function updateStudentAuthStatus(enabled, adminId = null) {
  try {
    console.log('🔧 Updating student auth status to:', enabled ? 'ENABLED' : 'DISABLED');
    
    const updateData = {
      student_auth_enabled: enabled,
      updated_at: new Date().toISOString()
    };
    
    if (adminId) {
      updateData.updated_by = adminId;
    }
    
    // Use UPDATE instead of UPSERT to avoid RLS issues
    const { data, error } = await supabase
      .from('system_settings')
      .update(updateData)
      .eq('id', 1)
      .select();
    
    if (error) {
      console.error('❌ Error updating auth status:', error);
      throw error;
    }
    
    if (!data || data.length === 0) {
      throw new Error('No rows updated. System settings row might not exist.');
    }
    
    // Clear cache to force refresh
    authStatusCache.lastChecked = null;
    
    console.log('✅ Student auth status updated successfully');
    return true;
    
  } catch (error) {
    console.error('❌ Exception updating auth status:', error);
    throw error;
  }
}

// ============================================
// CLEAR CACHE (FOR TESTING)
// ============================================
/**
 * Clear the auth status cache
 * Useful for testing or forcing immediate refresh
 */
export function clearAuthCache() {
  authStatusCache.lastChecked = null;
  console.log('🗑️ Auth cache cleared');
}

// ============================================
// GET AUTH STATUS WITH DETAILS
// ============================================
/**
 * Get detailed auth status information
 * @returns {Promise<object>} - Auth status with metadata
 */
export async function getAuthStatusDetails() {
  try {
    const { data, error } = await supabase
      .from('system_settings')
      .select('*')
      .eq('id', 1)
      .single();
    
    if (error) throw error;
    
    return {
      enabled: data.student_auth_enabled,
      updatedAt: data.updated_at,
      updatedBy: data.updated_by
    };
    
  } catch (error) {
    console.error('❌ Error getting auth details:', error);
    return {
      enabled: true,
      updatedAt: null,
      updatedBy: null
    };
  }
}

// ============================================
// EXPORT FOR GLOBAL ACCESS
// ============================================
// Make functions available globally for non-module scripts
if (typeof window !== 'undefined') {
  window.isStudentAuthEnabled = isStudentAuthEnabled;
  window.updateStudentAuthStatus = updateStudentAuthStatus;
  window.clearAuthCache = clearAuthCache;
  window.getAuthStatusDetails = getAuthStatusDetails;
}

console.log('✅ Auth Control Module loaded');
