# DATA-03 occupied-only persistent map trial

This is a separate, development-only data representation experiment. It compares the frozen v3 mapped reference against the v4 observed-detour candidate, then tests a third candidate that persists occupied hits while retaining free cells only for the latest unique scan. Old free observations expire at each new scan. Movement remains guarded by measured free cells; unknown is never treated as free. The 16000-entry budget counts free, occupied and derived blocked-set entries separately, including overlapping coordinates.

The study reuses exposed v4 development cases only for engineering diagnosis. It is not validation or test evidence. The comparison holds sensor cadence (32 ms), pose/control cadence, vehicle, world cases, scoring and repeats fixed. v3 source, v4 package, and legacy locks remain unchanged.

Run `python3 tools/build_data03.py` to materialize the isolated world/fixture, then run the Webots/Xvfb workflow. `python3 tools/run_data03.py --output artifacts/data03-occupied-only` runs development only. No held-out split exists.
