# Issues found in `tax_calculator.py`

Line numbers refer to the **original** file (commit `638c236`). Within each
group, the most severe issues come first. IDs are the checks the tools define
for each pattern.

## Verification status (read this first)

| Tool | Status |
|------|--------|
| Flake8 | **Run for real.** 22 findings before, 0 after (`reports/flake8_report_before.txt`, `reports/flake8_report_after.txt`). |
| Pylint | **Not executed.** PyPI was unreachable where the work was done. Ruff's Pylint-equivalent rules (`PL`, `N`, `D`, `SIM`, `UP`) were used as a stand-in: 48 findings before, 0 after (`reports/ruff_proxy_*.txt`). |
| Bandit | **Not executed**, same reason. Ruff's Bandit-equivalent `S` rules were used: 4 security findings before, 0 after. |

Run `bash run_analysis.sh` in your venv to produce the real
`pylint_report_*.txt`, `bandit_report_*.txt` and `flake8_report_*.txt`, and
check the Pylint score (target above 9.5) and Bandit output. Paste anything
unexpected back and it can be fixed in minutes.

## A. Security (Bandit)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| RSA key too short (B505) | Security, High | 83 | `key_size=1024` is breakable; below the 2048-bit minimum. | `key_size=2048`. |
| Insecure cipher mode (B305) | Security, Medium | 77 | AES in ECB mode: identical plaintext gives identical ciphertext (the program even printed `True` for "same PAN encrypts the same way twice"), and it has no integrity check. | AES-GCM via `AESGCM` with a random 12-byte nonce; `decrypt_pan` added so the round trip is testable. |
| Hard-coded encryption key | Security, High | 15 | `PAN_KEY = b"0123456789abcdef"` is committed in source. Bandit's name heuristic may not flag it, but it is a hard-coded secret. | Key read from the `PAN_ENCRYPTION_KEY` environment variable; random per-process key if unset. |
| XML parsed with `xml.dom.minidom` (B318 / B408) | Security, Medium | 5, 86 | Form 16 input is untrusted. minidom is open to entity-expansion ("billion laughs") attacks. | `defusedxml.ElementTree`; DTDs/entities rejected. Verified with a malicious entity payload. Also raises a clear `ValueError` if `<salary>`/`<tds>` is missing. |
| `wsgiref.handlers.CGIHandler` (B412 httpoxy) | Security, High | 6, 92 | CGI exposes a client `Proxy:` header as `HTTP_PROXY`, which can redirect the server's outbound requests. | `HTTP_PROXY` removed from the environment before the handler runs; `# nosec B412` kept on the import with the justification in the comment. |

## B. Bugs no tool reports (found by reading the program output)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Flat rate applied to whole income | Bug | 19-41 | `taxable * slabRate(taxable)` taxes all income at the top slab's rate. Salary 18,00,000 printed **358,800**; correct is **150,800** (0 + 20,000 + 40,000 + 60,000 + 25,000, plus 4% cess). | New `slab_tax()` taxes each slice at its own rate; shared by both regimes. |
| Rebate boundary off by one | Bug | 39 | `taxable < REBATE_LIMIT_NEW` excludes taxable income of exactly 12,00,000, which the rebate covers. Salary 12,75,000 printed **124,800**; correct is **0**. | `<=`. |
| Cess charged after rebate | Bug | 37-41 | Cess was computed before the rebate zeroed the tax, so it was added to nothing. | Cess applied after the rebate: `tax * (1 + CESS)`. |
| `better_regime` inverted | Bug | 66 | Returned `"new"` when new tax was **greater**, i.e. recommended the more expensive regime. | `new_tax <= old_tax` returns `"new"`; ties go to new. |
| Age 80 mis-classified | Bug | 46 | `age > 80` gives a 80-year-old the general exemption (250,000, printed). Super seniors are 80 and above. | `age >= 80` (500,000). |
| PAN regex not anchored | Bug | 72 | `re.match` only anchors the start, so the 13-character `ABCDE1234FXYZ` validated as `True`. | `re.fullmatch`. |
| Negative taxable income | Bug | 35, 51 | Salary below the deductions produced a negative taxable figure. | Clamped at 0. |

## C. Pylint findings

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Missing docstrings (C0114, C0116) | Style | 1, every `def` | No module or function docstrings. | Added to the module and all functions. |
| camelCase names (C0103) | Style | 18-104 | `slabRate`, `taxAmount`, `lowerLimit`, etc. are not snake_case. | Renamed all functions and locals. |
| Too many returns / no-else-return (R0911, R1705) | Code smell | 18-32 | Seven `return`s in an `if/elif` chain. | Replaced by a data table (`NEW_SLABS`), later by `slab_tax()`. |
| Possibly-undefined loop variable (W0631) | Bug risk | 60 | `print(..., rate)` after the loop: `rate` is undefined if the loop never runs. It is also a stray debug print inside a calculation. | Removed. |
| Unused arguments (W0613) | Code smell | 85, 91 | `strict` and `debug` never used. | Removed. |
| Unused imports (W0611) | Style | 2-4 | `os`, `sys`, `json`. | `sys` and `json` removed; `os` is now used (key, nonce, httpoxy). |
| Unused variables (W0612) | Style | 36 | `bracket`, `checked`. | Removed. |
| Bare `except` (W0702) | Code smell | 73 | Hides every error, including `KeyboardInterrupt`. | `except TypeError`. |
| Iterating `dict.keys()` (C0201, C0206) | Style | 52-53 | Loop over `.keys()` then index. | `sum(deductions.values())`. |
| Chained comparison (R1716) | Style | 44 | `age >= 60 and age < 80`. | `SENIOR_AGE <= age < SUPER_SENIOR_AGE`. |
| `%` formatting (C0209) | Style | 99-104 | Old-style formatting. | f-strings. |
| Magic numbers | Style | 44-48 | Ages and exemption limits inline. | Named constants. |
| `main()` runs on import | Code smell | 106 | Importing the module executes the demo. | `if __name__ == "__main__":`. |

## D. Flake8 findings (all 22 cleared)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| F401 unused imports | Style | 2, 3, 4 | `os`, `sys`, `json`. | See C. |
| F841 unused locals | Style | 36 | `bracket`, `checked`. | Removed. |
| E702 semicolon | Style | 36 | Two statements on one line. | Split (then removed). |
| E722 bare `except` | Style | 73 | See C. | `except TypeError`. |
| E302 / E305 blank lines | Style | 18, 34, 43, 50, 63, 70, 76, 82, 85, 91, 94, 106 | Need two blank lines around top-level definitions. | Added. |
| E501 line too long | Style | 16, 98, 102, 103 | Longer than 79 characters. | Wrapped. |

## E. Noticed but deliberately not changed

- `80C` is applied uncapped in the sample (`200000`). The legal cap is
  1,50,000; the code has no per-section caps.
- The old regime has no Section 87A rebate and the new regime has no marginal
  relief just above 12,00,000. Neither is modelled by the original program, so
  adding them would be new features rather than fixes.
- `PAN_ENCRYPTION_KEY` must be set (32, 48 or 64 hex characters) if PANs need to
  be decrypted in a later run; otherwise a fresh key is generated each run.

## Commits

| Commit | Purpose |
|--------|---------|
| `fix(bandit)` | Section A |
| `fix(flake8)` | Section D |
| `fix(pylint)` | Section C |
| `fix(logic)` | Section B |
