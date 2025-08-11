from nicegui import ui

from spiriSdk.utils.daemon_utils import active_sys_ids

class InputChecker:
    """A class to check the validity of inputs in a form-like structure."""
    def __init__(self):
        self.inputs = {}
        self.isValid = False

    def add(self, i, valid: bool):
        """Add an input to the checker with its validity status."""
        if valid:
            self.inputs[i] = True
        else:
            self.inputs[i] = False
        self.update()

    def reset(self):
        """Reset the inputs to an empty state."""
        while len(self.inputs) > 1:
            self.inputs.popitem()
            self.update()

    def update(self):
        """Update the validity status based on the current inputs."""
        for v in self.inputs.values():
            if v is False:
                self.isValid = False
                return
        
        self.isValid = True

    def checkSelect(self, i: ui.select):
        """Check the validity of a select input."""
        if i.value:
            self.inputs[i] = True
        else:
            self.inputs[i] = False
        self.update()
    
    def checkText(self, i: ui.input):
        """Check the validity of a text input."""
        if i.value:
            self.inputs[i] = True
        else:
            self.inputs[i] = False
        self.update()

    def checkNumber(self, i: ui.input|None):
        """Check the validity of a number input."""
        self.inputs[i] = False
        if i.value:
            if int(i.value) not in active_sys_ids and str(i.value).isdigit() and float(i.value) > 0 and float(i.value) < 255:
                self.inputs[i] = True
        self.update()