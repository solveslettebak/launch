import os
import sys

path_ph = '/home/operator-mcr/.phoebus/'
path_git = '/nfs/Linacshare_controlroom/MCR/launcher/shared-cs-studio-phoebus-layouts/'

found = False

print('\n')

print('This will copy files layout_* and window_* to',path_git,'and execute git add, commit and push. You need to supply your credentials.')
i = input('Proceed? (y/n)')
if not i.lower() == 'y':
  sys.exit(0)

for f in os.listdir(path_ph):
  if f.startswith('layout_') or f.startswith('window_'):
    found = True
    command = 'mv ' + path_ph + f + ' ' + path_git + f
    print('Found',f,'- moving to',path_git)
    os.system(command)

if not found:
  input('No new layouts found. Press enter to exit')
  sys.exit(0)

print('\n')

os.chdir(path_git)
assert os.getcwd() == path_git[:-1]
message = input('git commit message (or ctrl+c to abort): ')
if False:
  os.system('git add .')
  os.system('git commit -m "'+message+'"')
  os.system('git push')

input('Verify above output messages, and hit enter to exit')
