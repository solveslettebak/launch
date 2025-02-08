import plugin_mod as pm
import sys

COUNT = 5

global loopcount

# if returns 0, application closes.
def loop(caller):
    global COUNT
    global loopcount
    print('Hello from loop:',COUNT)
    COUNT = COUNT - 1

    caller.ping()
    caller.setMenu(menu_ID=0, name='veni vidi vici: ' + str(COUNT), link='asdf')
    
    loopcount += 1
    pm.saveParameter('loopcount', str(loopcount))
    
    return COUNT

def init():
    print('Initializing')
    
# TODO:
def quit():
    print('Time to die...')

# plugin_mod verifies this with correct ID and command before passing on here.
def msg_handler(command, **kw):
    print(command)
    
loopcount = int(pm.getParameter('loopcount', default=0))

# this call is blocking.
pm.start(sys.argv[1], init, loop, quit, msg_handler)
