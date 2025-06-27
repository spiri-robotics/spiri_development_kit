from nicegui import ui
from datetime import datetime
import subprocess

def get_battery_status():
    """Fetch battery percentage and charging status."""
    try:
        result = subprocess.run(
            ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"],
            capture_output=True, text=True, check=True
        ).stdout

        percent = "0%"
        charging = False

        for line in result.splitlines():
            if "percentage" in line:
                percent = line.split(":")[-1].strip()
            elif "state" in line:
                state = line.split(":")[-1].strip().lower()
                charging = state == "charging" or state == 'fully-charged'

        return percent, charging
    except:
        return "Unknown", False
    
def get_wifi_signal():
    """Fetch Wi-Fi signal strength."""
    try:
        result = subprocess.run(
            ["nmcli", "-f", "IN-USE,SIGNAL", "dev", "wifi"],
            capture_output=True, text=True, check=True
        ).stdout

        for line in result.splitlines():
            if line.startswith("*"):  # Currently connected network
                signal = int(line.split()[1])
                return signal

        return 0  # No connection
    except:
        return 0
    
def battery_icon(percent, charging):
    """Return the appropriate Material Symbol for battery."""
    percent = int(percent.replace("%", "")) if percent != "Unknown" else 0

    if charging:
        return "battery_charging_full"
    else:
        if percent > 95:
            return "battery_full"
        elif percent >= 85:
            return "battery_6_bar"
        elif percent >= 70:
            return "battery_5_bar"
        elif percent >= 50:
            return "battery_4_bar"
        elif percent >= 35:
            return "battery_3_bar"
        elif percent >= 20:
            return "battery_2_bar"
        elif percent > 0:
            return "battery_1_bar"
        else:
            return "battery_alert"

def wifi_icon(signal):
    """Return the appropriate Material Symbol for Wi-Fi signal strength."""
    if signal > 75:
        return "network_wifi"
    elif signal > 50:
        return "network_wifi_3_bar"
    elif signal > 25:
        return "network_wifi_2_bar"
    elif signal > 0:
        return 'network_wifi_1_bar'
    else:
        return "signal_wifi_off"
    
on = True  # Default dark mode state

async def header():
    with ui.header().classes('items-center'):
        with ui.row():
            ui.button('', icon='home', on_click=lambda: ui.navigate.to('/'), color='secondary').classes('text-base')
            ui.button('', icon='settings', on_click=lambda: ui.navigate.to('/settings'), color='secondary').classes('text-base')

        ui.space()

        dark = ui.dark_mode()
        dark.value = on

        def toggle_dark():
            global on
            dark.value = not dark.value
            on = dark.value
            dark_btn.props('icon="dark_mode"' if dark.value else 'icon="light_mode"')

        # Button with dynamic icon
        dark_btn = ui.button(
            '', 
            icon='dark_mode' if dark.value else 'light_mode', 
            on_click=toggle_dark, 
            color='secondary'
        ).classes('text-base')

        # Update icon when dark mode changes
        def update_icon():
            dark_btn.props('icon="dark_mode"' if dark.value else 'icon="light_mode"')
        dark.bind_value(update_icon)

        @ui.refreshable
        def clock():
            dateTime = datetime.astimezone(datetime.now())
            ui.label(dateTime.strftime('%A %B %d %Y')).classes('text-xl text-secondary')
            ui.label(dateTime.strftime('%X %Z')).classes('text-xl text-secondary')

        ui.timer(1.0, clock.refresh)
        
        with ui.row():
            percent, charging = get_battery_status()
            wifi_signal = get_wifi_signal()

            clock()

            # Battery icon
            ui.icon(battery_icon(percent, charging), color='secondary').classes("text-2xl")

            # Wi-Fi icon
            ui.icon(wifi_icon(wifi_signal), color='secondary').classes("text-2xl")
