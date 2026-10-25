"""Privileged world/reset/evaluation entry point; separate from drone control."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from blind_drone.adapters.webots.lab import main

main()
