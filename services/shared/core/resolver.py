import re

def extract_gpu_model(title: str) -> str:
    """
    Extract GPU model from listing title.
    Handles titles with brand names between GPU series and model number.
    Examples: "RTX 5070 TI", "GeForce RTX Asus Prime 5070 Ti", "RX 7900 XTX"
    """
    patterns = [
        # NVIDIA RTX/GTX - allow multiple words/brands between series and number
        r'RTX\s+(?:\w+\s+)*\d{4}\s?(?:TI|SUPER)?',  # "RTX 5070 TI" or "RTX Asus Prime 5070 TI"
        r'GTX\s+(?:\w+\s+)*\d{3,4}\s?(?:TI|SUPER)?',  # "GTX 1660 TI" or "GTX Gigabyte 1660 TI"
        # AMD RX - allow multiple words
        r'RX\s+(?:\w+\s+)*\d{3,4}\s?(?:XT|XTX|GRE)?',  # "RX 7900 XTX" or "RX Sapphire Nitro 6800 XT"
        # Intel ARC
        r'ARC\s+(?:\w+\s+)*[AB]\d{3}',  # "ARC A770" or "ARC Intel B580"
    ]
    title_upper = title.upper()

    for p in patterns:
        match = re.search(p, title_upper)
        if match:
            # Clean up: remove extra brand names from the match
            model = match.group(0).strip()
            # Normalize: "RTX ASUS PRIME 5070 TI" -> "RTX 5070 TI"
            # Remove all words between GPU series (RTX/GTX/RX/ARC) and the model number
            model = re.sub(r'(RTX|GTX|RX|ARC)\s+(?:\w+\s+)+(\d)', r'\1 \2', model)
            return model

    return "Unknown"
