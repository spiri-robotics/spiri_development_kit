from nicegui import ui
from pages.header import header

robots = [1, 2, 3]

@ui.page('/new_robots')
async def new_robots():
    await header()
    
    with ui.card():
        ui.label('New Robots').classes('text-h5')
        ui.label("Select new robot type")
        ui.dropdown_button(
            'Select Robot',
            options=[f'Robot {robot}' for robot in robots],
            on_change=lambda e: print(f'Selected: {e.value}'),
        )
        ui.label("Select robot additions:")
        ui.dropdown_button(
            'Select Additions',
            options=['Addition 1', 'Addition 2', 'Addition 3'],
            on_change=lambda e: print(f'Selected: {e.value}'),
        )
        def display_robot_options():
            selected_robot = ui.get('robot_dropdown').value
            selected_addition = ui.get('addition_dropdown').value
            ui.notify(f'Selected Robot: {selected_robot}, Selected Addition: {selected_addition}')
            for option in selected_robot.options:
                if option.type == bool:
                    ui.toggle(option.name, on_change=lambda e: print(f'{option.name} toggled: {e.value}'))
        display_robot_options()
