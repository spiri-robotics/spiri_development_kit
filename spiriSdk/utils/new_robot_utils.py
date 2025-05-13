import os
from nicegui import ui
import yaml
import re
from pathlib import Path
import uuid
from spiriSdk.dindocker import DockerInDocker
from nicegui import run
from spiriSdk.utils.daemon_utils import daemons, init_daemons
import shutil

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

async def save_robot_config(robot_type, selected_options):
    robot_id = uuid.uuid4().hex[:6]
    folder_name = f"{robot_type}-{robot_id}"
    folder_path = os.path.join(ROOT_DIR, "data", folder_name)
    os.makedirs(folder_path, exist_ok=True)

    config_path = os.path.join(folder_path, "config.env")
    with open(config_path, "w") as f:
        for key, value in selected_options.items():
            f.write(f"{key}={value}\n")

    new_daemon = DockerInDocker(image_name="docker:dind", container_name=folder_name)
    await run.io_bound(new_daemon.ensure_started)

    ui.notify(f"Saved config.env and started daemon for {folder_name}")

async def delete_robot(robot_name) -> bool:
    robot_path = os.path.join(ROOT_DIR, "data", robot_name)
    daemons = await init_daemons()
    daemon = daemons.pop(robot_name)
    daemon.cleanup()
    shutil.rmtree(robot_path)
    return True

def display_robot_options(robot_name, selected_additions, selected_options, options_container):
        print(daemons)
        ui.notify(f'Selected Robot: {robot_name}, Selected Addition: {addition}' for addition in selected_additions)
        options_path = os.path.join(ROBOTS_DIR, robot_name, 'options.yaml')
        if not os.path.exists(options_path):
            ui.notify(f"No options.yaml found for {robot_name}")
            options_container.clear()
            with options_container:
                ui.label(f'No options.yaml found for {robot_name}')
            return

        with open(options_path, 'r') as yaml_file:
            options = yaml.safe_load(yaml_file)

        selected_options.clear()
        for key, option in options.get('x-spiri-options', {}).items():
            selected_options[key] = option.get('value')

        # Clear previous options UI
        options_container.clear()

        # Display options dynamically
        with options_container:
            ui.label(f"Options for {robot_name}").classes('text-h5')

            for key, option in options.get('x-spiri-options', {}).items():
                ui.label(key).classes('text-h6')
                ui.label(option.get('help-text', '')).classes('text-body2')
                option_type = option.get('type', 'text')
                current_value = option.get('value', '')

                if option_type == 'bool':
                    with ui.row():
                        switch_label = ui.label(f"{current_value}").classes('text-body2')

                        def on_toggle(e, k=key):
                            selected_options[k] = e.value
                            switch_label.set_text(f"{e.value}")

                        ui.switch(
                            value=current_value,
                            on_change=on_toggle
                        )

                elif option_type == 'int':
                    min_val = option.get('min')
                    max_val = option.get('max')
                    step = option.get('step', 1) or 1
                    current_value = option.get('value', 0)

                    def make_int_input(k):
                        return lambda e: selected_options.update({k: int(e.value) if e.value.isdigit() else 0})
                    
                    def int_input_change(k):
                        return lambda e: selected_options.update({k: int(e.value)})

                    if min_val is not None and max_val is not None:
                        # Generate dropdown choices from min to max using step
                        int_options = list(range(min_val, max_val + 1, step))
                        with ui.select(
                            options=int_options,
                            value=current_value,
                            on_change=int_input_change(key)
                        ) as dropdown:
                            dropdown.label = key
                    else:
                        # Fallback: no min/max, use input box
                        ui.input(
                            label=f"{key} (int)",
                            value=str(current_value),
                            on_change=make_int_input(key)
                        )

                elif option_type == 'float':
                    def make_float_input(k):
                        return lambda e: selected_options.update({k: float(e.value) if e.value else 0.0})
                    ui.input(
                        label=f"{key} (float)",
                        value=str(current_value),
                        on_change=make_float_input(key)
                    )

                elif option_type == 'text':
                    ui.input(key, value=option.get('value', ''), on_change=(lambda e, k=key: selected_options.update({k: e.value})))
                
                elif option_type == 'dropdown':
                    # Ensure the dropdown options are a list
                    dropdown_options = option.get('options', [])
                    if isinstance(dropdown_options, list):
                        with ui.dropdown_button(f"{key}: {option.get('value', '')}", auto_close=True):
                            for item in dropdown_options:
                                ui.item(item, on_change=(lambda e, k=key: selected_options.update({k: e.value})))
                    else:
                        ui.label(f"Invalid dropdown options for {key}").classes('text-body2')
                
                else:
                    ui.input(key, value=option.get('value', ''), on_change=(lambda e, k=key: selected_options.update({k: e.value})))