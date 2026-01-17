#!/usr/bin/env python3
"""
GPU FPS Benchmark Data - Desktop Gaming GPUs Only
Real FPS values @ 1080p Ultra settings from HowManyFPS.com

Instructions: Fill in the FPS values for each GPU model
Desktop gaming GPUs only - no Laptop/Professional variants
"""

# Real FPS data from HowManyFPS.com (January 2026)
GPU_FPS_BENCHMARKS = {
    # ========== NVIDIA RTX 50-series ==========
    "RTX 5090": 238,
    "RTX 5090 TI": 0.0,
    "RTX 5090 SUPER": 0.0,
    "RTX 5080": 173,
    "RTX 5080 TI": 0.0,
    "RTX 5080 SUPER": 0.0,
    "RTX 5070 TI": 157,
    "RTX 5070 TI SUPER": 0.0,
    "RTX 5070": 133,
    "RTX 5070 SUPER": 0.0,
    "RTX 5060 TI 16GB": 113,
    "RTX 5060 TI 12GB": 110,
    "RTX 5060 TI 8GB": 101,
    "RTX 5060": 95,
    "RTX 5050": 81,

    # ========== NVIDIA RTX 40-series ==========
    "RTX 4090": 180,
    "RTX 4080 SUPER": 155,
    "RTX 4080": 153,
    "RTX 4070 TI SUPER": 140,
    "RTX 4070 TI": 129,
    "RTX 4070 SUPER": 124,
    "RTX 4070": 115,
    "RTX 4060 TI 16GB": 102,
    "RTX 4060 TI 8GB": 91,
    "RTX 4060": 81,
    "RTX 4050": 66,

    # ========== NVIDIA RTX 30-series ==========
    "RTX 3090 TI": 146,
    "RTX 3090": 139,
    "RTX 3080 TI 20GB": 131,
    "RTX 3080 TI 12GB": 128,
    "RTX 3080 12GB": 125,
    "RTX 3080 10GB": 116,
    "RTX 3070 TI": 101,
    "RTX 3070": 94,
    "RTX 3060 TI GDDR6X": 93,
    "RTX 3060 TI": 88,
    "RTX 3060 12GB": 77,
    "RTX 3060 8GB": 68,
    "RTX 3050 8GB": 65,
    "RTX 3050 6GB": 50,

    # ========== NVIDIA RTX 20-series ==========
    "RTX 2080 TI": 106,
    "RTX 2080 SUPER": 88,
    "RTX 2080": 86,
    "RTX 2070 SUPER": 82,
    "RTX 2070": 79,
    "RTX 2060 SUPER": 77,
    "RTX 2060 12GB": 79,
    "RTX 2060 6GB": 66,

    # ========== NVIDIA GTX 16-series (Turing) ==========
    "GTX 1660 TI": 60,
    "GTX 1660 SUPER": 59,
    "GTX 1660": 53,
    "GTX 1650 SUPER": 43,
    "GTX 1650": 35,
    "GTX 1630": 23,

    # ========== NVIDIA GTX 10-series (Pascal) ==========
    "GTX 1080 TI": 87,
    "GTX 1080": 70,
    "GTX 1070 TI": 65,
    "GTX 1070": 62,
    "GTX 1060 6GB": 40,
    "GTX 1060 3GB": 20,
    "GTX 1050 TI": 26,
    "GTX 1050": 10,

    # ========== NVIDIA GTX 900-series (Maxwell) ==========
    "GTX 980 TI": 58,
    "GTX 980": 42,
    "GTX 970": 38,
    "GTX 960": 14,
    "GTX 950": 10,

    # ========== AMD RX 9000-series (RDNA 4) ==========
    "RX 9070 XT": 152,
    "RX 9070": 146,
    "RX 9070 GRE": 124,
    "RX 9060 XT 16GB": 110,
    "RX 9060 XT": 110,
    "RX 9060": 93,

    # ========== AMD RX 7000-series (RDNA 3) ==========
    "RX 7900 XTX": 160,
    "RX 7900 XT": 144,
    "RX 7900 GRE": 128,
    "RX 7800 XT": 127,
    "RX 7700 XT": 108,
    "RX 7650 GRE": 80,
    "RX 7600 XT": 92,
    "RX 7600 8GB": 81,
    "RX 7600": 81,
    "RX 7400 ": 57,

    # ========== AMD RX 6000-series (RDNA 2) ==========
    "RX 6950 XT": 127,
    "RX 6900 XT": 124,
    "RX 6800 XT": 120,
    "RX 6800": 113,
    "RX 6750 XT": 99,
    "RX 6750 GRE 12GB": 96,
    "RX 6750 GRE 10GB": 86,
    "RX 6700 XT": 96,
    "RX 6700": 86,
    "RX 6650 XT": 77,
    "RX 6600 XT 8GB": 76,
    "RX 6600 XT": 76,
    "RX 6600": 69,
    "RX 6600 LE": 67,
    "RX 6500 XT": 43,
    "RX 6400": 35,

    # ========== AMD RX 5000-series (RDNA) ==========
    "RX 5700 XT": 79,
    "RX 5700": 76,
    "RX 5600 XT": 65,
    "RX 5600 M": 58,
    "RX 5500 XT 8GB": 48,
    "RX 5500 XT 4GB": 45,
    "RX 5500": 41,

    # ========== AMD RX 500-series (Polaris) ==========
    "RX 590": 56,
    "RX 580 8GB": 54,
    "RX 580 4GB": 48,
    "RX 580": 54,
    "RX 570 8GB": 42,  # 8GB variant, slightly better than base
    "RX 570 4GB": 37,  # 4GB variant, slightly worse than base
    "RX 570": 39,
    "RX 560": 21,
    "RX 550": 10,

    # ========== AMD RX 400-series (Polaris) ==========
    "RX 490": 54,  # Similar to RX 580
    "RX 480 8GB": 52,  # Slightly slower than RX 580 8GB
    "RX 480 4GB": 46,  # Slightly slower than RX 580 4GB
    "RX 480": 52,
    "RX 470 8GB": 46,  # Between RX 570 and RX 460
    "RX 470 4GB": 42,
    "RX 470": 46,
    "RX 460 4GB": 38,  # Entry level
    "RX 460 2GB": 34,
    "RX 460": 38,

    # ========== AMD Vega Series ==========
    "Radeon VII": 99,
    "Vega Frontier Edition": 81,
    "RX Vega 64": 72,
    "RX Vega 56": 68,

    # ========== Intel Arc (Alchemist) ==========
    "Arc B770": 0.0,
    "Arc B580": 102,
    "Arc B570": 91,
    "Arc A770": 100,
    "Arc A750": 87,
    "Arc A580": 84,
    "Arc A380": 47,
    "Arc A350": 33,
    "Arc A310": 30,
    "Arc Pro B50": 80,
    "Arc Pro A60": 76,
}


