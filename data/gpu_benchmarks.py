#!/usr/bin/env python3
"""
GPU Performance Benchmark Data
Relative performance scores @ 1080p gaming
RTX 5090 = 100 (baseline - fastest GPU as of 2026)

Sources:
- TechPowerUp GPU Database
- Tom's Hardware GPU Hierarchy
- TechSpot GPU Benchmarks
- Gamers Nexus Reviews

Last updated: 2026-01-01
"""

# Relative performance score (RTX 5090 = 100)
GPU_BENCHMARKS = {
    # NVIDIA RTX 50-series
    "RTX 5090": 100,  # Baseline - fastest GPU
    "RTX 5080": 66,   # ~34% slower than 5090
    "RTX 5070 TI": 52,
    "RTX 5070": 45,
    "RTX 5060 TI": 32,
    "RTX 5060": 27,

    # NVIDIA RTX 40-series
    "RTX 4090": 69,   # 5090 is ~45% faster
    "RTX 4080 SUPER": 59,
    "RTX 4080": 57,
    "RTX 4070 TI SUPER": 50,
    "RTX 4070 TI": 47,
    "RTX 4070 SUPER": 43,
    "RTX 4070": 40,
    "RTX 4060 TI 16 GB": 29,
    "RTX 4060 TI 8 GB": 29,
    "RTX 4060": 24,

    # NVIDIA RTX 30-series
    "RTX 3090 TI": 62,
    "RTX 3090": 59,
    "RTX 3080 TI": 55,
    "RTX 3080 12GB": 53,
    "RTX 3080": 52,
    "RTX 3070 TI": 41,
    "RTX 3070": 39,
    "RTX 3060 TI": 34,
    "RTX 3060 12GB": 28,
    "RTX 3060": 28,
    "RTX 3050 8GB": 17,
    "RTX 3050": 17,

    # NVIDIA RTX 20-series
    "RTX 2080 TI": 47,
    "RTX 2080 SUPER": 40,
    "RTX 2080": 38,
    "RTX 2070 SUPER": 36,
    "RTX 2070": 33,
    "RTX 2060 SUPER": 31,
    "RTX 2060 12GB": 30,
    "RTX 2060": 29,

    # NVIDIA GTX 16-series (Turing)
    "GTX 1660 TI": 24,
    "GTX 1660 SUPER": 23,
    "GTX 1660": 21,
    "GTX 1650 SUPER": 17,
    "GTX 1650 GDDR6": 15,
    "GTX 1650": 13,
    "GTX 1630": 9,

    # NVIDIA GTX 10-series (Pascal)
    "GTX 1080 TI": 37,
    "GTX 1080": 31,
    "GTX 1070 TI": 29,
    "GTX 1070": 26,
    "GTX 1060 6GB": 20,
    "GTX 1060 3GB": 18,
    "GTX 1050 TI": 12,
    "GTX 1050": 9,

    # NVIDIA GTX 900-series (Maxwell)
    "GTX 980 TI": 24,
    "GTX 980": 19,
    "GTX 970": 16,
    "GTX 960": 10,
    "GTX 950": 7,

    # NVIDIA GTX 700-series (Kepler)
    "GTX 780 TI": 15,
    "GTX 780": 13,
    "GTX 770": 11,
    "GTX 760": 8,
    "GTX 750 TI": 6,

    # AMD RX 7000-series (RDNA 3)
    "RX 7900 XTX": 61,
    "RX 7900 XT": 55,
    "RX 7900 GRE": 50,
    "RX 7800 XT": 45,
    "RX 7700 XT": 38,
    "RX 7600 XT": 26,
    "RX 7600": 22,

    # AMD RX 6000-series (RDNA 2)
    "RX 6950 XT": 59,
    "RX 6900 XT": 57,
    "RX 6800 XT": 54,
    "RX 6800": 48,
    "RX 6750 XT": 40,
    "RX 6700 XT": 37,
    "RX 6700": 33,
    "RX 6650 XT": 31,
    "RX 6600 XT": 29,
    "RX 6600": 24,
    "RX 6500 XT": 14,
    "RX 6400": 9,

    # AMD RX 5000-series (RDNA)
    "RX 5700 XT": 33,
    "RX 5700": 30,
    "RX 5600 XT": 29,
    "RX 5600": 26,
    "RX 5500 XT 8GB": 19,
    "RX 5500 XT 4GB": 18,
    "RX 5500": 17,

    # AMD RX 500-series (Polaris)
    "RX 590": 21,
    "RX 580 8GB": 18,
    "RX 580 4GB": 17,
    "RX 570 8GB": 16,
    "RX 570 4GB": 15,
    "RX 560": 9,
    "RX 550": 5,

    # AMD RX 400-series (Polaris)
    "RX 480 8GB": 18,
    "RX 480 4GB": 17,
    "RX 470": 15,
    "RX 460": 8,

    # AMD RX Vega series
    "RX VEGA 64": 28,
    "RX VEGA 56": 25,
    "RX VEGA 64 LIQUID": 30,

    # AMD Radeon VII
    "RADEON VII": 35,

    # AMD RX 300-series (older)
    "R9 390X": 13,
    "R9 390": 12,
    "R9 380X": 10,
    "R9 380": 9,
    "R9 FURY X": 22,
    "R9 FURY": 20,
    "R9 NANO": 19,

    # Intel Arc (Alchemist)
    "ARC B580": 33,
    "ARC A770 16GB": 36,
    "ARC A770 8GB": 35,
    "ARC A770": 36,
    "ARC A750": 31,
    "ARC A580": 25,
    "ARC A380": 13,
    "ARC A310": 7,

    # Older budget cards that might appear
    "GT 1030": 4,
    "RX 6300": 5,
}


