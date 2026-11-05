title: Log analyzer CLI with tests
kind: code
fixtures: fixtures/cli-log-analyzer
check: python3 {case_dir}/verify/cli-log-analyzer.py
expect: log_report.py, test_log_report.py, REPORT.md
timeout: 1800
---
This folder contains access.log, a web server log in the combined log format. Write a Python 3 command-line
tool `log_report.py` that analyzes it, using only the standard library.

Usage: `python3 log_report.py access.log [--top N] [--format json|text]` (defaults: --top 5, --format text).

With `--format json` it prints exactly one JSON object to stdout with these keys:
- `total_requests`: number of valid lines;
- `skipped_lines`: non-empty lines that do not parse (they must not crash the tool);
- `unique_ips`: number of distinct client IPs;
- `top_ips`: the N most frequent IPs as `[[ip, count], ...]`, ordered by count descending, ties by IP ascending;
- `status_counts`: object mapping each status code as a string (e.g. "404") to its count;
- `error_rate`: share of 4xx and 5xx responses among valid lines, rounded to 4 decimals;
- `top_paths`: the N most requested paths, same format and ordering as `top_ips`;
- `bytes_total`: sum of response sizes, where a size of "-" counts as 0;
- `requests_per_hour`: object mapping the two-digit hour of the timestamp (e.g. "08") to its count.

With `--format text` it prints the same information as a readable report.

Also write `test_log_report.py` with at least 5 unittest tests (including a malformed line and a "-" size)
and make sure `python3 -m unittest discover -v` passes. Run the tool on access.log to check it.

When you are done, write REPORT.md in this folder: what you did, the files you created, how you checked
the result, and anything that did not work.
