from dotenv import load_dotenv
from pathlib import Path
import os
import socket
from loguru import logger

load_dotenv(Path(os.environ.get("SDK_ROOT", ".")) / '.env')

CURRENT_PRIMARY_GROUP = os.getgid()
SDK_ROOT = Path(os.environ.get("SDK_ROOT", ".")).absolute()

ROBOT_DATA_ROOT = SDK_ROOT / "data"
ROBOT_DATA_ROOT.mkdir(parents=True, exist_ok=True)

GROUND_CONTROL_ADDRESS = os.environ.get("GROUND_CONTROL_ADDRESS")
if not os.environ.get("GROUND_CONTROL_ADDRESS"):
    GROUND_CONTROL_ADDRESS = str(socket.gethostbyname(socket.gethostname()))
    logger.warning(f"GROUND_CONTROL_ADDRESS not set, using {GROUND_CONTROL_ADDRESS} as auto-detected default")
    
SIM_ADDRESS = os.environ.get("SIM_ADDRESS")
if not os.environ.get("SIM_ADDRESS"):
    SIM_ADDRESS = str(socket.gethostbyname(socket.gethostname()))
    logger.warning(f"SIM_ADDRESS not set, using {SIM_ADDRESS} as auto-detected default")
