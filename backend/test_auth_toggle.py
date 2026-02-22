"""
Test script to verify Student Authentication Toggle functionality
"""
from database_service import get_supabase_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_system_settings_table():
    """Test if system_settings table exists and is accessible"""
    client = get_supabase_client()
    
    try:
        logger.info("Testing system_settings table...")
        
        # Try to read from system_settings
        result = client.table("system_settings").select("*").eq("id", 1).execute()
        
        if result.data:
            logger.info(f"✅ system_settings table exists")
            logger.info(f"   Current state: {result.data[0]}")
            logger.info(f"   student_auth_enabled: {result.data[0].get('student_auth_enabled')}")
            return True
        else:
            logger.warning("⚠️  system_settings table exists but no data found")
            logger.info("   Run backend/create_system_settings.sql in Supabase SQL Editor")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error accessing system_settings table: {e}")
        logger.info("   Please run backend/create_system_settings.sql in Supabase SQL Editor")
        return False

def test_toggle_update():
    """Test updating the auth toggle"""
    client = get_supabase_client()
    
    try:
        logger.info("\nTesting toggle update...")
        
        # Get current state
        current = client.table("system_settings").select("student_auth_enabled").eq("id", 1).single().execute()
        current_state = current.data.get('student_auth_enabled')
        logger.info(f"   Current state: {current_state}")
        
        # Toggle to opposite
        new_state = not current_state
        logger.info(f"   Updating to: {new_state}")
        
        result = client.table("system_settings").update({
            "student_auth_enabled": new_state
        }).eq("id", 1).execute()
        
        if result.data:
            logger.info(f"✅ Toggle updated successfully")
            
            # Toggle back to original
            logger.info(f"   Restoring to: {current_state}")
            client.table("system_settings").update({
                "student_auth_enabled": current_state
            }).eq("id", 1).execute()
            logger.info(f"✅ Restored to original state")
            return True
        else:
            logger.error("❌ Toggle update failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating toggle: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("="*50)
    logger.info("Student Authentication Toggle - Test Suite")
    logger.info("="*50)
    
    # Test 1: Table exists
    table_ok = test_system_settings_table()
    
    if table_ok:
        # Test 2: Can update
        update_ok = test_toggle_update()
        
        if update_ok:
            logger.info("\n" + "="*50)
            logger.info("✅ All tests passed!")
            logger.info("="*50)
            logger.info("\nThe Student Authentication toggle is ready to use.")
            logger.info("Login as admin and try toggling it in the dashboard.")
        else:
            logger.info("\n" + "="*50)
            logger.info("⚠️  Some tests failed")
            logger.info("="*50)
    else:
        logger.info("\n" + "="*50)
        logger.info("❌ Setup required")
        logger.info("="*50)
        logger.info("\nPlease run the following SQL in Supabase SQL Editor:")
        logger.info("   backend/create_system_settings.sql")

if __name__ == "__main__":
    main()
