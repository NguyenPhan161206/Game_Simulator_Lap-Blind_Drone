from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"versions/navigation_v4"),str(ROOT/"versions/retention_cold_v1")]
from blind_drone_retention.adapters.webots.lab import main
main()
