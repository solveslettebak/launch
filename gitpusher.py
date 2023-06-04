import os
import sys

path_ph = '/home/operator-mcr/.phoebus/'
path_git = '/nfs/Linacshare_controlroom/MCR/launcher/' # shared-cs-studio-phoebus-layouts/

found = False

print('\n')

for f in os.listdir(path_ph):
  if f.startswith('layout_') or f.startswith('window_'):
    found = True
    command = 'mv ' + path_ph + f + ' ' + path_git + f
    print('Found',f,'- moving to',path_git)
    os.system(command)

if not found:
  print('No new layouts found')
  sys.exit(0)

print('\n')

os.chdir(path_git)
assert os.getcwd() == path_git[:-1]
message = input('git commit message (or ctrl+c to abort): ')
os.system('git add .')
os.system('git commit -m "'+message+'"')
os.system('git push')
