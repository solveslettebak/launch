"""
Improvements to be made:
- More control over the git commands and their return, to handle errors
- Handle a wrong password
- Some check to verify the correct file is overwritten. Check text similarity etc. Display verification of this before moving files. (new files vs. overwritten files, etc.. and if text similarity is close, somehow suggest overwriting..? might be tricky with indiv. number difference...

"""

import os
import sys

path_ph = '/home/operator-mcr/.phoebus/'
path_git = '/nfs/Linacshare_controlroom/MCR/launcher/shared-cs-studio-phoebus-layouts/'

found = False

print('\n')

print('This will move files layout_* and window_* from:',path_ph)
print('to:',path_git)
print('and execute git add, commit and push. You need to supply your credentials.\n')
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

os.system('git add -A')
os.system('git commit -m "'+message+'"')
os.system('git push')

input('Verify above output messages, and hit enter to exit')
