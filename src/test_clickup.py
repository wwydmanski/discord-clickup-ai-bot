#!/usr/bin/env python3
"""
Test script to verify ClickUp API connection and credentials.
Run this script to test your ClickUp setup before running the Discord bot.
"""

import os
import sys
import pytest
from dotenv import load_dotenv
from bot import ClickUpClient

pytest.skip("manual integration script", allow_module_level=True)

def test_clickup_connection():
    """Test the ClickUp API connection and create a test task"""
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    api_token = os.getenv('CLICKUP_API_TOKEN')
    list_id = os.getenv('CLICKUP_LIST_ID')
    team_id = os.getenv('CLICKUP_TEAM_ID')
    
    if not api_token:
        print("❌ Error: CLICKUP_API_TOKEN not found in environment variables")
        return False
    
    if not list_id:
        print("❌ Error: CLICKUP_LIST_ID not found in environment variables")
        return False
    
    print("🔧 Testing ClickUp API connection...")
    print(f"   API Token: {'*' * (len(api_token) - 4)}{api_token[-4:]}")
    print(f"   List ID: {list_id}")
    print(f"   Team ID: {team_id or 'Not provided'}")
    print()
    
    try:
        # Initialize ClickUp client
        client = ClickUpClient(
            api_token=api_token,
            list_id=list_id,
            team_id=team_id
        )
        
        # Test team members (if team_id is provided)
        if team_id:
            print("👥 Fetching team members...")
            members = client.get_team_members()
            count = len(members) if members else 0
            if count:
                print(f"   Found {count} team members")
                for member in members[:3]:  # Show first 3 members
                    user = member.get('user', {})
                    print(f"   - {user.get('username', 'Unknown')} ({user.get('email', 'No email')})")
                if count > 3:
                    print(f"   ... and {count - 3} more")
            else:
                print("   No team members found or unable to fetch")
            print()
        
        # Create a test task
        print("📝 Creating test task...")
        test_task_response = client.create_task(
            name="Discord Bot Test Task",
            description="""
**This is a test task created by the Discord ClickUp Bot**

If you can see this task in your ClickUp list, your bot setup is working correctly!

You can safely delete this task.

**Test Details:**
- Created by: Discord Bot Test Script
- Purpose: Verify API connection
- Status: Test successful ✅
            """.strip()
        )
        
        task_id = test_task_response.get('id', 'Unknown')
        task_url = test_task_response.get('url', 'No URL provided')
        
        print("✅ Test task created successfully!")
        print(f"   Task ID: {task_id}")
        print(f"   Task URL: {task_url}")
        print()
        print("🎉 ClickUp integration is working correctly!")
        print("   You can now run the Discord bot with: python bot.py")
        print()
        print("💡 Don't forget to:")
        print("   1. Set up your Discord bot token")
        print("   2. Invite the bot to your Discord server")
        print("   3. Enable Message Content Intent in Discord Developer Portal")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ClickUp connection: {e}")
        print()
        print("🔍 Troubleshooting tips:")
        print("   1. Verify your ClickUp API token is correct")
        print("   2. Check that the List ID exists and you have access to it")
        print("   3. Ensure your ClickUp plan supports API access")
        print("   4. Try visiting the ClickUp list in your browser to confirm access")
        
        return False

def main():
    """Main function"""
    print("🧪 ClickUp Discord Bot - Connection Test")
    print("=" * 50)
    print()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ Error: .env file not found")
        print("   Please create a .env file based on env.example")
        print("   Copy env.example to .env and fill in your credentials")
        sys.exit(1)
    
    success = test_clickup_connection()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 