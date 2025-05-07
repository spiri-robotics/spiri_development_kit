from nicegui import ui
from spiriSdk.pages.header import header

@ui.page('/')
async def home():
    await header()