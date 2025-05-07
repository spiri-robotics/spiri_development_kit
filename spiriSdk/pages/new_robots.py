from nicegui import ui
import os
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
import yaml

robots = [1, 2, 3]

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ROBOTS_DIR = os.path.join(ROOT_DIR, 'robots')

# Get the list of robots dynamically from the robots folder
robots = [folder for folder in os.listdir(ROBOTS_DIR) if os.path.isdir(os.path.join(ROBOTS_DIR, folder))]

def ensure_options_yaml():
    robots = []
    for folder in os.listdir(ROBOTS_DIR):
        folder_path = os.path.join(ROBOTS_DIR, folder)
        if os.path.isdir(folder_path):
            robots.append(folder)  # Add to the robots list
            options_path = os.path.join(folder_path, 'options.yaml')
            if not os.path.exists(options_path):
                # Create a default options.yaml file
                default_options = {
                    'name': folder,
                    'type': 'default',
                    'enabled': True,
                }
                with open(options_path, 'w') as yaml_file:
                    yaml.dump(default_options, yaml_file)
    return robots

robots = ensure_options_yaml()

@ui.page('/new_robots')
async def new_robots():
    await styles()

    selected_robot = None
    selected_additions = ["gimbal"]

    options_container = ui.column()
    
    with ui.card():
        def display_robot_options(robot_name):
            ui.label("Options for selected Robot")
            ui.notify(f'Selected Robot: {robot_name}, Selected Addition: {addition}' for addition in selected_additions)
            options_path = os.path.join(ROBOTS_DIR, robot_name, 'options.yaml')
            if not os.path.exists(options_path):
                ui.notify(f"No options.yaml found for {robot_name}")
                return

            with open(options_path, 'r') as yaml_file:
                options = yaml.safe_load(yaml_file)

            # Clear previous options UI
            options_container.clear()

            # Display options dynamically
            with options_container:
                ui.label(f"Options for {robot_name}").classes('text-h5')
                for key, option in options.get('x-spiri-options', {}).items():
                    ui.label(option.get('help-text', '')).classes('text-body2')
                    option_type = option.get('type', 'text')
                    if option_type == 'bool':
                        with ui.row():
                            switch = ui.switch(value=option.get('value', False), on_change=lambda e, k=key: print(f"{k} switched: {e.value}"))
                            switch.label = key
                            ui.label(str(switch.value)).classes('text-body2')
                    elif option_type == 'int':
                        ui.label(key)
                        ui.slider(
                            min=option.get('min', 0),
                            max=option.get('max', 255),                   
                            step=option.get('step', 1),
                            value=option.get('value', 0),
                            on_change=lambda e, k=key: print(f"{k} changed: {e.value}")
                        ).props(f'label="{key}"')
                    elif option_type == 'text':
                        ui.input(key, value=option.get('value', ''), on_change=lambda e, k=key: ui.label(f"{k} changed: {e.value}"))
                    elif option_type == 'dropdown':
                        # Ensure the dropdown options are a list
                        dropdown_options = option.get('options', [])
                        if isinstance(dropdown_options, list):
                            with ui.dropdown_button(f"{key}: {option.get('value', '')}", auto_close=True):
                                for item in dropdown_options:
                                    ui.item(item, on_click=lambda _, i=item, k=key: print(f"{k} selected: {i}"))
                        else:
                            ui.label(f"Invalid dropdown options for {key}").classes('text-body2')
                    else:
                        ui.input(key, value=option.get('value', ''), on_change=lambda e, k=key: print(f"{k} changed: {e.value}"))
        
        with ui.card():
            ui.label('New Robot').classes('text-h5')
            ui.label("Select new robot type")
            with ui.dropdown_button('Select Robot', auto_close=True):
                for robot in robots:
                    ui.item(robot, on_click=lambda r=robot: display_robot_options(r))
