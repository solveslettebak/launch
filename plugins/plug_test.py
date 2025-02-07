import plugin_mod as pm
import sys

COUNT = 5

# if returns 0, application closes.
def loop(caller):
    global COUNT
    print('Hello from loop:',COUNT)
    COUNT = COUNT - 1

    caller.ping()
    caller.setMenu(menu_ID=0, name='veni vidi vici: ' + str(COUNT), link='asdf')
    
    return COUNT

def init():
    print('Initializing')
    
# TODO:
def quit():
    print('Time to die...')

# plugin_mod verifies this with correct ID and command before passing on here.
def msg_handler(command, **kw):
    print(command)

# this call is blocking.
pm.start(sys.argv[1], init, loop, quit, msg_handler)

startcount = pm.loadSetting('startcount')
if startcount == None:
    startcount = str(0)
pm.saveSetting('startcount', startcount)
print('This plugin was started',int(startcount),'times before')

