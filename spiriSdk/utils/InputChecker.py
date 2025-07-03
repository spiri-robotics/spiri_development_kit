from nicegui import ui
from spiriSdk.utils.daemon_utils import active_sys_ids

class InputChecker:
    def __init__(self):
        self.inputs = {}
        self.isValid = False

    def add(self, i, valid: bool):
        if valid:
            self.inputs[i] = True
        else:
            self.inputs[i] = False
        self.update()

    def reset(self):
        while len(self.inputs) > 1:
            self.inputs.popitem()
            self.update()

    def update(self):
        for v in self.inputs.values():
            if v is False:
                self.isValid = False
                return
        
        self.isValid = True

    def checkSelect(self, i: ui.select):
        if i.value:
            self.inputs[i] = True
        else:
            self.inputs[i] = False
        self.update()
    
    def checkText(self, i: ui.input):
        if i.value:
            self.inputs[i] = True
        else:
            self.inputs[i] = False
        self.update()

    def checkNumber(self, i: ui.input|None):
        self.inputs[i] = False
        if i.value:
            if int(i.value) not in active_sys_ids and str(i.value).isdigit() and float(i.value) > 0 and float(i.value) < 256:
                self.inputs[i] = True
        self.update()