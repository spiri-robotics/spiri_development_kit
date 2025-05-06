from nicegui import ui

async def header():
    with ui.header():
        ui.label('My Header')
        ui.button('Click Me', on_click=lambda: print('Button clicked!'))