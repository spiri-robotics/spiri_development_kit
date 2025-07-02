import os, asyncio, httpx
from nicegui import ui
from spiriSdk.utils.daemon_utils import daemons, display_daemon_status, start_container, stop_container, restart_container
from spiriSdk.utils.new_robot_utils import delete_robot, save_robot_config
from spiriSdk.pages.tools import gz_world
from spiriSdk.utils.gazebo_utils import get_running_worlds, is_robot_alive
from spiriSdk.pages.new_robots import new_robots
from spiriSdk.ui.ToggleButton import ToggleButton
from spiriSdk.utils.InputChecker import InputChecker

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
            await save_robot_config(selected_robot, selected_options)

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

            # Functions
            def update_status(name, label: ui.label):
                status = display_daemon_status(name)
                label.text = f'{status.capitalize()}'
                if status == 'running':
                    label.classes('text-[#609926]')
                elif status == 'stopped':
                    label.classes('text-[#d43131]')

            def start_polling(name, label, gz_toggle: ToggleButton):
                async def polling_loop():
                    while True:
                        update_status(name, label)
                        if not is_robot_alive(name):
                            if gz_toggle:
                                gz_toggle._state = True
                                gz_toggle.update()
                        if await get_running_worlds() == []:
                            gz_world.models = {}
                        await asyncio.sleep(5)
                asyncio.create_task(polling_loop())
                
            async def power_on(robot, buttons: list):
                for button in buttons:
                    button.disable()
                n = ui.notification(timeout=None)
                for i in range(1):
                    n.message = 'Powering on...'
                    n.spinner = True
                    await asyncio.sleep(1)
                    
                await start_container(robot)
                
                n.message = 'Container started'
                n.type = 'positive'
                n.spinner = False
                n.timeout = 4
                
                displayCards.refresh()

            async def power_off(robot, buttons: list):
                for button in buttons:
                    button.disable()
                n = ui.notification(timeout=None)
                for i in range(1):
                    n.message = 'Powering off...'
                    n.spinner = True
                    await asyncio.sleep(1)
                    
                message, type = stop_container(robot)
                
                n.message = message
                n.type = type
                n.spinner = False
                n.timeout = 4
                
                displayCards.refresh()

            async def reboot(robot, buttons: list):
                for button in buttons:
                    button.disable()
                n = ui.notification(message='Rebooting...', spinner=True, timeout=None)

                await restart_container(robot)
                
                n.message = 'Done'
                n.spinner = False
                n.type = 'positive'
                n.timeout = 4
                
                displayCards.refresh()

            async def add_to_world(robot):
                robotType = str(robot).rsplit('_', 1)[0]
                await gz_world.prep_bot(robot, robotType)
                ui.notify(f'Added {robot} to world')

            async def remove_from_world(robot):
                robot = gz_world.models[robot].kill_model()

            async def delete(n):
                notif = ui.notification(timeout=False)
                for i in range(1):
                    notif.message = 'Deleting...'
                    notif.spinner=True
                    await asyncio.sleep(0.1)

                if await delete_robot(n):
                    notif.message = f'{n} deleted'
                    notif.type = 'positive'
                else:
                    notif.message = 'error deleting robot'
                    notif.type = 'negative'
                
                notif.spinner = False
                notif.timeout = 4

            # Card and details
            with ui.card().classes('p-[calc(var(--nicegui-default-padding)*1.2)] w-[calc(50%-(var(--nicegui-default-gap)/2))] h-auto'):

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

                # Docker host
                with ui.card_section().classes('w-full p-0 mb-2'):
                    with ui.row():
                        command = f"DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_{robotName}.socket"
                        ui.code(command, language='bash').classes('text-sm text-gray-600 dark:text-gray-200')

                # IP and web interface link
                with ui.card_section().classes('w-full p-0 mb-2'):
                    if 'Running' in label_status.text:
                        ui.markdown(f'**Robot IP:** {daemons[robotName].get_ip()}')
                        
                        # Link to the robot's web interface if applicable
                        if "spiri_mu" in robotName:
                            url = f'http://{daemons[robotName].get_ip()}:{80}'
                            ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('text-sm dark:text-gray-200 py-3')
                                    
                        if 'ARC' in robotName:
                            url = f'http://{daemons[robotName].get_ip()}:{80}'
                            ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('text-sm dark:text-gray-200 py-3')
                    else:
                        ui.label('Robot IP not available')

                # Actions
                with ui.card_section().classes('w-full p-0 mt-auto'):
                    with ui.row(align_items='end'):
                        with ui.row():
                            power = ToggleButton(on_label='power off', off_label='power on')
                            if 'Running' in label_status.text:
                                power.state = True
                            else:
                                power.state = False
                            power.update()
                            
                            reboot_btn = ui.button('Reboot', color='secondary')
                        gz_toggle = ToggleButton(state=False, on_label="remove from gz sim", off_label="add to gz sim", on_switch=lambda r=robotName: remove_from_world(r), off_switch=lambda r=robotName: add_to_world(r))
                        
                        ui.space()
                        
                        trash = ui.button(icon='delete', on_click=lambda n=robotName: delete(n), color='negative')
                        
                        buttons = [power, reboot_btn, gz_toggle, trash]
                        
                        power.on_switch = lambda r=robotName, b=buttons: power_off(r, b)
                        power.off_switch = lambda r=robotName, b=buttons: power_on(r, b)
                        reboot_btn.on_click(lambda r=robotName, b=buttons: reboot(r, b))

                start_polling(robotName, label_status, gz_toggle)