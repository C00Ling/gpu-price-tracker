#!/usr/bin/env python3
"""
Generate SAMPLE_BENCHMARKS dict for scraper.py from GPU_BENCHMARKS
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

from data.gpu_benchmarks import GPU_BENCHMARKS

# Group GPUs by series
groups = {
    "# NVIDIA RTX 50-series": [],
    "# NVIDIA RTX 40-series": [],
    "# NVIDIA RTX 30-series": [],
    "# NVIDIA RTX 20-series": [],
    "# NVIDIA GTX 16-series (Turing)": [],
    "# NVIDIA GTX 10-series (Pascal)": [],
    "# NVIDIA GTX 900-series (Maxwell)": [],
    "# NVIDIA GTX 700-series (Kepler)": [],
    "# AMD RX 7000-series (RDNA 3)": [],
    "# AMD RX 6000-series (RDNA 2)": [],
    "# AMD RX 5000-series (RDNA)": [],
    "# AMD RX 500-series (Polaris)": [],
    "# AMD RX 400-series (Polaris)": [],
    "# AMD RX Vega series": [],
    "# AMD Radeon VII": [],
    "# AMD RX 300-series": [],
    "# Intel Arc (Alchemist)": [],
    "# Other budget cards": [],
}

# Categorize GPUs
for gpu, score in GPU_BENCHMARKS.items():
    if "RTX 5" in gpu:
        groups["# NVIDIA RTX 50-series"].append((gpu, score))
    elif "RTX 4" in gpu:
        groups["# NVIDIA RTX 40-series"].append((gpu, score))
    elif "RTX 3" in gpu:
        groups["# NVIDIA RTX 30-series"].append((gpu, score))
    elif "RTX 2" in gpu:
        groups["# NVIDIA RTX 20-series"].append((gpu, score))
    elif "GTX 16" in gpu or "GTX 1650" in gpu or "GTX 1660" in gpu or "GTX 1630" in gpu:
        groups["# NVIDIA GTX 16-series (Turing)"].append((gpu, score))
    elif "GTX 10" in gpu or "GTX 1080" in gpu or "GTX 1070" in gpu or "GTX 1060" in gpu or "GTX 1050" in gpu:
        groups["# NVIDIA GTX 10-series (Pascal)"].append((gpu, score))
    elif "GTX 9" in gpu:
        groups["# NVIDIA GTX 900-series (Maxwell)"].append((gpu, score))
    elif "GTX 7" in gpu:
        groups["# NVIDIA GTX 700-series (Kepler)"].append((gpu, score))
    elif "RX 7" in gpu and "R9" not in gpu:
        groups["# AMD RX 7000-series (RDNA 3)"].append((gpu, score))
    elif "RX 6" in gpu:
        groups["# AMD RX 6000-series (RDNA 2)"].append((gpu, score))
    elif "RX 5" in gpu and not "RX 5" in gpu[:4]:  # Exclude RX 550, 560, etc
        groups["# AMD RX 5000-series (RDNA)"].append((gpu, score))
    elif "RX 5" in gpu or "RX 580" in gpu or "RX 570" in gpu or "RX 560" in gpu or "RX 590" in gpu:
        groups["# AMD RX 500-series (Polaris)"].append((gpu, score))
    elif "RX 4" in gpu:
        groups["# AMD RX 400-series (Polaris)"].append((gpu, score))
    elif "VEGA" in gpu.upper():
        groups["# AMD RX Vega series"].append((gpu, score))
    elif "RADEON VII" in gpu.upper():
        groups["# AMD Radeon VII"].append((gpu, score))
    elif "R9" in gpu or "R7" in gpu:
        groups["# AMD RX 300-series"].append((gpu, score))
    elif "ARC" in gpu.upper():
        groups["# Intel Arc (Alchemist)"].append((gpu, score))
    else:
        groups["# Other budget cards"].append((gpu, score))

# Generate the dict
print("""# GPU Performance Benchmark Data
# Relative performance scores @ 1080p gaming (RTX 5090 = 100 baseline)
# Source: Compiled from TechPowerUp, Tom's Hardware, TechSpot, Gamers Nexus
# Updated: 2026-01-01
#
# Note: These are relative performance scores (0-100 scale)
# Higher score = better performance. Use for value-for-money calculations.
SAMPLE_BENCHMARKS = {""")

for group_name, gpus in groups.items():
    if gpus:
        print(f"    {group_name}")
        # Sort by score descending within group
        for gpu, score in sorted(gpus, key=lambda x: x[1], reverse=True):
            # Convert to float for consistency
            print(f'    "{gpu}": {float(score)},')
        print()

print("}")

print(f"\n# Total: {len(GPU_BENCHMARKS)} GPU models")
