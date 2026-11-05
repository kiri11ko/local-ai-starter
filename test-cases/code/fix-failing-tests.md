title: Fix the bugs so the tests pass
kind: code
fixtures: fixtures/fix-failing-tests
check: python3 {case_dir}/verify/fix-failing-tests.py
expect: REPORT.md
timeout: 1200
---
This folder contains `inventory.py` and its unit tests `test_inventory.py`. Several tests fail.
Run `python3 -m unittest -v` to see them, find the bugs in `inventory.py` and fix them.
Do not change `test_inventory.py`: the tests are the specification. Keep the public functions and their
signatures. Run the tests again until all of them pass.

When you are done, write REPORT.md in this folder: every bug you found (what was wrong and how you fixed it),
the final test output, and anything that did not work.
