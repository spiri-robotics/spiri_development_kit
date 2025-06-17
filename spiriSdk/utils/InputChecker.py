from nicegui import ui
from spiriSdk.utils.daemon_utils import active_sys_ids

class InputChecker:
    def __init__(self):
        self.inputs = {}
        self.isValid = False

    # def addValid(self, i):
    #     self.inputs[i] = True
    #     self.update()

    # def addNotValid(self, i):
    #     self.inputs[i] = False
    #     self.update()

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

    def checkNumber(self, i: ui.number|None, ogValue: int|float = 0):
        self.inputs[i] = False
        if i.value:
            if 'Port' in i.label:
                if i.value >= 1000:
                    self.inputs[i] = True
            elif 'System ID' in i.label:
                if i.value not in active_sys_ids:
                    self.inputs[i] = True
                elif ogValue:
                    if float(i.value) == float(ogValue):
                        self.inputs[i] = True
            else:
                self.inputs[i] = True
        self.update()

    def checkForChanges(self, ogSettings, newSettings):
        self.update()
        if self.isValid == True:
            for key in newSettings:
                if newSettings[key] != ogSettings[key]:
                    return
            self.isValid = False
            return