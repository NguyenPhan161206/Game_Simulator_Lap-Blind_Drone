from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"versions/navigation_v4"),str(ROOT/"versions/initialization_aa_v1")]
from blind_drone_aa.adapters.webots.lab import main
main()
