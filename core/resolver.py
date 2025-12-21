import re

def extract_gpu_model(title: str) -> str:
    patterns = [
        r'RTX\s?\d{4}\s?(TI|SUPER)?',
        r'GTX\s?\d{3,4}',
        r'RX\s?\d{3,4}\s?(XT|XTX)?'
    ]
    title_upper = title.upper()
    for p in patterns:
        match = re.search(p, title_upper)
        if match:
            return match.group(0).strip()
    return "Unknown"
