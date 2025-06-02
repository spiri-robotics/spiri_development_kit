from nicegui import ui
from spiriSdk.pages.header import header

@ui.page('/settings')
async def settings():
    await header()
    
    ui.label("Set the environment variables here:")