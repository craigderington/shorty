#! /usr/bin/python
# activate_this = "/Users/craigderington/Public/shorty/venv/bin/activate_this.py"
# execfile(activate_this, dict(__file__=activate_this))

import os
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/Users/craigderington/Public/pyshorty")

from app import app as application
application.secret_key = os.urandom(64)


