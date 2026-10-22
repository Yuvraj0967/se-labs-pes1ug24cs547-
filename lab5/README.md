# Lab 5: Static Code Analysis — Income Tax Calculator

**Your file:** `tax_calculator.py`

Follow the lab handout for the full instructions.

## About the program

A personal income-tax calculator. It works out tax under the new and old regimes (standard deduction, slab rates, Section 87A rebate, 80C/80D deductions and cess), picks the better regime, validates and encrypts PAN numbers, generates a signing key, reads salary and TDS from a Form-16 XML file, and can run as a CGI app. The slabs are those configured in the program (modelled on FY 2025-26) and are for teaching only, not tax advice.

The code works, but only just. It has quality, style and security problems of the kind Pylint, Flake8 and Bandit are built to find.

## What to do

1. **Install the program's packages** (it uses Cryptography):
   ```bash
   python -m pip install cryptography
   ```

2. **Run it** and read the output carefully:
   ```bash
   python tax_calculator.py
   ```
   Check whether every tax figure it prints makes sense, then try changing the inputs in `main()` to see what happens. Not every problem in this file is something a tool will flag, so pay attention to output that looks wrong.

3. **Install the tools:**
   ```bash
   python -m pip install pylint bandit flake8 defusedxml
   ```

4. **Run the analysis** and save the reports:
   ```bash
   python -m pylint tax_calculator.py > pylint_report.txt
   python -m bandit -r tax_calculator.py > bandit_report.txt
   python -m flake8 tax_calculator.py > flake8_report.txt
   ```

5. **Document the issues** in `issues.md` using this table (at least 4 rows, high and medium severity first):

   | Issue | Type | Line(s) | Description | Fix Approach |
   |-------|------|---------|-------------|--------------|
   | ... | ... | ... | ... | ... |

6. **Fix the code.** Fix at least 4 of the issues you documented, then rerun all three tools to confirm they are gone. Repeat until you are satisfied. The program should still do its job when you are done.

7. **Reflect.** Answer the four reflection questions from the handout in `reflection.md`.

## Deliverables

1. `tax_calculator.py`: your cleaned version, with at least 4 issues fixed.
2. `issues.md`: the completed issue table.
3. `reflection.md`: your answers to the reflection questions.

**Target:** aim for a Pylint score above 9.5 on your final file. A perfect 10.00/10 is very good.

Be ready to explain the bugs you found and how you fixed them. You may be called on to present.
