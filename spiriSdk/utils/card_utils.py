from nicegui import ui
from spiriSdk.pages.styles import styles

class RobotContainer:

    def __init__(self) -> None:
        self.card = None
        self.daemons = []


    def add_card(self, robotName, editRobot, bigCard, addRobot) -> None:
        addRobot.close()
        self.daemons.append(robotName)
        print(self.daemons)
        self.card = bigCard
        with self.card:
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

                        with ui.dropdown_button(icon='settings', color='secondary'):
                            ui.item('Edit', on_click=editRobot.open)
                            ui.item('Delete')

    def remove_card(self, robotName) -> None:
        self.card.delete(robotName)

    def display(self, addRobot, bigCard) -> None:
        self.card = bigCard
        with self.card:
            ui.button('Add Robot', on_click=addRobot.open, color='secondary')
            ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')


container = RobotContainer()