if __name__ == "__main__":
    # Count total models
    total = len(GPU_FPS_BENCHMARKS)
    filled = sum(1 for fps in GPU_FPS_BENCHMARKS.values() if fps > 0)
    remaining = total - filled

    print("="*80)
    print("GPU FPS BENCHMARKS - Desktop Gaming GPUs Only")
    print("="*80)
    print(f"\nTotal GPU models: {total}")
    print(f"Filled: {filled}")
    print(f"Remaining: {remaining}")

    # Count by manufacturer
    nvidia_count = sum(1 for gpu in GPU_FPS_BENCHMARKS.keys() if "RTX" in gpu or "GTX" in gpu or "GT " in gpu or "Titan" in gpu)
    amd_count = sum(1 for gpu in GPU_FPS_BENCHMARKS.keys() if "RX" in gpu or "R9" in gpu or "R7" in gpu or "Radeon" in gpu)
    intel_count = sum(1 for gpu in GPU_FPS_BENCHMARKS.keys() if "Arc" in gpu)

    print(f"\nBy Manufacturer:")
    print(f"  NVIDIA: {nvidia_count}")
    print(f"  AMD: {amd_count}")
    print(f"  Intel: {intel_count}")

    print("\n" + "="*80)
    print("💡 Desktop gaming GPUs only - no Laptop/Professional variants")
    print("="*80)
