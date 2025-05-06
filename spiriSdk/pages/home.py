from nicegui import ui
from pages.header import header

@ui.page('/')
async def home():
    await header()