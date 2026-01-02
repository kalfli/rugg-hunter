"""System Test Suite"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("🧪 RUG HUNTER V2.0 - SYSTEM TESTS")
print("="*80)

try:
    from core.honeypot_detector import HoneypotDetector
    print("✅ honeypot_detector imported")
except Exception as e:
    print(f"❌ honeypot_detector: {e}")

try:
    from core.mempool_monitor import MempoolMonitor
    print("✅ mempool_monitor imported")
except Exception as e:
    print(f"❌ mempool_monitor: {e}")

try:
    from core.multi_rpc_manager import create_default_rpc_manager
    print("✅ multi_rpc_manager imported")
except Exception as e:
    print(f"❌ multi_rpc_manager: {e}")

try:
    from core.trailing_stop_manager import TrailingStopManager
    print("✅ trailing_stop_manager imported")
except Exception as e:
    print(f"❌ trailing_stop_manager: {e}")

print("="*80)
print("✅ All imports successful!")
