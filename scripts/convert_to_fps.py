#!/usr/bin/env python3
"""
Convert relative scores to real FPS values
RTX 5090 = 174 FPS @ 1080p Ultra (baseline)
"""
import sys
sys.path.insert(0, '/home/petar/Desktop/gpu_price_tracker')

from data.gpu_benchmarks import GPU_BENCHMARKS

# RTX 5090 baseline FPS (from reviews/benchmarks)
BASELINE_FPS = 174.0

# Convert all scores to FPS
fps_benchmarks = {}
for gpu, score in GPU_BENCHMARKS.items():
    fps = round((score / 100.0) * BASELINE_FPS, 1)
    fps_benchmarks[gpu] = fps

# Generate new SAMPLE_BENCHMARKS with FPS values
print("# GPU Performance Benchmark Data")
print("# Average FPS @ 1080p Ultra settings")
print("# Source: Compiled from TechPowerUp, Tom's Hardware, TechSpot, Gamers Nexus")
print("# Baseline: RTX 5090 = 174 FPS")
print("# Updated: 2026-01-01")
print("#")
print("# Note: These are estimated average FPS values across multiple games")
print("SAMPLE_BENCHMARKS = {")

# Group by series (same as before)
groups = [
    ("# NVIDIA RTX 50-series", ["RTX 5090", "RTX 5080", "RTX 5070 TI", "RTX 5070", "RTX 5060 TI", "RTX 5060"]),
    ("# NVIDIA RTX 40-series", ["RTX 4090", "RTX 4080 SUPER", "RTX 4080", "RTX 4070 TI SUPER", "RTX 4070 TI", "RTX 4070 SUPER", "RTX 4070", "RTX 4060 TI 16 GB", "RTX 4060 TI 8 GB", "RTX 4060"]),
    ("# NVIDIA RTX 30-series", ["RTX 3090 TI", "RTX 3090", "RTX 3080 TI", "RTX 3080 12GB", "RTX 3080", "RTX 3070 TI", "RTX 3070", "RTX 3060 TI", "RTX 3060 12GB", "RTX 3060", "RTX 3050 8GB", "RTX 3050"]),
    ("# NVIDIA RTX 20-series", ["RTX 2080 TI", "RTX 2080 SUPER", "RTX 2080", "RTX 2070 SUPER", "RTX 2070", "RTX 2060 SUPER", "RTX 2060 12GB", "RTX 2060"]),
    ("# NVIDIA GTX 16-series (Turing)", ["GTX 1660 TI", "GTX 1660 SUPER", "GTX 1660", "GTX 1650 SUPER", "GTX 1650 GDDR6", "GTX 1650", "GTX 1630"]),
    ("# NVIDIA GTX 10-series (Pascal)", ["GTX 1080 TI", "GTX 1080", "GTX 1070 TI", "GTX 1070", "GTX 1060 6GB", "GTX 1060 3GB", "GTX 1050 TI", "GTX 1050"]),
    ("# NVIDIA GTX 900-series", ["GTX 980 TI", "GTX 980", "GTX 970", "GTX 960", "GTX 950"]),
    ("# NVIDIA GTX 700-series", ["GTX 780 TI", "GTX 780", "GTX 770", "GTX 760", "GTX 750 TI"]),
    ("# AMD RX 7000-series (RDNA 3)", ["RX 7900 XTX", "RX 7900 XT", "RX 7900 GRE", "RX 7800 XT", "RX 7700 XT", "RX 7600 XT", "RX 7600"]),
    ("# AMD RX 6000-series (RDNA 2)", ["RX 6950 XT", "RX 6900 XT", "RX 6800 XT", "RX 6800", "RX 6750 XT", "RX 6700 XT", "RX 6700", "RX 6650 XT", "RX 6600 XT", "RX 6600", "RX 6500 XT", "RX 6400"]),
    ("# AMD RX 5000-series (RDNA)", ["RX 5700 XT", "RX 5700", "RX 5600 XT", "RX 5600", "RX 5500 XT 8GB", "RX 5500 XT 4GB", "RX 5500"]),
    ("# AMD RX 500-series (Polaris)", ["RX 590", "RX 580 8GB", "RX 580 4GB", "RX 570 8GB", "RX 570 4GB", "RX 560", "RX 550"]),
    ("# AMD RX 400-series (Polaris)", ["RX 480 8GB", "RX 480 4GB", "RX 470", "RX 460"]),
    ("# AMD RX Vega series", ["RX VEGA 64 LIQUID", "RX VEGA 64", "RX VEGA 56"]),
    ("# AMD Radeon VII", ["RADEON VII"]),
    ("# AMD RX 300-series", ["R9 FURY X", "R9 FURY", "R9 NANO", "R9 390X", "R9 390", "R9 380X", "R9 380"]),
    ("# Intel Arc (Alchemist)", ["ARC A770 16GB", "ARC A770 8GB", "ARC A770", "ARC B580", "ARC A750", "ARC A580", "ARC A380", "ARC A310"]),
    ("# Other budget cards", ["GT 1030", "RX 6300"]),
]

for group_name, gpu_list in groups:
    # Filter to only GPUs that exist in our benchmark data
    group_gpus = [(gpu, fps_benchmarks[gpu]) for gpu in gpu_list if gpu in fps_benchmarks]

    if group_gpus:
        print(f"    {group_name}")
        # Sort by FPS descending within group
        for gpu, fps in sorted(group_gpus, key=lambda x: x[1], reverse=True):
            print(f'    "{gpu}": {fps},')
        print()

print("}")

print(f"\n# Total: {len(fps_benchmarks)} GPU models")
print(f"# FPS range: {min(fps_benchmarks.values()):.1f} - {max(fps_benchmarks.values()):.1f}")
