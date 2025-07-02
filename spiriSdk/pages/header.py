from nicegui import ui
from datetime import datetime
import subprocess
from spiriSdk.ui.ToggleButton import ToggleButton

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
        print('not charging')
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
    ui.dark_mode(None)

    @ui.refreshable
    def clock():
        dateTime = datetime.astimezone(datetime.now())
        ui.label(dateTime.strftime('%A %B %d %Y')).classes('text-xl font-light absolute top-10 right-60 z-50')
        ui.label(dateTime.strftime('%X %Z')).classes('text-xl font-light absolute top-10 right-24 z-50')

    ui.timer(1.0, clock.refresh)
    
    percent, charging = get_battery_status()
    wifi_signal = get_wifi_signal()

    clock()

    # Battery icon
    ui.icon(battery_icon(percent, charging)).classes("text-2xl absolute top-10 right-12 z-50")

    # Wi-Fi icon
    ui.icon(wifi_icon(wifi_signal)).classes("text-2xl absolute top-10 right-4 z-50")
