import json
import sys

EXIT_CODES = {"ok": 0, "blocked": 2, "error": 1}


def merge(request_path, bundle_path):
    with open(request_path) as f:
        request = json.load(f)
    if "bundle" not in request and "medicationRequests" not in request:
        with open(bundle_path) as f:
            request["bundle"] = json.load(f)
    print(json.dumps(request))


def check_case(actual_path, code, expected_path):
    with open(actual_path) as f:
        actual = json.load(f)
    with open(expected_path) as f:
        expected = json.load(f)
    exit_ok = code == EXIT_CODES.get(expected.get("status"))
    if actual == expected and exit_ok:
        return 0
    print(f"  expected: {json.dumps(expected)}")
    print(f"  actual:   {json.dumps(actual)} (exit {code})")
    return 1


def check_lines(actual_path, expected_path):
    with open(actual_path) as f:
        actual = [json.loads(line) for line in f if line.strip()]
    with open(expected_path) as f:
        expected = [json.loads(line) for line in f if line.strip()]
    if actual == expected:
        return 0
    for i, (a, e) in enumerate(zip(actual, expected), 1):
        if a != e:
            print(f"  line {i} expected: {json.dumps(e)}")
            print(f"  line {i} actual:   {json.dumps(a)}")
    if len(actual) != len(expected):
        print(f"  expected {len(expected)} responses, got {len(actual)}")
    return 1


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "merge":
        merge(sys.argv[2], sys.argv[3])
    elif command == "case":
        sys.exit(check_case(sys.argv[2], int(sys.argv[3]), sys.argv[4]))
    elif command == "lines":
        sys.exit(check_lines(sys.argv[2], sys.argv[3]))
