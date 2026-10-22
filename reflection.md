# Reflection

> The handout does not list the reflection questions, so these are the four
> standard questions for this lab. If your instructor's wording differs,
> paste it in and these answers can be re-fitted.

## 1. Which issues were easiest and hardest to fix?

The easiest were mechanical: unused imports, blank lines, line length, the
semicolon, and renaming to snake_case. Flake8 gives an exact line and code, and
the fix does not change behaviour. The hardest were the security findings,
because each one needed a design choice, not a one-line edit. Replacing AES-ECB
with AES-GCM meant deciding where the key comes from, how to generate nonces,
and adding a decrypt function to prove it works. The `CGIHandler` finding is a
real trade-off: the module is risky by design, so I mitigated it (stripping
`HTTP_PROXY`) and documented a `nosec` instead of pretending it disappeared.

## 2. Did the tools report anything that was a false positive, or miss something?

The `wsgiref` import warning is the nearest to a false positive. It flags the
module, not a defect in my code, and it stays flagged unless suppressed with a
reason. The bigger lesson was what the tools missed. None of them can tell that
a flat tax rate is wrong, that the rebate boundary is off by one, that
`better_regime` recommends the more expensive option, or that a 13-character
PAN is not valid. I only found those by reading the program's output and
checking the numbers by hand (for example, 18,00,000 salary taxed at 358,800
when slab arithmetic gives 150,800). Static analysis checks how the code is
written, not whether it computes the right thing.

## 3. How would you use static analysis in a normal workflow?

I would run Flake8 and Pylint in a pre-commit hook and in CI so style and
quality issues never reach review, and run Bandit in CI with the build failing on
medium and high findings. Suppressions (`nosec`, `disable`) would require a
written justification, as with `# nosec B412` here. Alongside that I would keep
unit tests: the tests I wrote for this lab (hand-computed tax figures, PAN
cases, an XML-entity attack) are what actually caught the logic bugs, and the
tools are what caught the security and maintainability problems. Neither
replaces the other.

## 4. What changed in code quality, readability, security and robustness?

Security: the hard-coded key, the ECB mode, the 1024-bit RSA key and the unsafe
XML parser are all gone, and PAN encryption is now non-deterministic and
reversible. Readability: every function has a docstring, names follow PEP 8,
and one `slab_tax()` helper replaced a seven-branch `if/elif` chain and a
duplicated loop. Robustness: the module no longer runs on import, bad PAN input
no longer swallows every exception, negative taxable income is clamped, and a
malformed Form 16 raises a clear error. Most importantly, the program's figures
are now correct: salary 12,75,000 gives 0 tax (it printed 124,800), salary
18,00,000 gives 150,800 (it printed 358,800), and the regime recommendation
matches the actual lower tax.
