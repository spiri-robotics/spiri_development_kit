import os, asyncio, httpx
from nicegui import ui
from spiriSdk.utils.daemon_utils import daemons, display_daemon_status
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

    with ui.row().classes('w-full'):
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

            async def update_status(name, label: ui.label):
                status = await display_daemon_status(name)
                label.text = f'{status}'
                if status == 'Running':
                    label.classes('text-[#4eb04c]')
                elif status == 'Stopped':
                    label.classes('text-[#d43131]')

            def start_polling(name, label, gz_toggle: ToggleButton):
                async def polling_loop():
                    while True:
                        await update_status(name, label)
                        if not is_robot_alive(name):
                            if gz_toggle:
                                gz_toggle._state = True
                                gz_toggle.update()
                        if await get_running_worlds() == []:
                            gz_world.models = {}
                        await asyncio.sleep(5)
                asyncio.create_task(polling_loop())

            async def add_to_world(robot):
                # ip = daemons[robotName].get_ip()
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
                    notif.message = 'Error deleting robot'
                    notif.type = 'negative'
                
                notif.spinner = False
                await asyncio.sleep(4)
                notif.dismiss()

            with ui.card().classes('p-[calc(var(--nicegui-default-padding)*1.2)]'):

                # Names and status
                with ui.row(align_items='start').classes('w-full mb-2'):
                    with ui.card_section().classes('p-0'):
                        if alias == robotName or alias == robotName:
                            ui.label(f'{robotName}').classes('text-xl font-semibold text-gray-900 dark:text-gray-100')
                        else:
                            ui.label(f'{alias}').classes('text-xl font-semibold text-gray-900 dark:text-gray-100')
                            ui.label(f'{robotName}').classes('text-base font-normal text-gray-900 dark:text-gray-100')

                    ui.space()

                    with ui.card_section().classes('p-0'):
                        label_status = ui.label('Status Loading...').classes('text-base font-semibold')

                # Docker host
                with ui.card_section().classes('w-full p-0 mb-2'):
                    with ui.row():
                        command = f"DOCKER_HOST=unix:///tmp/dind-sockets/spirisdk_{robotName}.socket"
                        ui.code(command, language='bash').classes('text-sm text-gray-600 dark:text-gray-200')

                # IP and web interface link
                with ui.card_section().classes('w-full p-0 mb-2'):
                    ui.label(f'IP: {daemons[robotName].get_ip()}').classes('text-base')

                    # Link to the robot's web interface if applicable
                    if "spiri_mu" in robotName:
                        url = f'http://{daemons[robotName].get_ip()}:{80}'
                        ui.link(f'Access the Web Interface', url, new_tab=True).classes('text-base')
                                
                    if "ARC" in robotName:
                        url = f'http://{daemons[robotName].get_ip()}:{80}'
                        ui.link(f'Access the Web Interface at: {url}', url, new_tab=True).classes('text-sm dark:text-gray-200 py-3')

                # Actions
                with ui.card_section().classes('w-full p-0 mt-auto'):
                    with ui.row(align_items='end'):
                        gz_toggle = ToggleButton(on_label="add to gz sim", off_label="remove from gz sim", on_switch=lambda r=robotName: add_to_world(r), off_switch=lambda r=robotName: remove_from_world(r)).classes('text-base')
                        ui.space()
                        ui.button(icon='delete', on_click=lambda n=robotName: delete(n), color='warning').classes('text-base')

                start_polling(robotName, label_status, gz_toggle)