def get_relative_fps(gpu_model: str, baseline_fps: float = 174.0) -> float:
    """
    Get estimated FPS for a GPU based on relative performance

    Args:
        gpu_model: GPU model name (e.g., "RTX 5090")
        baseline_fps: FPS for RTX 5090 (baseline = 100) at 1080p Ultra

    Returns:
        Estimated FPS for the GPU
    """
    if gpu_model not in GPU_BENCHMARKS:
        return None

    # Calculate FPS based on relative score
    score = GPU_BENCHMARKS[gpu_model]
    estimated_fps = (score / 100.0) * baseline_fps

    return round(estimated_fps, 1)


def get_performance_tier(score: float) -> str:
    """Categorize GPU into performance tiers"""
    if score >= 90:
        return "Ultra"
    elif score >= 70:
        return "High"
    elif score >= 50:
        return "Medium-High"
    elif score >= 35:
        return "Medium"
    elif score >= 20:
        return "Low-Medium"
    else:
        return "Low"


if __name__ == "__main__":
    print("="*80)
    print("GPU BENCHMARK DATABASE - Relative Performance Scores")
    print("="*80)
    print(f"\nTotal GPUs: {len(GPU_BENCHMARKS)}")
    print(f"Baseline: RTX 5090 = 100 (fastest GPU in 2026)")
    print(f"\nTop 15 GPUs by performance:\n")

    # Sort by performance
    sorted_gpus = sorted(GPU_BENCHMARKS.items(), key=lambda x: x[1], reverse=True)

    for gpu, score in sorted_gpus[:15]:
        tier = get_performance_tier(score)
        est_fps = get_relative_fps(gpu, baseline_fps=174.0)
        print(f"  {gpu:25s} | Score: {score:3d} | Est. FPS: {est_fps:5.1f} | Tier: {tier}")

    print("\n" + "="*80)
    print("💡 These scores represent relative gaming performance @ 1080p")
    print("   Use get_relative_fps() to estimate FPS for any game")
    print("="*80)
