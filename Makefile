.PHONY: check smoke navigation
check:
	python3 tools/check_scaffold.py
	python3 tools/build_lab.py --check
	python3 tools/build_scenarios.py --check
	python3 tools/build_navigation_v2.py --check
	python3 tools/build_research_v3.py --check
	python3 tools/build_runtime_v3.py --check
	python3 tools/build_navigation_v4.py --check
	python3 tools/build_data03.py --check
	python3 tools/build_data04.py --check
	python3 tools/build_initialization_aa.py --check
	python3 -m unittest discover -s tests -p 'test_*.py' -v

smoke:
	python3 tools/run_webots.py --smoke

navigation:
	python3 tools/run_webots.py --navigation

data03:
	python3 tools/build_navigation_v4.py
	python3 tools/build_data03.py

data04:
	python3 tools/build_navigation_v4.py
	python3 tools/build_data04.py
