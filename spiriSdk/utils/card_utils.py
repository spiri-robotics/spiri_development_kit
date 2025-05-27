from spiriSdk.utils.daemon_utils import daemons, stop_container, start_container, restart_container, display_daemon_status, DaemonEvent
from spiriSdk.utils.new_robot_utils import delete_robot, save_robot_config
from spiriSdk.pages.tools import tools, prep_bot
import asyncio
from nicegui import ui
import os
from pathlib import Path
from spiriSdk.pages.new_robots import new_robots
from spiriSdk.pages.edit_robot import edit_robot
import httpx

async def is_service_ready(url: str, timeout: float = 0.5) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            return response.status_code == 200
    except Exception:
        return False

async def addRobot():
    with ui.dialog() as d, ui.card(align_items='stretch').classes('w-full'):
        await new_robots()

        async def submit(button):
            button = button.props(add='loading')

            # Import here instead of at the top to get the updated selected_robot
            from spiriSdk.pages.new_robots import selected_robot, selected_options
            await save_robot_config(selected_robot, selected_options)

            d.close()

            # Refresh display to update visible cards
            from spiriSdk.pages.home import container
            ui.notify(f"Robot {selected_robot} added successfully!")

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', color='secondary', on_click=d.close).classes('text-base')
            ui.button('Add', color='secondary', on_click=lambda e: submit(e.sender)).classes('text-base')
    
    d.open()

async def editRobot(robotName):
    with ui.dialog() as d, ui.card(align_items='stretch').classes('w-full'):
        await edit_robot(robotName)

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', on_click=d.close, color='secondary') 
            ui.button('Save', on_click=d.close, color='secondary')
    d.open()

class RobotContainer:

    def __init__(self, bigCard,) -> None:
        self.destination = bigCard
        DaemonEvent.subscribe(self.displayCards)

    async def displayButtons(self) -> None:
        with self.destination:
            with ui.row().classes('justify-items-stretch w-full'):
                ui.button('Add Robot', on_click=addRobot, color='secondary').classes('text-base')
                ui.space()
                await tools()

    async def displayCards(self) -> None:
        names = daemons.keys()
        self.destination.clear()
        with self.destination:
            await self.displayButtons()
            for robotName in names:
                ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

                with ui.card().classes('w-full'):
                    with ui.row(align_items='stretch').classes('w-full'):
                        with ui.card_section():
                            ui.label(f'{robotName}').classes('mb-5 text-lg font-semibold text-gray-900 dark:text-gray-100')
                            label_status = ui.label('Status: Loading...').classes('text-sm text-gray-600 dark:text-gray-300')

                            async def update_status(name, label):
                                status = await display_daemon_status(name)
                                label.text = f'Status: {status}'

                            # Initial status
                            await update_status(robotName, label_status)

                            # Periodic update
                            def start_polling(name, label):
                                async def polling_loop():
                                    while True:
                                        await update_status(name, label)
                                        await asyncio.sleep(5)
                                asyncio.create_task(polling_loop())

                            start_polling(robotName, label_status)
                        ui.space()
                        with ui.card_actions():
                            def make_stop(robot=robotName):
                                message = stop_container(robot)
                                ui.notify(message)

                            async def make_start(robot=robotName):
                                await start_container(robot)

                            async def make_restart(robot=robotName):
                                await restart_container(robot)
                            
                            ui.button('Start', on_click=make_start, icon='play_arrow', color='positive').classes('m-1 text-base')
                            ui.button('Stop', on_click=make_stop, icon='stop', color='warning').classes('m-1 text-base')
                            ui.button('Restart', on_click=make_restart, icon='refresh', color='secondary').classes('m-1 mr-10 text-base')

                            ui.button("Add robot to world", on_click=lambda: prep_bot(), color='secondary').classes('m-1 mr-10 text-base')

                            async def delete(n):
                                if await delete_robot(n):
                                    ui.notify(f'{n} deleted')
                                else:
                                    ui.notify('error deleting robot')

                            with ui.dropdown_button(icon='settings', color='secondary').classes('text-base') as drop:
                                ui.item('Edit', on_click=lambda n=robotName: editRobot(n))
                                ui.item('Delete', on_click=lambda n=robotName: delete(n))

                    # Display the robot's Docker services command            
                    with ui.row().classes('w-full'):
                        with ui.card_section():
                            command = f"Docker services command: docker --host=unix:///tmp/dind-sockets/{robotName}.socket ps"
                            def copy_text(robot=robotName):
                                command = f"docker --host=unix:///tmp/dind-sockets/{robot}.socket ps"
                                ui.run_javascript(f'''
                                    navigator.clipboard.writeText("{command}");
                                ''')
                                ui.notify("Copied to clipboard!")
                            ui.label(command).classes('text-sm text-gray-200')
                        ui.button("Copy to Clipboard", icon="content_copy", on_click=copy_text, color='secondary').classes('m-1 mr-10')
                        
                    # Display the robot's web interface if applicable
                    if str.join("-", robotName.split("-")[:1]) == "spiri_mu":
                        with ui.card_section():
                            url = f'http://{daemons[robotName].get_ip()}:{8124}'

                            loading = ui.spinner(size='lg')
                            while not await is_service_ready(url):
                                await asyncio.sleep(1)

                            loading.delete()

                            ui.html(f'<iframe src="{url}" width="1000" height="600"></iframe>')
                        
