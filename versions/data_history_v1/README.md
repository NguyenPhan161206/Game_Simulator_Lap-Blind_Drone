# DATA-04: occupied-hit TTL

This development-only retention experiment uses DATA-03's latest-acquisition free evidence and expires each occupied hit 10 simulation seconds after its latest observation. A repeated hit refreshes the TTL; expired-hit inflation is rebuilt from the remaining hits. Unknown remains forbidden for route/command proof. The 16000-entry map budget is unchanged.

DATA-03 persistent-hit behavior is the paired reference. The study reuses the same 88 exposed development cases for diagnosis: 352 episodes, not new or independent cases. It is not validation/test evidence. Sensor cadence (32 ms), pose/control cadence, vehicle, worlds, scoring, free retention, planner, and repeats stay fixed. Ten seconds is an engineering point, not a safety recommendation or tuned optimum. v1/v2/v3/v4 source and locks remain unchanged.

Run `python3 tools/build_navigation_v4.py && python3 tools/build_data04.py` to materialize the isolated world/fixture, then use the Webots/Xvfb workflow. `python3 tools/run_data04.py --output artifacts/data04-hit-ttl` runs development only. No held-out split exists.
