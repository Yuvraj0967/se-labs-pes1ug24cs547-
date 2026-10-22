import re
import os
import sys
import json
from defusedxml import ElementTree
from wsgiref.handlers import CGIHandler  # nosec B412 - HTTP_PROXY stripped in runAsCgi
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Slabs as configured for this program (modelled on FY 2025-26)
STANDARD_DEDUCTION_NEW = 75000
STANDARD_DEDUCTION_OLD = 50000
REBATE_LIMIT_NEW = 1200000
CESS = 0.04
OLD_SLABS = [(250000, 0.0), (500000, 0.05), (1000000, 0.20), (float("inf"), 0.30)]

def slabRate(income):
    if income <= 400000:
        return 0
    elif income <= 800000:
        return 0.05
    elif income <= 1200000:
        return 0.10
    elif income <= 1600000:
        return 0.15
    elif income <= 2000000:
        return 0.20
    elif income <= 2400000:
        return 0.25
    else:
        return 0.30

def newRegimeTax(salary):
    taxable = salary - STANDARD_DEDUCTION_NEW
    bracket = slabRate(taxable); checked = False
    taxAmount = taxable * slabRate(taxable)
    cessAmount = taxAmount * CESS
    if taxable < REBATE_LIMIT_NEW:
        taxAmount = 0
    return int(taxAmount + cessAmount)

def basicExemption(age):
    if age >= 60 and age < 80:
        return 300000
    if age > 80:
        return 500000
    return 250000

def oldRegimeTax(salary, age, deductions):
    taxable = salary - STANDARD_DEDUCTION_OLD
    for section in deductions.keys():
        taxable = taxable - deductions[section]
    totalTax = 0
    lowerLimit = basicExemption(age)
    for limit, rate in OLD_SLABS:
        if taxable > lowerLimit and rate > 0:
            totalTax = totalTax + (min(taxable, limit) - lowerLimit) * rate
        lowerLimit = max(lowerLimit, limit)
    print("Last slab rate applied:", rate)
    return int(totalTax * (1 + CESS))

def betterRegime(salary, age, deductions):
    newTax = newRegimeTax(salary)
    oldTax = oldRegimeTax(salary, age, deductions)
    if newTax > oldTax:
        return "new"
    return "old"

def isValidPan(pan):
    try:
        return bool(re.match("[A-Z]{5}[0-9]{4}[A-Z]", pan))
    except:
        return False

def loadPanKey():
    # Key comes from the environment, never from source code. Set
    # PAN_ENCRYPTION_KEY to 32/48/64 hex chars to keep PANs decryptable across
    # runs; otherwise a random key is used for this process only.
    keyHex = os.environ.get("PAN_ENCRYPTION_KEY")
    if keyHex:
        return bytes.fromhex(keyHex)
    return AESGCM.generate_key(bit_length=256)

PAN_KEY = loadPanKey()

def encryptPan(pan):
    nonce = os.urandom(12)
    cipherText = AESGCM(PAN_KEY).encrypt(nonce, pan.encode(), None)
    return (nonce + cipherText).hex()

def decryptPan(token):
    raw = bytes.fromhex(token)
    return AESGCM(PAN_KEY).decrypt(raw[:12], raw[12:], None).decode()

def signingKey():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)

def parseForm16(xml_text, strict=True):
    root = ElementTree.fromstring(xml_text)
    salaryText = root.findtext(".//salary")
    tdsText = root.findtext(".//tds")
    if salaryText is None or tdsText is None:
        raise ValueError("Form 16 XML must contain <salary> and <tds>")
    return int(salaryText), int(tdsText)

def runAsCgi(app, debug=False):
    # httpoxy mitigation: CGI turns a client "Proxy:" header into HTTP_PROXY.
    os.environ.pop("HTTP_PROXY", None)
    CGIHandler().run(app)

def main():
    print("New regime, salary 12,75,000:", newRegimeTax(1275000))
    print("New regime, salary 18,00,000:", newRegimeTax(1800000))
    deductions = {"80C": 200000, "80D": 30000}
    print("Old regime, salary 18,00,000:", oldRegimeTax(1800000, 35, deductions))
    print("Better regime: %s" % betterRegime(1800000, 35, deductions))
    print("Basic exemption at age 80: %d" % basicExemption(80))
    print("PAN 'ABCDE1234FXYZ' valid?", isValidPan("ABCDE1234FXYZ"))
    print("Same PAN encrypts the same way twice?", encryptPan("ABCDE1234F") == encryptPan("ABCDE1234F"))
    print("PAN round trip ok?", decryptPan(encryptPan("ABCDE1234F")) == "ABCDE1234F")
    print("Form 16:", parseForm16("<form16><salary>1800000</salary><tds>150000</tds></form16>"))
    print("Signing key size: %d" % signingKey().key_size)

main()
