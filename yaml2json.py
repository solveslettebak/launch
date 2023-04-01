import json
import yaml

f_in = 'SLconsole_menus.yaml'
f_out = 'test.json'

data = yaml.safe_load(open(f_in,'r'))

json.dump(data, open(f_out,'w'))
