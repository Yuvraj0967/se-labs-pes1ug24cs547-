#!/usr/bin/env bash
# Regenerates the before/after reports with the REAL tools (Lab 5, Step 2).
# Usage (inside your activated venv, with pylint bandit flake8 defusedxml
# cryptography installed):   bash run_analysis.sh
cd "$(dirname "$0")" || exit 1
root=$(pwd)
base=638c236                       # original commit, before any fixes
mkdir -p reports
tmp=$(mktemp -d)
git show "$base:tax_calculator.py" > "$tmp/tax_calculator.py"

run() {                            # run <before|after> <directory>
    ( cd "$2" || exit 1
      python -m pylint tax_calculator.py > "$root/reports/pylint_report_$1.txt"
      python -m bandit -r tax_calculator.py > "$root/reports/bandit_report_$1.txt"
      python -m flake8 tax_calculator.py > "$root/reports/flake8_report_$1.txt" )
}
run before "$tmp"
run after "$root"
rm -rf "$tmp"

echo "Pylint  before: $(grep -o 'rated at [0-9.]*/10' reports/pylint_report_before.txt)"
echo "Pylint  after : $(grep -o 'rated at [0-9.]*/10' reports/pylint_report_after.txt)"
echo "Bandit  before: $(grep -c '>> Issue' reports/bandit_report_before.txt) issues"
echo "Bandit  after : $(grep -c '>> Issue' reports/bandit_report_after.txt) issues"
echo "Flake8  before: $(wc -l < reports/flake8_report_before.txt) lines"
echo "Flake8  after : $(wc -l < reports/flake8_report_after.txt) lines"
