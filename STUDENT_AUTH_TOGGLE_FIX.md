# Student Authentication Toggle - Fix Documentation

## Problem
The Student Authentication toggle button in the Admin Dashboard was not working because:
1. No event handler was attached to the toggle
2. The `system_settings` table might not exist in the database

## Solution Implemented

### 1. Frontend Changes

#### Updated `frontend/login.js`:
- Added import for `updateStudentAuthStatus` from `authControl.js`
- Added event listener for the `authToggle` checkbox
- Created `handleAuthToggle()` function to handle toggle changes
- Created `loadAuthToggleState()` function to load current state on dashboard load
- Updated `showAdminDashboard()` to load toggle state when dashboard is shown

#### How it works:
1. When admin logs in, the toggle loads its current state from the database
2. When admin clicks the toggle, it updates the `system_settings` table
3. Students attempting to login will check this setting before allowing access
4. If disabled, students see: "Student authentication is currently disabled by admin"

### 2. Database Setup

#### Created `backend/create_system_settings.sql`:
A SQL script that creates the `system_settings` table with:
- `id` (always 1, single row table)
- `student_auth_enabled` (boolean, default TRUE)
- `updated_at` (timestamp)
- `updated_by` (admin user ID)

#### Features:
- Row Level Security (RLS) enabled
- Anyone can read settings
- Only authenticated users can update
- Constraint ensures only one row exists

## Setup Instructions

### Step 1: Run Database Migration

Go to your Supabase SQL Editor and run:
```sql
-- Copy and paste the contents of backend/create_system_settings.sql
```

Or use the Supabase CLI:
```bash
supabase db push backend/create_system_settings.sql
```

### Step 2: Verify Table Creation

In Supabase, check that the `system_settings` table exists with:
```sql
SELECT * FROM system_settings;
```

You should see one row with `student_auth_enabled = true`.

### Step 3: Test the Toggle

1. Login as admin
2. You should see the "Student Authentication" toggle in the dashboard header
3. Click the toggle to disable student authentication
4. Try logging in as a student - you should see an error message
5. Toggle it back on - students should be able to login again

## How It Works

### Admin Side:
```javascript
// When toggle is clicked
handleAuthToggle() {
  // Update database
  await updateStudentAuthStatus(newState, adminId);
  // Show success message
}
```

### Student Side:
```javascript
// When student tries to login
handleStudentLogin() {
  // Check if auth is enabled
  const authEnabled = await isStudentAuthEnabled();
  if (!authEnabled) {
    throw new Error('Student authentication is disabled');
  }
  // Continue with login...
}
```

### Database:
```sql
-- Single row table
system_settings (
  id = 1,
  student_auth_enabled = true/false,
  updated_at = timestamp,
  updated_by = admin_user_id
)
```

## Features

### Caching
The auth status is cached for 30 seconds to reduce database queries:
- First check: Queries database
- Subsequent checks (within 30s): Uses cached value
- Force refresh: Pass `true` to `isStudentAuthEnabled(true)`

### Error Handling
- If database query fails, defaults to ENABLED (fail-safe)
- Toggle reverts to previous state if update fails
- Clear error messages shown to admin

### Security
- Only authenticated users can update settings
- RLS policies enforce access control
- Admin ID is logged with each change

## Testing

### Test 1: Toggle Functionality
1. Login as admin
2. Toggle should show current state (ON by default)
3. Click toggle OFF
4. Should see "Student authentication disabled" message
5. Toggle should stay OFF after page refresh

### Test 2: Student Login Block
1. Disable student authentication (toggle OFF)
2. Try to login as student
3. Should see error: "Student authentication is currently disabled by admin"
4. Enable authentication (toggle ON)
5. Student should be able to login

### Test 3: Persistence
1. Disable authentication
2. Logout and login again as admin
3. Toggle should still be OFF
4. Enable it back

## Troubleshooting

### Toggle doesn't work
- Check browser console for errors
- Verify `system_settings` table exists
- Check RLS policies are enabled

### Students can still login when disabled
- Clear browser cache
- Check if `isStudentAuthEnabled()` is being called
- Verify database value: `SELECT * FROM system_settings;`

### Toggle state not loading
- Check browser console for errors
- Verify admin is logged in
- Check `loadAuthToggleState()` is being called

## Files Modified

1. `frontend/login.js` - Added toggle handlers
2. `frontend/authControl.js` - Already had the logic
3. `backend/create_system_settings.sql` - New database table

## Next Steps

The toggle is now fully functional! Admins can:
- Enable/disable student authentication with one click
- See immediate feedback
- Control student access to the system

Students will:
- See clear error messages when auth is disabled
- Be able to login normally when enabled
- Not be able to bypass the restriction
