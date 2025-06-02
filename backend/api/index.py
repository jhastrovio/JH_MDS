# backend/api/index.py

import sys
import os
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app import app

# This is what Vercel looks for
handler = app
