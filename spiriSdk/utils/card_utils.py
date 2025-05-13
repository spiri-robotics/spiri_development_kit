from nicegui import ui
from spiriSdk.utils.new_robot_utils import delete_robot, daemons

class RobotContainer:

    def __init__(self, destination) -> None:
        self.destination = destination
        self.daemonList = None

    def displayAddButton(self, addRobot) -> None:
        with self.destination:
            ui.button('Add Robot', on_click=addRobot.open, color='secondary')
            ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')


    def displayCards(self, addRobot, editRobot) -> None:
        addRobot.close()
        self.daemonList = daemons.keys()
        print(self.daemonList)
        self.destination.clear()
        with self.destination:
            self.displayAddButton(addRobot)
            for robotName in self.daemonList:
                with ui.card().classes('w-full'):
                    with ui.row(align_items='stretch').classes('w-full'):
                        with ui.card_section():
                            ui.label(f'{robotName}').classes('mb-5')
                            ui.label(f'active').classes('mt-5')
                        ui.space()
                        with ui.card_actions():
                            ui.button('Start', icon='play_arrow', color='positive').classes('m-1')
                            ui.button('Stop', icon='stop', color='warning').classes('m-1')
                            ui.button('Restart', icon='refresh', color='secondary').classes('m-1 mr-10')

                            async def delete():
                                if await delete_robot(robotName):
                                    ui.notify(f'{robotName} deleted')
                                else:
                                    ui.notify('error deleting robot')

                                self.displayCards(addRobot, editRobot)

                            with ui.dropdown_button(icon='settings', color='secondary'):
                                ui.item('Edit', on_click=editRobot.open)
                                ui.item('Delete', on_click=delete)
