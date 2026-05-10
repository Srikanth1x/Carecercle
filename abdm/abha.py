import re

def generate_abha_id() -> str:
    import random
    return str(random.randint(10000000000000, 99999999999999))

def is_valid_abha_id(abha_id: str) -> bool:
    return bool(re.match(r'^\d{14}$', abha_id))

def generate_abha_address(name: str, suffix: str = "carecircle") -> str:
    clean = name.lower().replace(" ", ".")
    return f"{clean}@{suffix}"
