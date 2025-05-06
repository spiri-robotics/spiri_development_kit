from nicegui import ui

async def header():
    with ui.header().style('background-color: #9EDFEC'):
        ui.button('Home', on_click=lambda: ui.navigate.to('/'), color='#20788a')
        ui.button('Tools', on_click=lambda: ui.navigate.to('/tools'), color='#20788a')
        ui.button('Manage Robots', on_click=lambda: ui.navigate.to('/manage_robots'), color='#20788a')