from nicegui import ui
import os
from spiriSdk.pages.styles import styles
from spiriSdk.pages.header import header
import yaml
import re
from pathlib import Path

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
                services_path = Path(folder_path) / "services"
                if not services_path.exists():
                    ui.notify(f"Services folder not found under {folder_path}", type="error")
                    continue               
                service_folders = [p for p in services_path.iterdir() if p.is_dir()]
                if not service_folders:
                    ui.notify(f"No service folder found under {services_path}", type="error")
                    continue

                compose_file = service_folders[0] / "docker-compose.yaml"
                if not compose_file.exists():
                    ui.notify(f"{compose_file} not found!", type="error")
                    continue
        
                compose_text = compose_file.read_text()
                variables = set(re.findall(r'\$[{]?([A-Z_][A-Z0-9_]*)[}]?', compose_text))

                default_options = {
                    'x-spiri-options': {}}
                for var in variables:
                    print(f"Detected variable: {var}")
                    if var not in default_options["x-spiri-options"]:
                        default_options["x-spiri-options"][var] = {
                            "type": "text",  # Default type (can be adjusted if needed)
                            "value": 0,  # Default to spiri.env value if available
                            "help-text": f"Auto-detected variable {var}"
                        }

                with open(options_path, 'w') as yaml_file:
                    yaml.dump(default_options, yaml_file)
    return robots

robots = ensure_options_yaml()

async def new_robots():
    await styles()

    selected_robot = {'name': None}
    selected_additions = ["gimbal"]

    def on_select(robot_name: str):
        selected_robot['name'] = robot_name
        display_robot_options(robot_name)
    
    def display_robot_options(robot_name):
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
                ui.label(key).classes('text-h6')
                ui.label(option.get('help-text', '')).classes('text-body2')
                option_type = option.get('type', 'text')
                if option_type == 'bool':
                    with ui.row():
                        switch_label = ui.label(str(option.get('value', False))).classes('text-body2')
                        switch = ui.switch(
                            value=option.get('value', False),
                            on_change=lambda e, k=key, lbl=switch_label: lbl.set_text(f"{e.value}")
                        )
                        switch.label = key
                elif option_type == 'int':
                    min_val = option.get('min')
                    max_val = option.get('max')
                    step = option.get('step', 1) or 1
                    current_value = option.get('value', 0)

                    if min_val is not None and max_val is not None:
                        # Generate dropdown choices from min to max using step
                        int_options = list(range(min_val, max_val + 1, step))
                        with ui.select(
                            options=int_options,
                            value=current_value,
                            on_change=lambda e, k=key: print(f"{k} changed: {e.value}")
                        ) as dropdown:
                            dropdown.label = key
                    else:
                        # Fallback: no min/max, use input box
                        ui.input(
                            label=f"{key} (integer)",
                            value=str(current_value),
                            on_change=lambda e, k=key: print(f"{k} changed: {e.value}")
                        )
                elif option_type == 'text':
                    ui.input(key, value=option.get('value', ''), on_change=lambda e, k=key: print(f"{k} changed: {e.value}"))
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
        with ui.dropdown_button("Choose Robot Here", color='secondary', auto_close=True) as dropdown:
            for robot in robots:
                ui.item(robot, on_click=lambda _, r=robot: on_select(r))

        options_container = ui.column()

        ui.button('Add Robot', color='secondary', on_click=lambda: ui.notify(f'Robot {selected_robot} added!')).classes('q-mt-md')
