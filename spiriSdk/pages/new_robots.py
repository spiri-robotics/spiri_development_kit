from nicegui import ui
from pages.header import header

robots = [1, 2, 3]

@ui.page('/new_robots')
async def new_robots():

    ui.label('this is the new robots page yayyyy')