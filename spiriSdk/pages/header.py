from nicegui import ui
from spiriSdk.pages.styles import styles
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
                charging = state == "charging"

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
    elif percent > 80:
        return "battery_full"
    elif percent > 60:
        return "battery_5_bar"
    elif percent > 40:
        return "battery_4_bar"
    elif percent > 20:
        return "battery_2_bar"
    else:
        return "battery_alert"

def wifi_icon(signal):
    """Return the appropriate Material Symbol for Wi-Fi signal strength."""
    if signal > 75:
        return "signal_wifi_4_bar"
    elif signal > 50:
        return "signal_wifi_3_bar"
    elif signal > 25:
        return "signal_wifi_2_bar"
    elif signal > 0:
        return "signal_wifi_1_bar"
    else:
        return "signal_wifi_off"


async def header():

    with ui.header():
        with ui.row():
            ui.button('Home', on_click=lambda: ui.navigate.to('/'), color='secondary')
            ui.button('Tools', on_click=lambda: ui.navigate.to('/tools'), color='secondary')
            ui.button('Manage Robots', on_click=lambda: ui.navigate.to('/manage_robots'), color='secondary')

        ui.space()

        @ui.refreshable
        def clock():
            dateTime = datetime.astimezone(datetime.now())
            ui.label(dateTime.strftime('%A %B %m %Y')).classes('text-lg text-secondary')
            ui.label(dateTime.strftime('%X %Z')).classes('text-lg text-secondary')

        ui.timer(1.0, clock.refresh)
        
        with ui.row():
            percent, charging = get_battery_status()
            wifi_signal = get_wifi_signal()

            clock()

            # Battery icon
            ui.icon(battery_icon(percent, charging), color='secondary').classes("text-2xl")

            # Wi-Fi icon
            ui.icon(wifi_icon(wifi_signal), color='secondary').classes("text-2xl")
