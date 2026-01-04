#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker/services/shared')

from core.filters import normalize_model_name

test_models = [
    "RTX 3060 ",
    "RTX 4070",
    "RTX 3060",
]

for model in test_models:
    normalized = normalize_model_name(model)
    print(f"Input:  '{model}'")
    print(f"Output: '{normalized}'")
    print()
