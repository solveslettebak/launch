import os
import sys
import json
from pathlib import Path

# Not sure if used anymore. To be removed.
#settingsPath = os.path.expanduser('~/settings.json')

newSettingsPath = Path.home() / "settings.json"

current_OS = 'linux' if not sys.platform.lower().startswith('win') else 'windows'

# TODO : use pathlib, and keep main path here.

# Use JSONDecoder to parse multiple JSON objects
def parse_multiple_json(data):
    decoder = json.JSONDecoder()
    pos = 0
    objects = []
    while pos < len(data):
        json_obj, pos = decoder.raw_decode(data, pos)
        objects.append(json_obj)
        # Skip any whitespace between JSON objects
        while pos < len(data) and data[pos].isspace():
            pos += 1
    return objects