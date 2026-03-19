"""
Root-level Streamlit entry point.
This wrapper ensures imports work correctly on Streamlit Cloud.
"""
import sys
from pathlib import Path

# Ensure repo root is in Python path
repo_root = Path(__file__).parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import and run the actual app
from app.streamlit_app import *  # noqa: F401, F403
