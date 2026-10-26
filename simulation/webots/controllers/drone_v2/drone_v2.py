from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"src"))
from blind_drone.adapters.webots.drone_v2 import main
main()
