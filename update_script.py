import os
import re

file_path = r'd:\cryptomentorAI\Bismillah\app\trade_execution.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update reconcile_position signature
text = text.replace(') -> Tuple[bool, list]:', ') -> Tuple[bool, list, float]:')

# We also need to remove the emergency close based on Qty inside the quantity check
# Around line 212
qty_logic_old = '''    # 1. Quantity check ────────────────────────────────────────────────────────
    if not _within_pct(actual_qty, expected_qty, QTY_TOLERANCE_PCT):
        notes.append(
            f"qty_mismatch actual={actual_qty} expected={expected_qty}"
        )
        # Cannot safely repair qty after entry. Close to protect user.
        try:
            close_side = "SELL" if side.upper() == "LONG" else "BUY"
            await asyncio.to_thread(
                client.place_order,
                symbol,
                close_side,
                actual_qty,
                'market',
                None,
                True,  # reduce_only
            )
            notes.append("emergency_closed")
        except Exception as e:
            notes.append(f"emergency_close_failed: {e}")
        return False, notes'''

qty_logic_new = '''    # 1. Quantity check ────────────────────────────────────────────────────────
    if not _within_pct(actual_qty, expected_qty, QTY_TOLERANCE_PCT):
        notes.append(
            f"qty_mismatch_ignored actual={actual_qty} expected={expected_qty}"
        )
        # Self-healing: we ignore qty mismatch and update to the actual qty from the exchange
        pass'''

if qty_logic_old in text:
    text = text.replace(qty_logic_old, qty_logic_new)
else:
    print('Could not find qty_logic_old')

# Now fix the returns. 
text = text.replace('return False, notes', 'return False, notes, locals().get(\'actual_qty\', 0.0)')
text = text.replace('return True, notes', 'return True, notes, locals().get(\\'actual_qty\\', 0.0)')

# 3. Update execute_trade_standalone
old_call = '''        try:
            healthy, reconcile_notes = await reconcile_position(
                client=client,
                user_id=user_id,
                symbol=symbol,
                side=side,
                expected_qty=quantity,
                expected_tp=levels.tp1,
                expected_sl=levels.sl,
            )'''
new_call = '''        try:
            healthy, reconcile_notes, actual_qty = await reconcile_position(
                client=client,
                user_id=user_id,
                symbol=symbol,
                side=side,
                expected_qty=quantity,
                expected_tp=levels.tp1,
                expected_sl=levels.sl,
            )
            
            # Adopt the actual quantity from the exchange if successful or if ignored
            if actual_qty > 0:
                quantity = actual_qty
                
            '''
text = text.replace(old_call, new_call)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated trade_execution.py')
