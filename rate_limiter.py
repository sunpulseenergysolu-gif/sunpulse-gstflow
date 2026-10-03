"""
Rate Limiter & Brute-Force Defense Engine for SunPulse GSTFlow
Tracks failed authentication attempts per Client IP and User, with progressive lockouts:
- 3 failed attempts: 30 seconds lockout
- 5 failed attempts: 5 minutes (300s) lockout
- 10 failed attempts: 1 hour (3600s) lockout
"""

import time
from typing import Tuple, Dict, Any

# Structure: identifier -> {"count": int, "lock_until": float, "last_attempt": float}
_LOGIN_TRACKER: Dict[str, Dict[str, Any]] = {}

def check_login_lockout(client_id: str) -> Tuple[bool, int, int]:
    """
    Checks if a client identifier (IP or Username) is currently locked out.
    Returns: (is_locked: bool, remaining_seconds: int, total_failures: int)
    """
    now = time.time()
    record = _LOGIN_TRACKER.get(client_id)
    if not record:
        return False, 0, 0
    
    lock_until = record.get("lock_until", 0)
    if now < lock_until:
        remaining = int(lock_until - now) + 1
        return True, remaining, record.get("count", 0)
    
    return False, 0, record.get("count", 0)

def record_failed_attempt(client_id: str) -> Tuple[int, int]:
    """
    Records a failed authentication attempt and calculates lockout duration.
    Returns: (lockout_duration_seconds: int, total_failures: int)
    """
    now = time.time()
    record = _LOGIN_TRACKER.setdefault(client_id, {"count": 0, "lock_until": 0, "last_attempt": now})
    
    # If last attempt was more than 2 hours ago, reset failure counter
    if now - record.get("last_attempt", now) > 7200:
        record["count"] = 0

    record["count"] += 1
    record["last_attempt"] = now
    count = record["count"]

    lock_duration = 0
    if count >= 10:
        lock_duration = 3600  # 1 hour
    elif count >= 5:
        lock_duration = 300   # 5 minutes
    elif count >= 3:
        lock_duration = 30    # 30 seconds

    if lock_duration > 0:
        record["lock_until"] = now + lock_duration

    return lock_duration, count

def record_successful_login(client_id: str):
    """
    Clears failed attempt history upon successful authentication.
    """
    if client_id in _LOGIN_TRACKER:
        del _LOGIN_TRACKER[client_id]

def get_failed_attempts(client_id: str) -> int:
    return _LOGIN_TRACKER.get(client_id, {}).get("count", 0)
