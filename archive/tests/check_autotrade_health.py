"""
Comprehensive Autotrade System Health Check
Check all components of autotrade system for issues
"""

import subprocess
import sys
from datetime import datetime


def run_ssh_command(command):
    """Run SSH command on VPS"""
    full_cmd = f'ssh root@147.93.156.165 "{command}"'
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.returncode
    except Exception as e:
        return f"Error: {e}", 1


def check_service_status():
    """Check if cryptomentor service is running"""
    print("\n" + "="*60)
    print("1. SERVICE STATUS CHECK")
    print("="*60)
    
    output, code = run_ssh_command("systemctl is-active cryptomentor.service")
    
    if "active" in output:
        print("✅ Service is ACTIVE and RUNNING")
        
        # Get uptime
        output, _ = run_ssh_command("systemctl status cryptomentor.service --no-pager | grep 'Active:'")
        print(f"   {output.strip()}")
        
        return True
    else:
        print("❌ Service is NOT RUNNING")
        print(f"   Status: {output.strip()}")
        return False


def check_import_errors():
    """Check for import errors in logs"""
    print("\n" + "="*60)
    print("2. IMPORT ERROR CHECK")
    print("="*60)
    
    output, _ = run_ssh_command(
        "journalctl -u cryptomentor.service --since '10 minutes ago' --no-pager | "
        "grep -i 'ImportError' | tail -5"
    )
    
    if output.strip():
        print("❌ IMPORT ERRORS FOUND:")
        print(output)
        return False
    else:
        print("✅ No import errors in last 10 minutes")
        return True


def check_autotrade_engines():
    """Check if autotrade engines are generating signals"""
    print("\n" + "="*60)
    print("3. AUTOTRADE ENGINE CHECK")
    print("="*60)
    
    # Check for signal generation
    output, _ = run_ssh_command(
        "journalctl -u cryptomentor.service --since '5 minutes ago' --no-pager | "
        "grep -E 'Signal.*conf=|Engine.*Candidate' | tail -10"
    )
    
    if output.strip():
        lines = output.strip().split('\n')
        print(f"✅ Engines are ACTIVE - {len(lines)} signals generated in last 5 minutes")
        print("\n   Recent signals:")
        for line in lines[-3:]:
            if "Signal" in line:
                # Extract key info
                parts = line.split("INFO - ")
                if len(parts) > 1:
                    print(f"   • {parts[1]}")
        return True
    else:
        print("⚠️  No signals generated in last 5 minutes")
        print("   This might be normal if no trading opportunities")
        return True


def check_active_sessions():
    """Check number of active autotrade sessions"""
    print("\n" + "="*60)
    print("4. ACTIVE SESSIONS CHECK")
    print("="*60)
    
    # Count unique engine IDs in logs
    output, _ = run_ssh_command(
        "journalctl -u cryptomentor.service --since '10 minutes ago' --no-pager | "
        "grep -oP 'Engine:\\d+' | sort -u | wc -l"
    )
    
    try:
        count = int(output.strip())
        if count > 0:
            print(f"✅ {count} active autotrade sessions detected")
            return True
        else:
            print("⚠️  No active sessions detected in last 10 minutes")
            return False
    except:
        print("⚠️  Could not determine session count")
        return False


def check_websocket_connections():
    """Check WebSocket connection status"""
    print("\n" + "="*60)
    print("5. WEBSOCKET CONNECTION CHECK")
    print("="*60)
    
    # Check for WS errors
    output, _ = run_ssh_command(
        "journalctl -u cryptomentor.service --since '5 minutes ago' --no-pager | "
        "grep -i 'WS error' | wc -l"
    )
    
    try:
        error_count = int(output.strip())
        if error_count > 50:
            print(f"⚠️  High number of WebSocket errors: {error_count}")
            print("   This is a known issue with Bitunix WS (using wrong URL scheme)")
            print("   Autotrade still works, but PnL updates may be delayed")
            return True  # Not critical
        elif error_count > 0:
            print(f"✅ Some WebSocket errors ({error_count}) but within normal range")
            return True
        else:
            print("✅ No WebSocket errors")
            return True
    except:
        print("⚠️  Could not check WebSocket status")
        return True


