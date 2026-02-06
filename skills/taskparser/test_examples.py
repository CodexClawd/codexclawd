#!/usr/bin/env python3
"""Test examples for TaskParser"""

import sys
sys.path.insert(0, '/home/boss/.openclaw/workspace/skills/taskparser')

from taskparser import TaskParser


def run_tests():
    """Run test cases and show results"""
    parser = TaskParser()
    
    test_cases = [
        # (input, expected_action, should_have_datetime)
        ("call mom tomorrow", "call", True),
        ("email HR by friday", "email", True),
        ("grocery shopping this weekend", "buy", True),
        ("dentist appointment march 15", "meet", True),
        ("remind me to take meds at 8pm daily", "remind", True),
        ("I should pay the electricity bill by next tuesday", "pay", True),
        ("Don't forget to book the flight", "remind", False),
        ("Need to clean the apartment before weekend", "clean", True),
        ("Gym at 6pm today", "exercise", True),
        ("asap: write that report", "task", True),
    ]
    
    print("Running TaskParser Tests")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for text, expected_action, should_have_dt in test_cases:
        result = parser.parse_intent(text)
        
        action_ok = result['action'] == expected_action
        dt_ok = (result['datetime'] is not None) == should_have_dt
        
        status = "✅" if action_ok and dt_ok else "❌"
        
        print(f"\n{status} Input: \"{text}\"")
        print(f"   Action: {result['action']} (expected: {expected_action})")
        print(f"   Subject: {result['subject']}")
        print(f"   Has datetime: {result['datetime'] is not None} (expected: {should_have_dt})")
        if result['datetime']:
            from datetime import datetime
            dt = datetime.fromisoformat(result['datetime'])
            print(f"   When: {dt.strftime('%Y-%m-%d %H:%M')}")
        
        if action_ok and dt_ok:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
