.PHONY: check smoke
check:
	python3 tools/check_scaffold.py
	python3 tools/build_lab.py --check
	python3 -m unittest discover -s tests -p 'test_*.py' -v

smoke:
	python3 tools/run_webots.py --smoke
