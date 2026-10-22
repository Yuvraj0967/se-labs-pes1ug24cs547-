"""Personal income-tax calculator (new and old regime, modelled on FY 2025-26).

The slabs are configured for teaching purposes only and are not tax advice.
"""

import os
import re
from wsgiref.handlers import CGIHandler  # nosec B412 - HTTP_PROXY stripped
from defusedxml import ElementTree
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Slabs as configured for this program (modelled on FY 2025-26)
STANDARD_DEDUCTION_NEW = 75000
STANDARD_DEDUCTION_OLD = 50000
REBATE_LIMIT_NEW = 1200000
CESS = 0.04
NONCE_SIZE = 12
SENIOR_AGE = 60
SUPER_SENIOR_AGE = 80
EXEMPTION_GENERAL = 250000
EXEMPTION_SENIOR = 300000
EXEMPTION_SUPER_SENIOR = 500000
NEW_SLABS = [
    (400000, 0.0),
    (800000, 0.05),
    (1200000, 0.10),
    (1600000, 0.15),
    (2000000, 0.20),
    (2400000, 0.25),
    (float("inf"), 0.30),
]
OLD_SLABS = [
    (250000, 0.0),
    (500000, 0.05),
    (1000000, 0.20),
    (float("inf"), 0.30),
]


def slab_rate(income):
    """Return the new-regime rate of the slab that contains ``income``."""
    return next(rate for limit, rate in NEW_SLABS if income <= limit)


def new_regime_tax(salary):
    """Return new-regime tax (including cess) for ``salary``."""
    taxable = salary - STANDARD_DEDUCTION_NEW
    tax_amount = taxable * slab_rate(taxable)
    cess_amount = tax_amount * CESS
    if taxable < REBATE_LIMIT_NEW:
        tax_amount = 0
    return int(tax_amount + cess_amount)


def basic_exemption(age):
    """Return the old-regime basic exemption limit for a taxpayer's age."""
    if SENIOR_AGE <= age < SUPER_SENIOR_AGE:
        return EXEMPTION_SENIOR
    if age > SUPER_SENIOR_AGE:
        return EXEMPTION_SUPER_SENIOR
    return EXEMPTION_GENERAL


def old_regime_tax(salary, age, deductions):
    """Return old-regime tax (including cess) after ``deductions``.

    ``deductions`` maps a section name (e.g. "80C") to the amount claimed.
    """
    taxable = salary - STANDARD_DEDUCTION_OLD - sum(deductions.values())
    total_tax = 0
    lower_limit = basic_exemption(age)
    for limit, rate in OLD_SLABS:
        if taxable > lower_limit and rate > 0:
            total_tax += (min(taxable, limit) - lower_limit) * rate
        lower_limit = max(lower_limit, limit)
    return int(total_tax * (1 + CESS))


def better_regime(salary, age, deductions):
    """Return "new" or "old", whichever regime is chosen for the taxpayer."""
    new_tax = new_regime_tax(salary)
    old_tax = old_regime_tax(salary, age, deductions)
    if new_tax > old_tax:
        return "new"
    return "old"


def is_valid_pan(pan):
    """Return True if ``pan`` looks like a PAN number."""
    try:
        return bool(re.match("[A-Z]{5}[0-9]{4}[A-Z]", pan))
    except TypeError:
        return False


def load_pan_key():
    """Return the AES key used to protect PAN numbers.

    The key comes from the environment, never from source code. Set
    PAN_ENCRYPTION_KEY to 32/48/64 hex characters to keep PANs decryptable
    across runs; otherwise a random key is used for this process only.
    """
    key_hex = os.environ.get("PAN_ENCRYPTION_KEY")
    if key_hex:
        return bytes.fromhex(key_hex)
    return AESGCM.generate_key(bit_length=256)


PAN_KEY = load_pan_key()


def encrypt_pan(pan):
    """Encrypt ``pan`` with AES-GCM and return nonce + ciphertext as hex."""
    nonce = os.urandom(NONCE_SIZE)
    cipher_text = AESGCM(PAN_KEY).encrypt(nonce, pan.encode(), None)
    return (nonce + cipher_text).hex()


def decrypt_pan(token):
    """Reverse :func:`encrypt_pan` and return the PAN as text."""
    raw = bytes.fromhex(token)
    plain = AESGCM(PAN_KEY).decrypt(raw[:NONCE_SIZE], raw[NONCE_SIZE:], None)
    return plain.decode()


def signing_key():
    """Generate a fresh 2048-bit RSA signing key."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def parse_form16(xml_text):
    """Return ``(salary, tds)`` read from a Form 16 XML string."""
    root = ElementTree.fromstring(xml_text)
    salary_text = root.findtext(".//salary")
    tds_text = root.findtext(".//tds")
    if salary_text is None or tds_text is None:
        raise ValueError("Form 16 XML must contain <salary> and <tds>")
    return int(salary_text), int(tds_text)


def run_as_cgi(app):
    """Serve the WSGI ``app`` through CGI."""
    # httpoxy mitigation: CGI turns a client "Proxy:" header into HTTP_PROXY.
    os.environ.pop("HTTP_PROXY", None)
    CGIHandler().run(app)


def main():
    """Print a short demonstration of the calculator."""
    print("New regime, salary 12,75,000:", new_regime_tax(1275000))
    print("New regime, salary 18,00,000:", new_regime_tax(1800000))
    deductions = {"80C": 200000, "80D": 30000}
    print("Old regime, salary 18,00,000:",
          old_regime_tax(1800000, 35, deductions))
    print(f"Better regime: {better_regime(1800000, 35, deductions)}")
    print(f"Basic exemption at age 80: {basic_exemption(80)}")
    print("PAN 'ABCDE1234FXYZ' valid?", is_valid_pan("ABCDE1234FXYZ"))
    first = encrypt_pan("ABCDE1234F")
    second = encrypt_pan("ABCDE1234F")
    print("Same PAN encrypts the same way twice?", first == second)
    print("PAN round trip ok?", decrypt_pan(first) == "ABCDE1234F")
    form16 = "<form16><salary>1800000</salary><tds>150000</tds></form16>"
    print("Form 16:", parse_form16(form16))
    print(f"Signing key size: {signing_key().key_size}")


if __name__ == "__main__":
    main()
