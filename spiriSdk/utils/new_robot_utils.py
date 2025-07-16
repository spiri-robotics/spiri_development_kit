import yaml, re, uuid
from nicegui import ui
from pathlib import Path
from loguru import logger

from spiriSdk.utils.SDKRobot import SDKRobot
from spiriSdk.utils.daemon_utils import robots, active_sys_ids
from spiriSdk.utils.InputChecker import InputChecker

ROOT_DIR = Path(__file__).parents[2].absolute()
ROBOTS_DIR = ROOT_DIR / 'robots'

# Get the list of robots dynamically from the robots folder
robots = [folder.name for folder in ROBOTS_DIR.iterdir() if folder.exists()]

def ensure_options_yaml():
    robots = []
    for folder in ROBOTS_DIR.iterdir():
        if folder.exists():
            robots.append(folder.name)  # Add to the robots list
            options_path = folder / 'options.yaml'
            if not options_path.exists():
                # Create a default options.yaml file
                services_path = folder / "services"
                if not services_path.exists():
                    ui.notify(f"Services folder not found under {folder}", type="error")
                    continue
                service_folders = [p for p in services_path.iterdir() if p.is_dir()]
                if not service_folders:
                    ui.notify(f"No service folders found under {services_path}", type="error")
                    continue

                compose_file = service_folders[0] / "docker-compose.yaml"
                if not compose_file.exists():
                    compose_file = service_folders[0] / "docker-compose.yml"
                    if not compose_file.exists():
                        ui.notify(f"{compose_file} not found!", type="error")
                        continue
        
                compose_text = compose_file.read_text()
                variables = set(re.findall(r'\$[{]?([A-Z_][A-Z0-9_]*)[}]?', compose_text))

                default_options = {'x-spiri-options': {}}
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
    robot_id = selected_options.get('MAVLINK_SYS_ID', uuid.uuid4().hex[:6])
    if robot_type == 'spiri_mu' and selected_options.get('GIMBAL') == False:
        robot_type = 'spiri_mu_no_gimbal'
    robot_name = f"{robot_type}_{robot_id}"
    new_robot= SDKRobot(robot_name, folder=ROBOTS_DIR / robot_type / 'services', selected_options=selected_options)
    robots[robot_name] = new_robot
    active_sys_ids.append(robot_id)
    dialog.close()  # Close the dialog after saving
    from spiriSdk.utils.card_utils import displayCards
    displayCards.refresh()
    ui.notify(f"Robot {robot_name} added successfully!", type='positive')

async def delete_robot(robot_name: str) -> bool:
    logger.info(f"Deleting robot {robot_name}")
    robot = robots.pop(robot_name)
    from spiriSdk.utils.card_utils import displayCards
    displayCards.refresh()
    robot.delete()
    active_sys_ids.remove(int(robot_name.rsplit('_', 1)[1]))
    logger.success(f"Robot {robot_name} deleted successfully")
    return True

def display_robot_options(robot_type: str, selected_options, options_container: ui.column, checker: InputChecker):
    options_path = ROBOTS_DIR / robot_type / 'options.yaml'
    if not options_path.exists():
        options_container.clear()
        with options_container:
            ui.label(f'No options.yaml found for {robot_type}')
        return

    with open(options_path, 'r') as yaml_file:
        options = yaml.safe_load(yaml_file)
    
    format_rules = {
        'Mavlink': 'MAVLink',
        'Sys': 'System',
        'Id': 'ID',
        'Desc': 'Description'
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

                def on_toggle(e, k):
                    selected_options[k] = e.value
                
                with ui.row().classes('items-center justify-between w-[35%]'):
                    ui.label(formatted_key)
                    ui.switch(value=current_value, on_change=lambda e, k=key: on_toggle(e.sender, k))
                    selected_options[key] = current_value

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
                        'Value must be an integer between 1 and 254': lambda value, minVal=min_val, maxVal = max_val: str(value).isdigit() and float(value) >= minVal and float(value) <= maxVal,
                        'System ID already in use': lambda value: int(value) not in active_sys_ids
                    }
                ).classes('w-full pb-1')
                
                checker.add(numInput, False)
            
            else:
                def handleText(e: ui.input, k):
                    selected_options.update({k: e.value})
                    
                textInput = ui.input(
                    label=f'{formatted_key}', 
                    placeholder=current_value, 
                    on_change=lambda e, k=key: handleText(e.sender, k)
                ).classes('w-full pb-1')
                
                if 'DESC' in key:
                    textInput.label = f'{formatted_key} (optional)'