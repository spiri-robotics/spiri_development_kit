from nicegui import ui
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header

@ui.page('/')
async def home():
    await styles()
    await header()