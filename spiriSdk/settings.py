from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(os.environ.get("SDK_ROOT", ".")) / '.env')

CURRENT_PRIMARY_GROUP = os.getgid()
SDK_ROOT = Path(os.environ.get("SDK_ROOT", ".")).absolute()
