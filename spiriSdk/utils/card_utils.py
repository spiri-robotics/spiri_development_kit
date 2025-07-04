import os, asyncio, httpx
from nicegui import ui
from loguru import logger
from spiriSdk.utils.daemon_utils import daemons, display_daemon_status, start_container, stop_container, restart_container
from spiriSdk.utils.new_robot_utils import delete_robot, save_robot_config
from spiriSdk.pages.tools import gz_world
from spiriSdk.utils.gazebo_utils import get_running_worlds, is_robot_alive
from spiriSdk.pages.new_robots import new_robots
from spiriSdk.ui.ToggleButton import ToggleButton
from spiriSdk.utils.InputChecker import InputChecker
from datetime import datetime

async def is_service_ready(url: str, timeout: float = 0.5) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)            
            return response.status_code == 200
    except Exception:
        return False
    
def copy_text(command):
    ui.run_javascript(f'''
        navigator.clipboard.writeText("{command}");
    ''')
    ui.notify("Copied to clipboard!")
    
async def addRobot():
    with ui.dialog() as d, ui.card(align_items='stretch').classes('w-full'):
        checker = InputChecker()
        await new_robots(checker)

        async def submit(button):
            button = button.props(add='loading')

            # Import here instead of at the top to get the updated selected_robot
            from spiriSdk.pages.new_robots import selected_robot, selected_options
            await save_robot_config(selected_robot, selected_options, d)

            d.close()

            # Refresh display to update visible cards
            displayCards.refresh()

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', color='secondary', on_click=d.close).classes('text-base')
            # Add button is disabled until all input fields have valid values
            ui.button(
                'Add', 
                color='secondary', 
                on_click=lambda e: submit(e.sender)
            ).classes('text-base').bind_enabled_from(checker, 'isValid')
    
    d.open()
    
def update_status(name, label: ui.label, running_chip: ui.chip = None, restarting_chip: ui.chip = None, exited_chip: ui.chip = None):
    status = display_daemon_status(name)
    if isinstance(status, dict):
        running_chip.visible = True
        restarting_chip.visible = True 
        exited_chip.visible = True
        running_chip.text = f'Running: {status.get("running", 0)}'
        restarting_chip.text = f'Restarting: {status.get("restarting", 0)}'
        exited_chip.text = f'Exited: {status.get("exited", 0)}'
        label.visible = False
    else:
        running_chip.visible = False
        restarting_chip.visible = False
        exited_chip.visible = False
        label.visible = True
        label.text = f'{status.capitalize()}'
    if status == 'running':
        label.classes('text-[#609926]')
    elif status == 'stopped':
        label.classes('text-[#d43131]')
    return status

polling_tasks = {}

def start_polling(name, label, gz_toggle: ToggleButton):
    if name in polling_tasks and not polling_tasks[name].done():
        old = polling_tasks.get(name)
        old.cancel()

    async def polling_loop():
        while True:
            status = update_status(name, label)
            world_running = await get_running_worlds()
            if gz_toggle:
                if len(world_running) > 0:
                    gz_toggle.visible = True
                else:
                    if is_robot_alive(name):
                        await remove_from_world(name)
                    gz_toggle.visible = False
                if not is_robot_alive(name):
                    gz_toggle.state = False
                    gz_toggle.update()
                else:
                    gz_toggle.state = True
                    gz_toggle.update()
            if len(world_running) == 0:
                gz_world.models = {}
            await asyncio.sleep(3)
    polling_tasks[name] = asyncio.create_task(polling_loop())
    
async def power_on(robot, buttons: list):
    for button in buttons:
        button.disable()
    logger.info(f'Powering on {robot}...')
    n = ui.notification(timeout=None)
    for i in range(1):
        n.message = f'Powering on {robot}...'
        n.spinner = True
        await asyncio.sleep(1)
        
    await start_container(robot)
    
    n.message = f'Container {robot} started'
    n.type = 'positive'
    n.spinner = False
    n.timeout = 4
    
    displayCards.refresh()

async def power_off(robot, buttons: list):
    logger.info(f'Powering off {robot}...')
    for button in buttons:
        button.disable()
    n = ui.notification(timeout=None)
    for i in range(1):
        n.message = f'Powering off {robot}...'
        n.spinner = True
        await asyncio.sleep(1)
        
    message, type = stop_container(robot)
    logger.info(message)
    
    n.message = message
    n.type = type
    n.spinner = False
    n.timeout = 4
    
    displayCards.refresh()

async def reboot(robot, buttons: list):
    logger.info(f'Rebooting {robot}...')
    for button in buttons:
        button.disable()
    n = ui.notification(message=f'Rebooting {robot}...', spinner=True, timeout=None)

    await restart_container(robot)
    
    n.message = f'{robot} rebooted'
    n.spinner = False
    n.type = 'positive'
    n.timeout = 4
    
    displayCards.refresh()
    
