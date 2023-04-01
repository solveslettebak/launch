import yaml
import json

fname = 'SLconsole_menus'

data = json.load(open(fname+".json",'r'))

yaml.dump(data, open(fname+'.yaml','w'))


