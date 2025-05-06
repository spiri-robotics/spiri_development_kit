from nicegui import ui
from pages.header import header

@ui.page('/new_robots')
async def new_robots():
    await header()