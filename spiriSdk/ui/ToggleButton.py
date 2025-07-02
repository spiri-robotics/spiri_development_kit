from nicegui import ui

class ToggleButton(ui.button):
    def __init__(self, *args, state=True, on_label="on", off_label="off", on_switch=None, off_switch=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state
        self.on_label = on_label
        self.off_label = off_label
        self.on_switch = on_switch
        self.off_switch = off_switch
        self.on('click', self.toggle)
        self.update()

    async def toggle(self) -> None:
        result = False
        if self.state:
            result = await self.on_switch()
        elif not self.state:
            result = await self.off_switch()
        if(result):
            self.state = not self.state
            self.update()
    
    def update(self) -> None:
        self.color = "negative" if self.state else "positive"
        label = self.on_label if self.state else self.off_label
        self.props(f'color={self.color}')
        self.set_text(label)
        super().update()