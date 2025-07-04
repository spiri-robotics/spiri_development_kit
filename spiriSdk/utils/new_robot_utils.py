import os, yaml, re, uuid, shutil
from nicegui import ui, run
from pathlib import Path
from spiriSdk.docker.dindocker import DockerInDocker
from spiriSdk.utils.daemon_utils import daemons, start_services, active_sys_ids
from spiriSdk.utils.InputChecker import InputChecker
from loguru import logger
import dotenv

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
                    compose_file = service_folders[0] / "docker-compose.yml"
                    if not compose_file.exists():
                        ui.notify(f"{compose_file} not found!", type="error")
                        continue
        
                compose_text = compose_file.read_text()
                variables = set(re.findall(r'\$[{]?([A-Z_][A-Z0-9_]*)[}]?', compose_text))

                default_options = {
                    'x-spiri-options': {}}
                for var in variables:
                    logger.debug(f"Detected variable: {var}")
                    if var not in default_options["x-spiri-options"]:
                        default_options["x-spiri-options"][var] = {
                            "type": "text",  # Default type (can be adjusted if needed)
                            "value": 0,  # Default to spiri.env value if available
                            "help-text": f"Auto-detected variable {var}"
                        }

                with open(options_path, 'w') as yaml_file:
                    yaml.dump(default_options, yaml_file)

    return robots

async def save_robot_config(robot_type, selected_options, dialog):
    if robot_type == "ARC":
        robot_id = selected_options.get('ARC_SYS_ID', uuid.uuid4().hex[:6])
    else:   
        robot_id = selected_options.get('MAVLINK_SYS_ID', uuid.uuid4().hex[:6])
    folder_name = f"{robot_type}_{robot_id}"
    folder_path = os.path.join(ROOT_DIR, "data", folder_name)

    os.makedirs(folder_path, exist_ok=True)
    
    new_daemon = DockerInDocker(image_name="docker:dind", container_name=folder_name)

    config_path = new_daemon.robot_env
    for key, value in selected_options.items():
        if 'NAME' in key:
            dotenv.set_key(config_path, key, folder_name)
            if value:
                dotenv.set_key(config_path, 'ALIAS', value)
        else:
            dotenv.set_key(config_path, key, str(value))
    
    await run.io_bound(new_daemon.ensure_started)
    daemons[folder_name] = new_daemon
    active_sys_ids.append(robot_id)
    
    dialog.close()  # Close the dialog after saving

    from spiriSdk.utils.card_utils import displayCards
    displayCards.refresh()
    await start_services(folder_name)

    # ui.notify(f"Saved config.env and started daemon for {folder_name}")
    ui.notify(f"Robot {folder_name} added successfully!", type='positive')

async def delete_robot(robot_name) -> bool:
    logger.info(f"Deleting robot {robot_name}")
    robot_path = os.path.join(ROOT_DIR, "data", robot_name)
    daemon = daemons.pop(robot_name)
    from spiriSdk.utils.card_utils import displayCards
    displayCards.refresh()
    daemon.cleanup()
    robot_sys = str(robot_name).rsplit('_', 1)
    active_sys_ids.remove(int(robot_sys[1]))
    if os.path.exists(robot_path):
        shutil.rmtree(robot_path)
    logger.success(f"Robot {robot_name} deleted successfully")
    return True

def display_robot_options(robot_name, selected_options, options_container, checker: InputChecker):
    options_path = os.path.join(ROBOTS_DIR, robot_name, 'options.yaml')
    if not os.path.exists(options_path):
        options_container.clear()
        with options_container:
            ui.label(f'No options.yaml found for {robot_name}')
        return

    with open(options_path, 'r') as yaml_file:
        options = yaml.safe_load(yaml_file)

    format_rules = {
        'Arc': 'ARC',
        'Mavlink': 'MAVLink',
        'Sys': 'System',
        'Id': 'ID',
        'Mavros': 'MAVROS',
        'Gcs': 'GCS',
        'Serial0': 'Serial',
        'Sitl': 'SITL'
    }

    # Clear previous options and UI
    selected_options.clear()
    options_container.clear()

    # Display options dynamically
    with options_container:
        for key, option in options.get('x-spiri-options', {}).items():
            selected_options[key] = None
            option_type = option.get('type', 'text')
            current_value = option.get('value', '')
            if current_value == 'None':
                current_value = None

            formatted_key = str(key).replace("_", " ").title()
            for og, new in format_rules.items():
                formatted_key = formatted_key.replace(og, new)

            if option_type == 'bool':
                if current_value == 1:
                    bool_value = True
                else:
                    bool_value = False

                def on_toggle(e, k):
                    if e.value == True:
                        selected_options[k] = 1
                    else:
                        selected_options[k] = 0
                
                with ui.row().classes('items-center justify-between w-[35%]'):
                    ui.label(formatted_key)
                    ui.switch(value=bool_value, on_change=lambda e, k=key: on_toggle(e.sender, k))

            elif option_type == 'int':
                min_val = option.get('min', None)
                max_val = option.get('max', None)
                step = option.get('step', 1)
                current_value = option.get('value', 0)

                def handleNum(e, k):
                    checker.checkNumber(e)

                    if str(e.value).isdigit():
                        selected_options[k] = int(e.value)

                numInput = ui.input(
                    label=f'{formatted_key}*',
                    value=None,
                    on_change=lambda e, k=key: handleNum(e.sender, k),
                    validation={
                        'Field cannot be empty': lambda value: value,
                        'Value must be an integer': lambda value: str(value).isdigit(),
                        'Value must be between 1 and 254': lambda value, minVal=min_val, maxVal = max_val: float(value) >= minVal and float(value) <= maxVal,
                        'System ID already in use': lambda value: int(value) not in active_sys_ids
                    }
                ).classes('w-full pb-1')
                
                checker.add(numInput, False)
            
            else:
                def handleText(e: ui.input, k):
                    selected_options.update({k: e.value})

                if 'NAME' in key:
                    textVal = ''
                else:
                    textVal = current_value
                    
                ui.input(
                    label=f'{formatted_key}', 
                    value=textVal, 
                    placeholder=current_value, 
                    on_change=lambda e, k=key: handleText(e.sender, k)
                ).classes('w-full pb-1')