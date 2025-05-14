from nicegui import ui, run
from spiriSdk.utils.daemon_utils import daemons, stop_container, start_container, restart_container, display_daemon_status
from spiriSdk.utils.new_robot_utils import delete_robot
from spiriSdk.pages.tools import prep_bot
import asyncio

class RobotContainer:

    def __init__(self, bigCard, addRobot, editRobot) -> None:
        self.destination = bigCard
        self.addRobot = addRobot
        self.editRobot = editRobot

    def displayAddButton(self) -> None:
        with self.destination:
            ui.button('Add Robot', on_click=self.addRobot.open, color='secondary')
            ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')

    async def displayCards(self) -> None:
        names = daemons.keys()
        print(names)
        self.addRobot.close()
        self.destination.clear()
        with self.destination:
            self.displayAddButton()
            for robotName in names:
                with ui.card().classes('w-full'):
                    with ui.row(align_items='stretch').classes('w-full'):
                        with ui.card_section():
                            ui.label(f'{robotName}').classes('mb-5')
                            label_status = ui.label('Status: Loading...').classes('text-sm text-gray-500')

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
                                stop_container(robot)

                            def make_start(robot=robotName):
                                start_container(robot)

                            def make_restart(robot=robotName):
                                restart_container(robot)
                            ui.button('Start', on_click=make_start, icon='play_arrow', color='positive').classes('m-1')
                            ui.button('Stop', on_click=make_stop, icon='stop', color='warning').classes('m-1')
                            ui.button('Restart', on_click=make_restart, icon='refresh', color='secondary').classes('m-1 mr-10')

                            ui.button("Add robot to world", on_click=lambda: prep_bot(robotName)).classes('m-1 mr-10')

                            async def delete(n):
                                if await delete_robot(n):
                                    ui.notify(f'{n} deleted')
                                else:
                                    ui.notify('error deleting robot')

                                await self.displayCards()

                            with ui.dropdown_button(icon='settings', color='secondary'):
                                ui.item('Edit', on_click=self.editRobot.open)
                                ui.item('Delete', on_click=lambda n=robotName: delete(n))

    def assignAddRobot(self, addRobot) -> None:
        self.addRobot = addRobot

    def assignEditRobot(self, editRobot) -> None:
        self.editRobot = editRobot
