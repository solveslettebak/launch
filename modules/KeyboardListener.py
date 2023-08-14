import pyxhook

# Evil snooping-on-the-keyboard class for sinister purposes
class KeyboardListener:
    def __init__(self):
        self.hookman = pyxhook.HookManager()
        self.hookman.KeyDown = self.kbevent
        self.hookman.KeyUp = self.kbevent
        self.hookman.HookKeyboard()
        self.hookman.start()

        self.shortcuts = {} # Maps key combinations to functions. tuple of string : function - ex: ('Alt','F1') : <function>
        self.function_arguments = {} # Keeps arguments for each function. function : string  - ex: <function> : "python /path/application.py"

        self.combos = {'Ctrl':False, 'Alt':False, 'Shift':False,} 

        self.registerShortcut(('F9',), self.example_handler, '') # example handler. Remove/overwrite.. Note: first argument must be tuple, so remember the comma: ('F12',)
        self.registerShortcut(('Ctrl','F12'), self.example_handler, '') # example handler. Remove/overwrite..

    # Handles keypresses. Keeps track of function key states, and calls registered functions when it detects a shortcut pressed.
    def kbevent(self,event):

        keydown = event.MessageName == 'key down'

        if event.Key.startswith('Control'):
            self.combos['Ctrl'] = keydown

        if event.Key.startswith('Alt'):
            self.combos['Alt'] = keydown

        if event.Key.startswith('Shift'):
            self.combos['Shift'] = keydown

        for value in self.shortcuts.keys():
            for key in value:
                if key in ['Ctrl','Alt','Shift']: 
                    if not self.combos[key]:
                        break
                if key == event.Key and keydown:
                    for i in self.combos.keys():
                        #print('i',i,':',self.combos[i],' ',(i not in value))
                        if self.combos[i] and (i not in value):
                            #print('\n\nasdf\n\n')
                            return
                    fn = self.shortcuts[value]
                    arg = self.function_arguments[fn]
                    fn(arg)
                
    def example_handler(self, arg):
        print('\n\nwheeee\n\n')

    # shortcut: tuple of names for the keys. ex: ('Ctrl','F12')
    # callback: function to execute
    # args: To be changed, but now: a string value to pass to the menu click handler.
    def registerShortcut(self,shortcut,callback, args): # should change to a **kwargs here, and make that the way i handle all menu clicks, instead of the horrible double lambda BS
        self.shortcuts[shortcut] = callback
        self.function_arguments[callback] = args

    def stoplistening(self):
        self.hookman.cancel()
