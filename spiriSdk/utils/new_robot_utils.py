import os, yaml, re, uuid, shutil
from nicegui import ui
from pathlib import Path
from spiriSdk.docker.dindocker import DockerInDocker
from nicegui import run
from spiriSdk.utils.daemon_utils import daemons, start_services, DaemonEvent

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
    robot_id = selected_options.get('DRONE_SYS_ID', uuid.uuid4().hex[:6])
    folder_name = f"{robot_type}-{robot_id}"
    folder_path = os.path.join(ROOT_DIR, "data", folder_name)
    os.makedirs(folder_path, exist_ok=True)

    config_path = os.path.join(folder_path, "config.env")
    with open(config_path, "w") as f:
        for key, value in selected_options.items():
            f.write(f"{key}={value}\n")

    new_daemon = DockerInDocker(image_name="docker:dind", container_name=folder_name)
    await run.io_bound(new_daemon.ensure_started)
    daemons[folder_name] = new_daemon

    await start_services(folder_name)
    await DaemonEvent.notify()

    ui.notify(f"Saved config.env and started daemon for {folder_name}")

async def delete_robot(robot_name) -> bool:
    robot_path = os.path.join(ROOT_DIR, "data", robot_name)
    daemon = daemons.pop(robot_name)
    daemon.cleanup()
    if os.path.exists(robot_path):
        shutil.rmtree(robot_path)
    await DaemonEvent.notify()
    return True

def display_robot_options(robot_name, selected_additions, selected_options, options_container):
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

    format_rules = {
        'Sys': 'System',
        'Id': 'ID',
        'Gcs': 'GCS',
        'Serial0': 'Serial 0',
        'Sitl': 'SITL'
    }

    # Clear previous options UI
    options_container.clear()

    # Display options dynamically
    with options_container:
        for key, option in options.get('x-spiri-options', {}).items():
            help_text = option.get('help-text', False)
            option_type = option.get('type', 'text')
            current_value = option.get('value', '')

            formatted_key = str(key).replace("_", " ").title()
            for og, new in format_rules.items():
                formatted_key = formatted_key.replace(og, new)

            if option_type == 'bool':
                with ui.row().classes('items-center w-[35%]'):
                    def on_toggle(e, k):
                        selected_options[k] = e.value
                    
                    ui.label(formatted_key)
                    ui.switch(value=current_value, on_change=lambda e, k=key: on_toggle(e, k)).classes('ml-auto')

            elif option_type == 'int' or option_type == 'float':
                min_val = option.get('min', None)
                max_val = option.get('max', None)
                step = option.get('step', 1)
                current_value = option.get('value', 0)

                def update(e, k):
                    if int(e.value) == e.value:
                        selected_options[k] = int(e.value)
                    else:
                        selected_options[k] = e.value

                # def make_int_input(k):
                #     return lambda e: selected_options.update({k: int(e.value) if e.value.isdigit() else 0})
                
                # def int_input_change(k):
                #     return lambda e: selected_options.update({k: int(e.value)})

                # if min_val is not None and max_val is not None:
                    # Generate dropdown choices from min to max using step
                # int_options = list(range(min_val, max_val + 1, step))
                ui.number(
                    formatted_key,
                    value=current_value,
                    min=min_val,
                    max=max_val,
                    step=step,
                    on_change=lambda e, k=key: update(e.sender, k)
                ).classes('w-full')
                # else:
                #     # Fallback: no min/max, use input box
                #     ui.input(
                #         label=f"{key} (int)",
                #         value=str(current_value),
                #         on_change=make_int_input(key)
                #     )

            # elif option_type == 'float':
            #     def make_float_input(k):
            #         return lambda e: selected_options.update({k: float(e.value) if e.value else 0.0})
            #     ui.input(
            #         label=f"{key} (float)",
            #         value=str(current_value),
            #         on_change=make_float_input(key)
            #     )

            # elif option_type == 'text':
            #     ui.input(key, value=option.get('value', ''), on_change=(lambda e, k=key: selected_options.update({k: e.value})))
            
            elif option_type == 'dropdown':
                # Ensure the dropdown options are a list
                dropdown_options = option.get('options', [])
                if isinstance(dropdown_options, list):
                    ui.select(dropdown_options, label=formatted_key, on_change=lambda e, k=key: selected_options.update({k: e.value})).classes('w-full')
                else:
                    ui.label(f"Invalid dropdown options for {key}").classes('text-body2')
            
            else:
                ui.input(formatted_key, value=current_value, on_change=(lambda e, k=key: selected_options.update({k: e.value}))).classes('w-full')