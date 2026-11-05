"""Hidden check for the cli-log-analyzer case. Runs in the model's work folder.

Computes the true numbers from access.log itself, runs the model's script and compares,
then runs the model's own unit tests. Exit code 0 means everything matched.
"""
import collections
import json
import re
import subprocess
import sys

LINE = re.compile(r'^(\S+) \S+ \S+ \[\d+/\w+/\d+:(\d\d):\d\d:\d\d [^\]]+\] "(\S+) (\S+) [^"]*" (\d{3}) (\d+|-)')


def truth(path, top):
    valid, skipped = [], 0
    for raw in open(path, encoding="utf-8"):
        if not raw.strip():
            continue
        match = LINE.match(raw)
        if match:
            valid.append(match.groups())
        else:
            skipped += 1
    rank = lambda counter: [[k, v] for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:top]]
    statuses = collections.Counter(g[4] for g in valid)
    errors = sum(v for k, v in statuses.items() if k[0] in "45")
    return {
        "total_requests": len(valid),
        "skipped_lines": skipped,
        "unique_ips": len({g[0] for g in valid}),
        "top_ips": rank(collections.Counter(g[0] for g in valid)),
        "status_counts": dict(sorted(statuses.items())),
        "error_rate": round(errors / len(valid), 4),
        "top_paths": rank(collections.Counter(g[3] for g in valid)),
        "bytes_total": sum(int(g[5]) for g in valid if g[5] != "-"),
        "requests_per_hour": dict(sorted(collections.Counter(g[1] for g in valid).items())),
    }


def main():
    expected = truth("access.log", 3)
    run = subprocess.run([sys.executable, "log_report.py", "access.log", "--top", "3", "--format", "json"],
                         capture_output=True, text=True, timeout=60)
    print("log_report.py exit code:", run.returncode)
    try:
        got = json.loads(run.stdout)
    except ValueError:
        print("stdout is not JSON:", run.stdout[:500], run.stderr[-500:])
        return 1
    wrong = 0
    for key, value in expected.items():
        mine = got.get(key)
        if isinstance(value, float):
            same = isinstance(mine, (int, float)) and abs(mine - value) < 1e-4
        else:
            same = mine == value
        print(("ok    " if same else "WRONG ") + key + ("" if same else f": expected {value!r}, got {mine!r}"))
        wrong += not same
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-v"], capture_output=True, text=True,
                           timeout=120)
    ran = re.search(r"Ran (\d+) test", tests.stderr)
    count = int(ran.group(1)) if ran else 0
    print(f"model's own tests: {count} ran, exit code {tests.returncode}")
    print(f"{len(expected) - wrong} of {len(expected)} fields right")
    return 0 if wrong == 0 and run.returncode == 0 and tests.returncode == 0 and count >= 5 else 1


if __name__ == "__main__":
    sys.exit(main())
