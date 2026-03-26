"""
Simple Automaton Client for Python
Uses send-task.js (proven working) via subprocess
"""

import subprocess
import json
import time
import sqlite3
from pathlib import Path

class AutomatonSimpleClient:
    def __init__(self, automaton_dir="C:/Users/dragon/automaton"):
        """
        Initialize simple Automaton client
        
        Args:
            automaton_dir: Path to Automaton directory
        """
        self.automaton_dir = Path(automaton_dir)
        self.send_task_script = self.automaton_dir / "send-task.js"
        self.db_path = "C:/root/.automaton/state.db"
        
        # Verify send-task.js exists
        if not self.send_task_script.exists():
            raise FileNotFoundError(f"send-task.js not found at {self.send_task_script}")
    
    def send_task(self, task_content, wait_for_response=True, timeout=120):
        """
        Send task to Automaton using send-task.js
        
        Args:
            task_content: The task/question to send
            wait_for_response: Whether to wait for response
            timeout: Max seconds to wait (default: 2 minutes)
        
        Returns:
            dict: {
                'success': bool,
                'task_id': str,
                'response': str (if wait_for_response=True),
                'error': str (if failed)
            }
        """
        try:
            # Run send-task.js
            result = subprocess.run(
                ['node', 'send-task.js', task_content],
                cwd=str(self.automaton_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"send-task.js failed: {result.stderr}"
                }
            
            # Parse task ID from output
            task_id = self._extract_task_id(result.stdout)
            
            response_data = {
                'success': True,
                'task_id': task_id,
                'response': None
            }
            
            if wait_for_response and task_id:
                response = self._wait_for_response(task_id, timeout)
                response_data['response'] = response
            
            return response_data
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'send-task.js timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_task_id(self, output):
        """Extract task ID from send-task.js output"""
        for line in output.split('\n'):
            if 'Task ID:' in line:
                return line.split('Task ID:')[1].strip()
        return None
    
    def _wait_for_response(self, task_id, timeout):
        """
        Wait for Automaton to process task and return response
        
        Args:
            task_id: Task ID to wait for
            timeout: Max seconds to wait
        
        Returns:
            str: Response or None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Check if processed
                cursor.execute("""
                    SELECT processed_at FROM inbox_messages WHERE id = ?
                """, (task_id,))
                
                result = cursor.fetchone()
                
                if result and result[0]:
                    # Get response from latest turn
                    cursor.execute("""
                        SELECT thinking FROM turns 
                        WHERE timestamp > (SELECT received_at FROM inbox_messages WHERE id = ?)
                        ORDER BY timestamp DESC LIMIT 1
                    """, (task_id,))
                    
                    turn = cursor.fetchone()
                    conn.close()
                    
                    if turn:
                        return turn[0]
                
                conn.close()
                time.sleep(3)  # Check every 3 seconds
                
            except Exception as e:
                print(f"Error checking response: {e}")
                time.sleep(3)
        
        return None  # Timeout
    
    def get_status(self):
        """Get Automaton status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM turns")
            total_turns = cursor.fetchone()[0]
            
            cursor.execute("SELECT timestamp FROM turns ORDER BY timestamp DESC LIMIT 1")
            last_activity = cursor.fetchone()
            
            conn.close()
            
            return {
                'success': True,
                'total_turns': total_turns,
                'last_activity': last_activity[0] if last_activity else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Test script
if __name__ == "__main__":
    print("=" * 50)
    print("TEST AUTOMATON SIMPLE CLIENT")
    print("=" * 50)
    
    # Initialize
    client = AutomatonSimpleClient()
    
    # Test 1: Send simple task
    print("\n1. Sending test task...")
    result = client.send_task(
        "Hello from Python! Please respond with a short greeting.",
        wait_for_response=True,
        timeout=90
    )
    
    if result['success']:
        print(f"   ✅ Task sent! ID: {result['task_id']}")
        if result['response']:
            print(f"   📬 Response: {result['response'][:200]}...")
        else:
            print("   ⏳ No response (timeout or still processing)")
    else:
        print(f"   ❌ Failed: {result.get('error')}")
    
    # Test 2: Check status
    print("\n2. Checking Automaton status...")
    status = client.get_status()
    
    if status['success']:
        print(f"   Total turns: {status['total_turns']}")
        print(f"   Last activity: {status['last_activity']}")
    else:
        print(f"   ❌ Failed: {status.get('error')}")
    
    print("\n" + "=" * 50)
    print("✅ TEST COMPLETE")
    print("=" * 50)
