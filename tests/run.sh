#!/bin/bash
set -u

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1
lake build dosegate >/dev/null || { echo "build failed"; exit 1; }
bin="$root/.lake/build/bin/dosegate"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

pass=0
fail=0

for request in tests/cases/*.request.json; do
    name="$(basename "$request" .request.json)"
    expected="tests/cases/$name.expected.json"
    python3 tests/check.py merge "$request" tests/bundle.json > "$out/in.json"
    "$bin" render < "$out/in.json" > "$out/actual.json"
    code=$?
    if python3 tests/check.py case "$out/actual.json" "$code" "$expected"; then
        pass=$((pass + 1))
    else
        echo "FAIL render $name"
        fail=$((fail + 1))
    fi
done

"$bin" serve < tests/serve/session.in.jsonl > "$out/serve.jsonl"
if python3 tests/check.py lines "$out/serve.jsonl" tests/serve/session.expected.jsonl; then
    pass=$((pass + 1))
else
    echo "FAIL serve session"
    fail=$((fail + 1))
fi

echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
