from nicegui import ui
from spiriSdk.pages.header import header

@ui.page('/tools')
async def tools():
    await header()