import os

path_ph = '/home/operator-mcr/.phoebus/'
path_git = '/nfs/Linacshare_controlroom/MCR/launcher/shared-cs-studio-phoebus-layouts/'

found = False

for f in os.listdir(path_ph):
  if f.startswith('layout_') or f.startswith('window_'):
    found = True
    command = 'cp ' + path_ph + f + ' ' + path_git + f
    #print(command)
    #os.system(command)

if not found:
  print('No new layouts found')

os.chdir(path_git)
assert os.getcwd() == path_git[:-1]
os.system('git status')


