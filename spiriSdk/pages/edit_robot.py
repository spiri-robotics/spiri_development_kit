from nicegui import ui
from pages.header import header

@ui.page('/edit_robot')
async def edit_robot():

    ui.label('this is the edit robot page')