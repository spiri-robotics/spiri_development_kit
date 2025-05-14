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
        if percent > 95:
            return "battery_charging_full"
        elif percent >= 85:
            return 'battery_charging_90'
        elif percent >= 70:
            return "battery_charging_80"
        elif percent >= 50:
            return "battery_charging_60"
        elif percent >= 35:
            return "battery_charging_50"
        elif percent >= 20:
            return "battery_charging_30"
        elif percent > 0:
            return "battery_charging_20"
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


async def header():

    with ui.header().classes('content-center border-b-4 border-[#274c77]'):
        ui.button('actual add robot page', on_click=lambda: ui.navigate.to('/new_robots'), color='secondary').classes('text-base')
        ui.space()

        @ui.refreshable
        def clock():
            dateTime = datetime.astimezone(datetime.now())
            ui.label(dateTime.strftime('%A %B %m %Y')).classes('text-xl text-secondary')
            ui.label(dateTime.strftime('%X %Z')).classes('text-xl text-secondary')

        ui.timer(1.0, clock.refresh)
        
        with ui.row().classes('self-center'):
            percent, charging = get_battery_status()
            wifi_signal = get_wifi_signal()

            clock()

            # Battery icon
            ui.icon(battery_icon(percent, charging), color='secondary').classes("text-2xl")

            # Wi-Fi icon
            ui.icon(wifi_icon(wifi_signal), color='secondary').classes("text-2xl")
