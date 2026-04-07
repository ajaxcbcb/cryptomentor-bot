#!/usr/bin/env python3
"""
Comprehensive System Audit Script
Checks for common issues in handlers, callbacks, and flows
"""

import re
import os
from pathlib import Path

class SystemAuditor:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        
    def add_issue(self, category, file, line, description, severity="ERROR"):
        self.issues.append({
            "severity": severity,
            "category": category,
            "file": file,
            "line": line,
            "description": description
        })
    
    def audit_file(self, filepath):
        """Audit a single Python file for common issues"""
        print(f"\n📄 Auditing: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check 1: Missing error handling in async functions
            self.check_error_handling(filepath, content, lines)
            
            # Check 2: Callback patterns
            self.check_callbacks(filepath, content, lines)
            
            # Check 3: Database operations
            self.check_database_ops(filepath, content, lines)
            
            # Check 4: User notifications
            self.check_notifications(filepath, content, lines)
            
            # Check 5: State management
            self.check_state_management(filepath, content, lines)
            
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
    
    def check_error_handling(self, filepath, content, lines):
        """Check for missing try-except blocks in critical functions"""
        # Find async functions
        async_funcs = re.finditer(r'async def (\w+)\(', content)
        
        for match in async_funcs:
            func_name = match.group(1)
            func_start = match.start()
            
            # Find function body (rough estimate)
            func_lines_start = content[:func_start].count('\n')
            
            # Check if function has try-except
            # Look ahead ~50 lines
            func_snippet = '\n'.join(lines[func_lines_start:func_lines_start+50])
            
            if 'try:' not in func_snippet and 'except' not in func_snippet:
                # Check if it's a critical function (contains bot.send, database ops, etc.)
                if any(keyword in func_snippet for keyword in ['bot.send', '.execute()', 'update_', 'save_', 'delete_']):
                    self.add_issue(
                        "Error Handling",
                        filepath,
                        func_lines_start + 1,
                        f"Function '{func_name}' performs critical operations without try-except",
                        "WARNING"
                    )
    
    def check_callbacks(self, filepath, content, lines):
        """Check for callback query handling issues"""
        # Find callback handlers
        callbacks = re.finditer(r'async def (callback_\w+)\(', content)
        
        for match in callbacks:
            func_name = match.group(1)
            func_start = match.start()
            func_lines_start = content[:func_start].count('\n')
            
            # Check if callback answers the query
            func_snippet = '\n'.join(lines[func_lines_start:func_lines_start+30])
            
            if 'query.answer()' not in func_snippet and 'callback_query.answer()' not in func_snippet:
                self.add_issue(
                    "Callback Handling",
                    filepath,
                    func_lines_start + 1,
                    f"Callback '{func_name}' might not answer the query (causes loading spinner)",
                    "WARNING"
                )
    
    def check_database_ops(self, filepath, content, lines):
        """Check for database operation issues"""
        # Find database operations without error handling
        db_ops = re.finditer(r'\.(execute|insert|update|delete|upsert)\(', content)
        
        for match in db_ops:
            op_start = match.start()
            op_lines_start = content[:op_start].count('\n')
            
            # Check if operation is in try-except block
            # Look backwards for try:
            lines_before = lines[max(0, op_lines_start-10):op_lines_start]
            
            has_try = any('try:' in line for line in lines_before)
            
            if not has_try:
                self.add_issue(
                    "Database Operations",
                    filepath,
                    op_lines_start + 1,
                    f"Database operation without try-except block",
                    "WARNING"
                )
    
    def check_notifications(self, filepath, content, lines):
        """Check for user notification issues"""
        # Find send_message calls
        sends = re.finditer(r'(bot|application\.bot)\.send_message\(', content)
        
        for match in sends:
            send_start = match.start()
            send_lines_start = content[:send_start].count('\n')
            
            # Check if send is in try-except
            lines_before = lines[max(0, send_lines_start-5):send_lines_start]
            lines_after = lines[send_lines_start:min(len(lines), send_lines_start+10)]
            
            has_try = any('try:' in line for line in lines_before)
            has_except = any('except' in line for line in lines_after)
            
            if not (has_try and has_except):
                self.add_issue(
                    "User Notifications",
                    filepath,
                    send_lines_start + 1,
                    f"send_message without error handling (user might not get notified of failures)",
                    "INFO"
                )
    
    def check_state_management(self, filepath, content, lines):
        """Check for state management issues"""
        # Find ConversationHandler states
        if 'ConversationHandler' in content:
            # Check if all states are handled
            states_match = re.search(r'states=\{([^}]+)\}', content, re.DOTALL)
            if states_match:
                states_block = states_match.group(1)
                # Count states
                state_count = len(re.findall(r'WAITING_\w+:', states_block))
                print(f"  ℹ️  Found {state_count} conversation states")
    
    def generate_report(self):
        """Generate audit report"""
        print("\n" + "="*80)
        print("AUDIT REPORT")
        print("="*80)
        
        # Group by severity
        errors = [i for i in self.issues if i['severity'] == 'ERROR']
        warnings = [i for i in self.issues if i['severity'] == 'WARNING']
        infos = [i for i in self.issues if i['severity'] == 'INFO']
        
        print(f"\n📊 Summary:")
        print(f"  🔴 Errors: {len(errors)}")
        print(f"  🟡 Warnings: {len(warnings)}")
        print(f"  ℹ️  Info: {len(infos)}")
        
        if errors:
            print(f"\n🔴 ERRORS ({len(errors)}):")
            for issue in errors:
                print(f"  [{issue['category']}] {issue['file']}:{issue['line']}")
                print(f"    {issue['description']}")
        
        if warnings:
            print(f"\n🟡 WARNINGS ({len(warnings)}):")
            for issue in warnings[:10]:  # Show first 10
                print(f"  [{issue['category']}] {issue['file']}:{issue['line']}")
                print(f"    {issue['description']}")
            if len(warnings) > 10:
                print(f"  ... and {len(warnings)-10} more warnings")
        
        if infos:
            print(f"\nℹ️  INFO ({len(infos)}):")
            print(f"  {len(infos)} informational items found")
        
        print("\n" + "="*80)
        
        return {
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len(infos),
            "total": len(self.issues)
        }

def main():
    auditor = SystemAuditor()
    
    # Files to audit
    files_to_audit = [
        "Bismillah/bot.py",
        "Bismillah/app/handlers_autotrade.py",
        "Bismillah/app/handlers_risk_mode.py",
        "Bismillah/app/handlers_community.py",
        "Bismillah/app/handlers_skills.py",
        "Bismillah/app/trading_mode_manager.py",
        "Bismillah/app/autotrade_engine.py",
        "Bismillah/app/scalping_engine.py",
        "Bismillah/app/scheduler.py",
    ]
    
    print("🔍 Starting System Audit...")
    print("="*80)
    
    for filepath in files_to_audit:
        if os.path.exists(filepath):
            auditor.audit_file(filepath)
        else:
            print(f"⚠️  File not found: {filepath}")
    
    # Generate report
    stats = auditor.generate_report()
    
    # Save detailed report
    with open("AUDIT_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# System Audit Report\n\n")
        f.write(f"**Generated:** {__import__('datetime').datetime.now()}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- 🔴 Errors: {stats['errors']}\n")
        f.write(f"- 🟡 Warnings: {stats['warnings']}\n")
        f.write(f"- ℹ️  Info: {stats['infos']}\n")
        f.write(f"- Total Issues: {stats['total']}\n\n")
        
        f.write("## Detailed Findings\n\n")
        for issue in auditor.issues:
            f.write(f"### {issue['severity']}: {issue['category']}\n")
            f.write(f"**File:** `{issue['file']}:{issue['line']}`\n\n")
            f.write(f"{issue['description']}\n\n")
            f.write("---\n\n")
    
    print(f"\n✅ Detailed report saved to: AUDIT_REPORT.md")
    
    return stats['errors'] == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
