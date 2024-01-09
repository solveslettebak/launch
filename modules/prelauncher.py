# Purpose:
#
# Check if a virtual environment setting exists. 
# - If yes: print it to stdout, and return with exit code 0. 
# - Otherwise: return with exit code 1.
#

import sys
import json
from common import settingsPath

try:
  settings = json.load(open(settingsPath))
except:
  sys.exit(1)

if not 'venv' in settings:
  sys.exit(1)

if settings['venv'] == '':
  sys.exit(1)

print(settings['venv'])
sys.exit(0)
