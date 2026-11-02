from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"versions/navigation_v4"),str(ROOT/"versions/initialization_aa_v1"),str(ROOT/"versions/retention_cold_v1"),str(ROOT/"versions/sensor_pilots_v1"),str(ROOT/"versions/efficiency_eval_v1"),str(ROOT/"versions/efficiency_runtime_v1"),str(ROOT/"tools")]
from blind_drone_sensor_pilots.adapters.webots.drone import main
main()
