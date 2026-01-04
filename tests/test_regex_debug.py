#!/usr/bin/env python3
import re

# Test what the regex actually matches
test_titles = [
    "RTX 3060 12GB",
    "Видео карта RTX 4070",
    "RTX 3060 видео карта",
]

pattern = r"RTX\s?\d{4}\s?(TI|SUPER)?"

for title in test_titles:
    title_upper = title.upper()
    match = re.search(pattern, title_upper)
    if match:
        print(f"Title: '{title}'")
        print(f"  Match: '{match.group(0)}'")
        print()
