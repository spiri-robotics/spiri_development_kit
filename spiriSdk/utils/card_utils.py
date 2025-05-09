from nicegui import ui
from spiriSdk.utils.new_robot_utils import daemons

class RobotContainer:

    def __init__(self, bigCard) -> None:
        self.destination = bigCard
        self.daemons = ['thing1', 'thing2', 'thing3']

    def displayAddButton(self, addRobot) -> None:
        with self.destination:
            ui.button('Add Robot', on_click=addRobot.open, color='secondary')
            ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')


    def displayCards(self) -> None:
        self.destination.clear()
        with self.destination:
            for robotName in self.daemons:
                with ui.card().classes('w-[calc(50vw-24px)]'):
                    with ui.card_section():
                        ui.label(f'{robotName}').classes('mb-5')
                        ui.label(f'active').classes('mt-5')
                    ui.space()
                    with ui.card_actions():
                        ui.button('Start', icon='play_arrow', color='positive').classes('m-1')
                        ui.button('Stop', icon='stop', color='warning').classes('m-1')
                        ui.button('Restart', icon='refresh', color='secondary').classes('m-1 mr-10')

                        with ui.dropdown_button(icon='settings', color='secondary'):
                            ui.item('Edit', on_click=lambda: print("edit"))
                            ui.item('Delete', on_click=lambda: self.remove_card(robotName, self.destination))


    # def add_card(self, robotName, editRobot, bigCard, addRobot) -> None:
    #     addRobot.close()
    #     self.daemons.append(robotName)
    #     print(self.daemons)

    #     #newCard = RobotCard(bigCard, robotName, addRobot, editRobot)
    #     #self.cards.append(newCard)
    #     self.main = bigCard
    #     with self.main:
    #         with ui.card().classes('w-full'):
    #             with ui.row(align_items='stretch').classes('w-full'):
    #                 with ui.card_section():
    #                     ui.label(f'{robotName}').classes('mb-5')
    #                     ui.label(f'active').classes('mt-5')
    #                 ui.space()
    #                 with ui.card_actions():
    #                     ui.button('Start', icon='play_arrow', color='positive').classes('m-1')
    #                     ui.button('Stop', icon='stop', color='warning').classes('m-1')
    #                     ui.button('Restart', icon='refresh', color='secondary').classes('m-1 mr-10')

    #                     with ui.dropdown_button(icon='settings', color='secondary'):
    #                         ui.item('Edit', on_click=editRobot.open)
    #                         ui.item('Delete', on_click=lambda: self.remove_card(robotName, bigCard))

    # def remove_card(self, robotName, bigCard) -> None:
    #     self.main = bigCard
    #     self.daemons.remove(robotName)

    def display(self, addRobot, bigCard) -> None:
        self.main = bigCard
        with self.main:
            ui.button('Add Robot', on_click=addRobot.open, color='secondary')
            ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary')
