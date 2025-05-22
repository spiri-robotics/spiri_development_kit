from spiriSdk.utils.daemon_utils import daemons, stop_container, start_container, restart_container, display_daemon_status
from spiriSdk.utils.new_robot_utils import delete_robot, save_robot_config
from spiriSdk.pages.tools import tools, prep_bot
import asyncio
import os
from pathlib import Path
from spiriSdk.pages.new_robots import new_robots#, clear_fields
from spiriSdk.pages.edit_robot import edit_robot

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
            await container.displayCards()
            ui.notify(f"Robot {selected_robot} added successfully!")

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', color='secondary', on_click=d.close).classes('text-base')
            ui.button('Add', color='secondary', on_click=lambda e: submit(e.sender)).classes('text-base')
    
    d.open()

async def editRobot(robotID):
    with ui.dialog() as d, ui.card(align_items='stretch').classes('w-full'):
        await edit_robot(robotID)

        with ui.card_actions().props('align=center'):
            ui.button('Cancel', on_click=d.close, color='secondary') 
            ui.button('Save', on_click=d.close, color='secondary')
    d.open()

class RobotContainer:

    def __init__(self, bigCard,) -> None:
        self.destination = bigCard

    async def displayButtons(self) -> None:
        with self.destination:
            with ui.row().classes('justify-items-stretch w-full'):
                ui.button('Add Robot', on_click=addRobot, color='secondary').classes('text-base')
                ui.space()
                await tools()

    async def displayCards(self) -> None:
        names = daemons.keys()
        print(names)
        self.addRobot.close()
        self.destination.clear()
        with self.destination:
            await self.displayButtons()
            for robotID in names:
                ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                folder_name = f"{robotID}"
                folder_path = os.path.join(ROOT_DIR, "data", folder_name)
                config_path = os.path.join(folder_path, "config.env")

                robotName = robotID

                with open(config_path, "r") as options:
                    for line in options:
                        if 'name='.casefold() in line.casefold():
                            robotName = line[5:]

                with ui.card().classes('w-full'):
                    with ui.row(align_items='stretch').classes('w-full'):
                        with ui.card_section():
                            ui.label(f'{robotName}').classes('mb-5 text-lg font-semibold text-gray-900 dark:text-gray-100')
                            label_status = ui.label('Status: Loading...').classes('text-sm text-gray-600 dark:text-gray-300')

                            async def update_status(name, label):
                                status = await display_daemon_status(name)
                                label.text = f'Status: {status}'

                            # Initial status
                            await update_status(robotID, label_status)

                            # Periodic update
                            def start_polling(name, label):
                                async def polling_loop():
                                    while True:
                                        await update_status(name, label)
                                        await asyncio.sleep(5)
                                asyncio.create_task(polling_loop())

                            start_polling(robotID, label_status)
                        ui.space()
                        with ui.card_actions():
                            def make_stop(robot=robotID):
                                stop_container(robot)

                            async def make_start(robot=robotID):
                                await start_container(robot)

                            async def make_restart(robot=robotID):
                                await restart_container(robot)
                            
                            ui.button('Start', on_click=make_start, icon='play_arrow', color='positive').classes('m-1 text-base')
                            ui.button('Stop', on_click=make_stop, icon='stop', color='warning').classes('m-1 text-base')
                            ui.button('Restart', on_click=make_restart, icon='refresh', color='secondary').classes('m-1 mr-10 text-base')

                            ui.button("Add robot to world", on_click=lambda: prep_bot(), color='secondary').classes('m-1 mr-10 text-base')

                            async def delete(n):
                                if await delete_robot(n):
                                    ui.notify(f'{n} deleted')
                                    await self.displayCards()
                                else:
                                    ui.notify('error deleting robot')

                            with ui.dropdown_button(icon='settings', color='secondary').classes('text-base') as drop:
                                ui.item('Edit', on_click=lambda n=robotID: editRobot(n))
                                ui.item('Delete', on_click=lambda n=robotID: delete(n))
                    with ui.row().classes('w-full'):
                        with ui.card_section():
                            command = f"Docker services command: unix:///tmp/dind-sockets/{robotName}.socket"
                            def copy_text(robot=robotName):
                                command = f"Docker services command: unix:///tmp/dind-sockets/{robot}.socket"
                                ui.run_javascript(f'''
                                    navigator.clipboard.writeText("{command}");
                                ''')
                                ui.notify("Copied to clipboard!")
                            ui.label(command).classes('text-sm text-gray-200')
                        ui.button("Copy to Clipboard", on_click=copy_text, color='secondary').classes('m-1 mr-10')
                            
