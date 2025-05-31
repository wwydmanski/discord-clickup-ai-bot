#!/usr/bin/env python3
"""
Test script for AI-powered command detection functionality
"""

import sys
import os
import asyncio

# Add parent directory to path to import bot module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bot import is_task_creation_command

async def test_command_detection():
    """Test various inputs for AI-powered command detection"""
    
    # Test cases: (input, expected_result, description)
    test_cases = [
        # Commands - should be detected as commands
        ("dodaj taska", True, "Polish: add task"),
        ("stwórz task", True, "Polish: create task"),
        ("wrzuć to do backlog", True, "Polish: put to backlog"),
        ("task z tego", True, "Polish: task from this"),
        ("zapisz to", True, "Polish: save this"),
        ("task proszę", True, "Polish: task please"),
        ("możesz dodać task?", True, "Polish: can you add task?"),
        ("potrzebuję task", True, "Polish: I need a task"),
        
        ("create task", True, "English: create task"),
        ("add task", True, "English: add task"),
        ("task this", True, "English: task this"),
        ("backlog this", True, "English: backlog this"),
        ("please create task", True, "English: please create task"),
        ("can you make a task?", True, "English: can you make a task?"),
        ("need a task", True, "English: need a task"),
        ("task", True, "English: just 'task'"),
        
        # Natural language commands - should be detected
        ("zrób z tego zadanie", True, "Polish: make this a task"),
        ("save this as a task", True, "English: save as task"),
        ("track this discussion", True, "English: track this"),
        ("zanotuj to sobie", True, "Polish: note this down"),
        
        # Task descriptions - should NOT be detected as commands
        ("Fix login bug with special characters", False, "Direct task description"),
        ("Implement user authentication system", False, "Direct task description"),
        ("Review the new authentication system", False, "Direct task description"),
        ("Update user interface design for mobile", False, "Direct task description"),
        ("Create API documentation for payment endpoints", False, "Direct task description"),
        ("Add unit tests for the shopping cart module", False, "Direct task description"),
        ("Debug performance issues in database queries", False, "Direct task description"),
        ("Refactor authentication middleware", False, "Direct task description"),
        
        # Technical descriptions that might confuse pattern matching
        ("The task is to implement OAuth integration", False, "Contains 'task' but is description"),
        ("We need to task the frontend team with this", False, "Uses 'task' as verb"),
        ("This creates a new task in the system", False, "About task creation but not a command"),
        ("Task management should be improved", False, "About tasks in general"),
        
        # Polish technical descriptions
        ("Napraw błąd logowania na produkcji", False, "Polish: fix login bug on production"),
        ("Zaimplementuj nowy system płatności", False, "Polish: implement new payment system"),
        ("Dodaj walidację do formularza", False, "Polish: add validation to form"),
        ("Stwórz dokumentację API", False, "Polish: create API docs"),
        
        # Edge cases
        ("", False, "Empty string"),
        ("task about authentication system implementation", False, "Task as noun in longer sentence"),
        ("create new authentication flow for users", False, "Create something specific"),
        ("add more features to the dashboard", False, "Add specific features"),
        ("make the system more secure", False, "Make something specific"),
        
        # Ambiguous cases - these might vary depending on AI interpretation
        ("dodaj więcej funkcji", False, "Polish: add more features (specific)"),
        ("create better UX", False, "Create something specific"),
        ("improve performance", False, "Specific improvement task"),
    ]
    
    print("🧪 Testing AI-Powered Command Detection Logic\n")
    print("🤖 Using OpenAI GPT-4o for intent analysis")
    print("-" * 80)
    
    passed = 0
    total = len(test_cases)
    failed_cases = []
    
    for i, (input_text, expected, description) in enumerate(test_cases):
        try:
            result = await is_task_creation_command(input_text)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            
            print(f"{i+1:2d}. {status} | {input_text:<40} | {description}")
            
            if result == expected:
                passed += 1
            else:
                failed_cases.append((input_text, expected, result, description))
                print(f"     Expected: {expected}, Got: {result}")
                
        except Exception as e:
            print(f"{i+1:2d}. 💥 ERROR | {input_text:<40} | {description}")
            print(f"     Error: {e}")
            failed_cases.append((input_text, expected, "ERROR", description))
    
    print("-" * 80)
    print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if failed_cases:
        print(f"\n❌ Failed cases ({len(failed_cases)}):")
        for text, expected, actual, desc in failed_cases:
            print(f"  • '{text}' -> Expected: {expected}, Got: {actual}")
            print(f"    {desc}")
    
    if passed == total:
        print("\n🎉 All tests passed! AI command detection is working perfectly.")
        return True
    elif passed >= total * 0.8:  # 80% threshold for AI-based system
        print(f"\n✅ Good performance! {passed}/{total} tests passed.")
        print("   AI-based systems may have some variation in edge cases.")
        return True
    else:
        print(f"\n⚠️  Performance below threshold. {total-passed} tests failed.")
        print("   Consider reviewing the AI prompt or test cases.")
        return False

async def test_ai_reasoning():
    """Test a few examples and show AI reasoning"""
    print("\n🔍 AI Reasoning Examples:")
    print("-" * 50)
    
    examples = [
        "dodaj taska",
        "Fix login bug", 
        "task z tego",
        "Implement OAuth system"
    ]
    
    for example in examples:
        result = await is_task_creation_command(example)
        print(f"'{example}' -> {'COMMAND' if result else 'TASK_DESCRIPTION'}")

if __name__ == "__main__":
    async def main():
        success = await test_command_detection()
        await test_ai_reasoning()
        return success
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test failed with error: {e}")
        sys.exit(1) 