async def add_to_world(robot):
    try:
        robotType = "_".join(str(robot).split('_')[0:-1])
        print(robotType)
        await gz_world.prep_bot(robot, robotType)
        running_worlds = await get_running_worlds()
        if len(running_worlds) > 0:
            ui.notify(f'Added {robot} to world')
            return True
        else:
            raise Exception('No world running')
    except Exception as e:
        print(e)
        return False

async def remove_from_world(robot):
    try:
        robot = gz_world.models[robot].kill_model()
        return True
    except Exception as e:
        print(e)
        return False
    
async def delete(robot):
    n = ui.notification(timeout=False)
    for i in range(1):
        n.message = f'Deleting {robot}...'
        n.spinner=True
        await asyncio.sleep(0.1)

    if await delete_robot(robot):
        n.message = f'{robot} deleted'
        n.type = 'positive'
    else:
        n.message = f'error deleting {robot}'
        n.type = 'negative'
    
    n.spinner = False
    n.timeout = 4
                        
@ui.refreshable
def displayCards():
    names = daemons.keys()

    with ui.row(align_items='stretch').classes('w-full'):
        for robotName in names:

            ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            DATA_DIR = os.path.join(ROOT_DIR, 'data')
            config_file = os.path.join(DATA_DIR, robotName, 'config.env')
            alias = robotName
            with open(config_file) as f:
                for line in f:
                    if 'ALIAS' in line:
                        alias = line.split('=', 1)
                        alias = alias[1].strip()
                        break

            # Card and details
            half = 'calc(50%-(var(--nicegui-default-gap)/2))'
            third = 'calc((100%/3)-(var(--nicegui-default-gap)/1.5))' # formula: (100% / {# of cards}) - ({default gap} / ({# of cards} / {# of gaps}))
            card_padding = 'calc(var(--nicegui-default-padding)*1.2)'
            with ui.card().classes(f'p-[{card_padding}] w-full min-[1466px]:w-[{half}] min-[2040px]:w-[{third}] h-auto'):

                # Name(s) and status
                with ui.row(align_items='start').classes('w-full mb-2'):
                    with ui.card_section().classes('p-0'):
                        if alias == robotName or alias == robotName:
                            ui.label(f'{robotName}').classes('text-xl font-semibold text-gray-900 dark:text-gray-100 pb-6')
                        else:
                            ui.label(f'{alias[1:-1]}').classes('text-xl font-semibold text-gray-900 dark:text-gray-100')
                            ui.label(f'{robotName}').classes('text-base font-normal text-gray-900 dark:text-gray-100')

                    ui.space()

                    with ui.card_section().classes('p-0'):
                        label_status = ui.label('Status Loading...').classes('text-base font-semibold')
                        
                    update_status(robotName, label_status)

                # Stats/info
                if daemons[robotName].container is not None and daemons[robotName].container.status == 'running': 
                    # Docker host
                    with ui.card_section().classes('w-full p-0 mb-2'):
                        with ui.row():
                            command = f"DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_{robotName}.socket"
                            ui.code(command, language='bash').classes('text-gray-600 dark:text-gray-200')

                    # IP and web interface link
                    with ui.card_section().classes('w-full p-0 mb-2'):
                        if 'Running' in label_status.text:
                            ui.markdown(f'**Robot IP:** {daemons[robotName].get_ip()}')
                        
                            # Link to the robot's web interface if applicable 
                            # if "spiri_mu" in robotName:
                            #     url = f'http://{daemons[robotName].get_ip()}:{80}'
                            #     ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('py-3')
                                        
                            if 'ARC' in robotName:
                                url = f'http://{daemons[robotName].get_ip()}:{8080}'
                                ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('py-3')
                # else:
                #     with ui.card_section().classes('w-full p-0 mb-2'):
                #         ui.label('Robot stats not available')

                # Actions
                with ui.card_section().classes('w-full p-0 mt-auto'):
                    with ui.row(align_items='end'):
                        on = False
                        if daemons[robotName].container is not None and daemons[robotName].container.status == 'running':
                            on = True
                        power = ToggleButton(on_label='power off', off_label='power on', state=on)
                        
                        reboot_btn = ui.button('Reboot', color='secondary')
                        
                        gz_toggle = ToggleButton(state=False, on_label="remove from gz sim", off_label="add to gz sim", on_switch=lambda r=robotName: remove_from_world(r), off_switch=lambda r=robotName: add_to_world(r))
                        gz_toggle.visible = False
                        
                        ui.space()
                        
                        trash = ui.button(icon='delete', on_click=lambda n=robotName: delete(n), color='negative')
                        
                        buttons = [power, reboot_btn, gz_toggle, trash]
                        
                        power.on_switch = lambda r=robotName, b=buttons: power_off(r, b)
                        power.off_switch = lambda r=robotName, b=buttons: power_on(r, b)
                        reboot_btn.on_click(lambda r=robotName, b=buttons: reboot(r, b))

                start_polling(robotName, label_status, gz_toggle)