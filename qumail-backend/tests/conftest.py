"""
pytest configuration file for the QuMail test suite.
This file configures pytest to recognize the app module.
"""

import sys
import os

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))