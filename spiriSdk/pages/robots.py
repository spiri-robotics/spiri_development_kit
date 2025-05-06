from nicegui import ui
from pages.header import header

@ui.page('/tools')
async def tools():
    await header()