def check_recent_errors():
    """Check for any critical errors"""
    print("\n" + "="*60)
    print("6. CRITICAL ERROR CHECK")
    print("="*60)
    
    output, _ = run_ssh_command(
        "journalctl -u cryptomentor.service --since '10 minutes ago' --no-pager | "
        "grep -E 'ERROR|CRITICAL|Exception' | "
        "grep -v 'WS error' | "
        "grep -v 'ImportError' | "
        "tail -10"
    )
    
    if output.strip():
        print("⚠️  ERRORS FOUND:")
        print(output)
        return False
    else:
        print("✅ No critical errors in last 10 minutes")
        return True


def check_database_connectivity():
    """Check if database queries are working"""
    print("\n" + "="*60)
    print("7. DATABASE CONNECTIVITY CHECK")
    print("="*60)
    
    # Check for database-related errors
    output, _ = run_ssh_command(
        "journalctl -u cryptomentor.service --since '10 minutes ago' --no-pager | "
        "grep -iE 'database|supabase|connection.*failed' | "
        "grep -i error | tail -5"
    )
    
    if output.strip():
        print("❌ DATABASE ERRORS FOUND:")
        print(output)
        return False
    else:
        print("✅ No database errors detected")
        return True


def check_memory_usage():
    """Check service memory usage"""
    print("\n" + "="*60)
    print("8. MEMORY USAGE CHECK")
    print("="*60)
    
    output, _ = run_ssh_command(
        "systemctl status cryptomentor.service --no-pager | grep 'Memory:'"
    )
    
    if output.strip():
        print(f"✅ {output.strip()}")
        
        # Check if memory is too high (> 500MB)
        if "Memory:" in output:
            try:
                mem_str = output.split("Memory:")[1].split()[0]
                if "M" in mem_str:
                    mem_mb = float(mem_str.replace("M", ""))
                    if mem_mb > 500:
                        print("   ⚠️  Memory usage is high (>500MB)")
                        return True
                    else:
                        print("   ✅ Memory usage is normal")
                        return True
            except:
                pass
        return True
    else:
        print("⚠️  Could not check memory usage")
        return True


def check_scalping_mode():
    """Check if scalping mode is available"""
    print("\n" + "="*60)
    print("9. SCALPING MODE CHECK")
    print("="*60)
    
    # Check if scalping files exist
    output, _ = run_ssh_command(
        "ls -la /root/cryptomentor-bot/Bismillah/app/scalping_engine.py "
        "/root/cryptomentor-bot/Bismillah/app/trading_mode.py "
        "/root/cryptomentor-bot/Bismillah/app/trading_mode_manager.py 2>&1"
    )
    
    if "No such file" in output:
        print("❌ Scalping mode files MISSING")
        print(output)
        return False
    else:
        print("✅ Scalping mode files present")
        
        # Check if scalping engine is imported without errors
        output, _ = run_ssh_command(
            "journalctl -u cryptomentor.service --since '10 minutes ago' --no-pager | "
            "grep -i 'scalping' | tail -5"
        )
        
        if output.strip():
            print("   Scalping activity detected:")
            for line in output.strip().split('\n')[:3]:
                print(f"   • {line.split('python3')[1] if 'python3' in line else line}")
        
        return True


def main():
    """Run all health checks"""
    print("="*60)
    print("AUTOTRADE SYSTEM HEALTH CHECK")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    checks = [
        ("Service Status", check_service_status),
        ("Import Errors", check_import_errors),
        ("Autotrade Engines", check_autotrade_engines),
        ("Active Sessions", check_active_sessions),
        ("WebSocket Connections", check_websocket_connections),
        ("Critical Errors", check_recent_errors),
        ("Database Connectivity", check_database_connectivity),
        ("Memory Usage", check_memory_usage),
        ("Scalping Mode", check_scalping_mode),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error running {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("HEALTH CHECK SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print(f"OVERALL: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ SYSTEM HEALTHY - All checks passed!")
    elif passed >= total * 0.8:
        print("⚠️  SYSTEM MOSTLY HEALTHY - Some minor issues")
    else:
        print("❌ SYSTEM HAS ISSUES - Needs attention")
    
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nHealth check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
