import sys
import os

# Add project root to path for imports
# Project structure: claw-agent/ -> claw-gateway/ -> tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
