import plugin_mod as pm
import sys

updateInProgress = False
updateFlag = False

def remoteUpdateCheck(self):
    global updateInProgress

    if updateFlag: # If this instance initiates the remote update, then we don't listen to that signal. 
        return
    try:
        data = open('update.flag','r').read()[0]
    except OSError:
        print('Problem reading update flag file. Giving up..')
        #self.remoteUpdateTimer.stop()
        
    if data == '0' and updateInProgress: # perform the relaunch on a detected falling edge of the update flag.
        updateInProgress = False # this never worked... comment out perhaps
        print('Remote update signal detected, relaunching..')
        onRelaunch()
        
    if data == '1' and not updateInProgress:
        print('Prepare update..')
        updateInProgress = True

def clearUpdateFlag(self):
    global updateFlag

    updateFlag = False
    # self.setRemoteUpdateTimer.stop()
    try:
        open('update.flag','w+').write('0')
    except OSError:
        print('Problem clearing update flag...')
    print('Relaunching this instance...')
    onRelaunch()

def onInitiateUpdate(self):
    global updateFlag

    print('Initiating remote update of running instances of launcher')
    if updateFlag: # update already in progress.
        return
    #self.updateFlag = True
    #self.setRemoteUpdateTimer = QTimer()
    #self.setRemoteUpdateTimer.start(10*1000)
    #self.setRemoteUpdateTimer.timeout.connect(self.clearUpdateFlag)
    try:
        open('update.flag','w+').write('1')
    except OSError:
        print('Problem setting update flag. Giving up..')
        updateFlag = False
        #self.setRemoteUpdateTimer.stop()
    print('done')


LOOPCOUNT = 0


def onRelaunch():
    pass

# if returns 0, application closes.
def loop(caller):
    print('[Remote relaunch]: hello..')
    return 1

def init():
    print('Initializing')
    
def quit():
    print('Time to die...')

# plugin_mod verifies this with correct ID and command before passing on here.
def msg_handler(command, **kw):
    print('[Remote relaunch]: I have received a message! Here it is:',command)

pm.set_loop_interval(5000)

# this call is blocking.
pm.start(sys.argv[1], init, loop, quit, msg_handler)