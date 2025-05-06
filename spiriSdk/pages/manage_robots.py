from nicegui import ui
from pages.header import header

@ui.page('/manage_robots')
async def manage_robots():
    await header()