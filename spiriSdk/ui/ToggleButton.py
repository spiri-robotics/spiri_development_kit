from nicegui import ui

class ToggleButton(ui.button):
    def __init__(self, *args, on_label="on", off_label="off", on_switch=None, off_switch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = True
        self.color = "positive"
        self.on_label = on_label
        self.off_label = off_label
        self.on_switch = on_switch
        self.off_switch = off_switch
        self.on('click', self.toggle)

    async def toggle(self) -> None:
        if self._state:
            await self.on_switch()
        elif not self._state:
            await self.off_switch()
        self._state = not self._state
        self.update()
    
    def update(self) -> None:
        self.color = "positive" if self._state else "warning"
        label = self.on_label if self._state else self.off_label
        self.props(f'color={self.color}')
        self.set_text(label)
        super().update()