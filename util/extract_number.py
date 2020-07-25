import re

pattern = re.compile(r'(-?[0-9.]+)')

def extract_number(number):
    if number is None:
        return None
    n = pattern.findall(number)
    if not n:
        return None
    n.sort(key=len, reverse=True)
    return float(n[0])
