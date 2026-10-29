from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"versions/navigation_v4"),str(ROOT/"versions/data_occupied_v1"),str(ROOT/"versions/data_history_v1")]
from blind_drone_v4.adapters.webots.lab import main
main()
