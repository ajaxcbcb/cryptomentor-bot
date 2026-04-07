# Demo users — special restricted accounts (prank/demo only)
# These users bypass referral requirement but have a $50 balance cap.
# Demo users CANNOT access Community Partners feature.

DEMO_USER_IDS = {1234500001, 1234500002, 1234500003, 1234500004, 1234500005}
DEMO_BALANCE_LIMIT = 50.0  # USD


def is_demo_user(user_id: int) -> bool:
    return int(user_id) in DEMO_USER_IDS


def check_demo_balance_exceeded(user_id: int, current_balance: float) -> bool:
    """Returns True if demo user has exceeded the $50 limit."""
    if not is_demo_user(user_id):
        return False
    return current_balance > DEMO_BALANCE_LIMIT
