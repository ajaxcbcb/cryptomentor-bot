"""
Run Full Broadcast - Automated
Menjalankan broadcast otomatis dengan konfirmasi
"""

import subprocess
import sys

def run_full_broadcast():
    """Run full broadcast with automatic confirmation"""
    
    print("="*60)
    print("FULL BROADCAST - AUTOMATED EXECUTION")
    print("="*60)
    print("\n⚠️  WARNING: This will send to 1,228 users!")
    print("\nStarting broadcast in 3 seconds...")
    
    import time
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("\n🚀 LAUNCHING BROADCAST...\n")
    
    # Run the test script with automatic input
    # Input: "3" for full broadcast, then "BROADCAST" to confirm
    process = subprocess.Popen(
        ['python', 'test_social_proof_live.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send inputs
    stdout, stderr = process.communicate(input="3\nBROADCAST\n")
    
    # Print output
    print(stdout)
    
    if stderr:
        print("\n⚠️  Errors:")
        print(stderr)
    
    print("\n" + "="*60)
    print("BROADCAST EXECUTION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        run_full_broadcast()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
