#!/usr/bin/env python3
"""
Startup script for the Discord ClickUp Bot.
This script checks dependencies and starts the bot with proper error handling.
"""

import os
import sys
import subprocess
import importlib.util

def check_dependencies():
    """Check if all required dependencies are installed"""
    dependencies = [
        ('discord', 'discord.py'),
        ('aiohttp', 'aiohttp'),
        ('requests', 'requests'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing = []
    
    for module_name, package_name in dependencies:
        if importlib.util.find_spec(module_name) is None:
            missing.append(package_name)
    
    if missing:
        print("❌ Missing dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print()
        print("📦 Install missing dependencies with:")
        print(f"   pip install {' '.join(missing)}")
        print("   or")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_environment():
    """Check if environment file exists and has required variables"""
    if not os.path.exists('.env'):
        print("❌ Error: .env file not found")
        print()
        print("📋 Setup instructions:")
        print("   1. Copy env.example to .env:")
        print("      cp env.example .env")
        print("   2. Edit .env with your API tokens and IDs")
        print("   3. Run this script again")
        return False
    
    # Load and check environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = ['DISCORD_BOT_TOKEN', 'CLICKUP_API_TOKEN', 'CLICKUP_LIST_ID']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print()
            print("📝 Please edit your .env file and add the missing variables")
            return False
        
        return True
        
    except ImportError:
        print("❌ Error: python-dotenv not installed")
        return False

def run_bot():
    """Run the Discord bot"""
    try:
        print("🚀 Starting Discord ClickUp Bot...")
        print("   Press Ctrl+C to stop the bot")
        print()
        
        # Import and run the bot
        from bot import main
        main()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("🤖 Discord ClickUp Bot - Startup")
    print("=" * 40)
    print()
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ All dependencies found")
    print()
    
    # Check environment
    print("🔧 Checking configuration...")
    if not check_environment():
        sys.exit(1)
    print("✅ Configuration looks good")
    print()
    
    # Offer to run test first
    response = input("🧪 Would you like to test ClickUp connection first? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        print()
        try:
            subprocess.run([
                sys.executable,
                os.path.join(os.path.dirname(__file__), 'test_clickup.py')
            ], check=True)
        except subprocess.CalledProcessError:
            print()
            response = input("❓ Test failed. Continue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("👋 Exiting...")
                sys.exit(1)
        except FileNotFoundError:
            print("❌ test_clickup.py not found, skipping test")
        print()
    
    # Run the bot
    run_bot()

if __name__ == "__main__":
    main() 