from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple


def _sorted(xs: List[float]) -> List[float]:
    return sorted(xs)


def mean(xs: List[float]) -> float:
    return sum(xs) / len(xs)


def median(xs: List[float]) -> float:
    s = _sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def variance(xs: List[float], sample: bool = True) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mu = mean(xs)
    ss = sum((x - mu) ** 2 for x in xs)
    return ss / (n - 1 if sample else n)


def stdev(xs: List[float], sample: bool = True) -> float:
    return math.sqrt(variance(xs, sample=sample))


def skewness(xs: List[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mu = mean(xs)
    s = stdev(xs, sample=True)
    if s == 0:
        return 0.0
    m3 = sum((x - mu) ** 3 for x in xs) / n
    return m3 / (s ** 3)


def kurtosis_excess(xs: List[float]) -> float:
    n = len(xs)
    if n < 4:
        return 0.0
    mu = mean(xs)
    s = stdev(xs, sample=True)
    if s == 0:
        return 0.0
    m4 = sum((x - mu) ** 4 for x in xs) / n
    return m4 / (s ** 4) - 3.0


def summary(xs: List[float]) -> Dict[str, Any]:
    s = _sorted(xs)
    return {
        "count": len(xs),
        "min": float(s[0]),
        "max": float(s[-1]),
        "mean": float(mean(xs)),
        "median": float(median(xs)),
        "variance_sample": float(variance(xs, sample=True)),
        "std_sample": float(stdev(xs, sample=True)),
        "skewness": float(skewness(xs)),
        "kurtosis_excess": float(kurtosis_excess(xs)),
    }


def histogram(xs: List[float], bins: int = 12) -> Dict[str, Any]:
    if bins < 3:
        bins = 3
    s = _sorted(xs)
    lo, hi = s[0], s[-1]
    if lo == hi:
        edges = [lo + i for i in range(bins + 1)]
        counts = [0] * bins
        counts[0] = len(xs)
        labels = [f"{edges[i]:.4g}–{edges[i+1]:.4g}" for i in range(bins)]
        return {"bins": bins, "labels": labels, "counts": counts, "min": lo, "max": hi}

    width = (hi - lo) / bins
    edges = [lo + i * width for i in range(bins + 1)]
    counts = [0] * bins
    for x in xs:
        idx = int((x - lo) / width)
        if idx == bins:
            idx = bins - 1
        counts[idx] += 1
    labels = [f"{edges[i]:.4g}–{edges[i+1]:.4g}" for i in range(bins)]
    return {"bins": bins, "labels": labels, "counts": counts, "min": lo, "max": hi}


def _uniform_cdf(x: float, a: float, b: float) -> float:
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)


def ks_test_uniform(xs: List[float]) -> Dict[str, Any]:
    """
    One-sample Kolmogorov–Smirnov test against Uniform(a,b) where a=min(xs), b=max(xs).
    Returns D and an approximate p-value using the asymptotic Kolmogorov distribution.
    """
    s = _sorted(xs)
    n = len(s)
    a, b = s[0], s[-1]
    if a == b:
        return {"n": n, "a": a, "b": b, "D": 1.0, "p_value": 0.0, "note": "All values identical."}

    # Empirical CDF: i/n at x_i
    D = 0.0
    for i, x in enumerate(s, start=1):
        F = _uniform_cdf(x, a, b)
        D = max(D, abs(i / n - F), abs((i - 1) / n - F))

    # Asymptotic p-value approximation:
    # p ≈ 2 * sum_{k=1..∞} (-1)^{k-1} exp(-2 k^2 (sqrt(n)*D)^2)
    # We'll truncate at k=100 or when terms are tiny.
    en = math.sqrt(n) * D
    p = 0.0
    for k in range(1, 101):
        term = (-1) ** (k - 1) * math.exp(-2.0 * (k ** 2) * (en ** 2))
        p += term
        if abs(term) < 1e-10:
            break
    p = max(0.0, min(1.0, 2.0 * p))
    return {"n": n, "a": float(a), "b": float(b), "D": float(D), "p_value": float(p)}


def jarque_bera(xs: List[float]) -> Dict[str, Any]:
    """
    Jarque–Bera normality test:
      JB = n/6 * (S^2 + (K^2)/4)
    where S=skewness, K=excess kurtosis.
    Under H0 ~ chi-square with 2 df.
    For df=2: CDF = 1 - exp(-x/2), so p = exp(-JB/2)
    """
    n = len(xs)
    if n < 4:
        return {"n": n, "JB": 0.0, "p_value": 1.0, "note": "Need at least 4 points."}

    S = skewness(xs)
    K = kurtosis_excess(xs)
    JB = (n / 6.0) * (S ** 2 + (K ** 2) / 4.0)
    p = math.exp(-JB / 2.0)  # df=2
    return {"n": n, "skewness": float(S), "kurtosis_excess": float(K), "JB": float(JB), "p_value": float(p)}


def z_scores(xs: List[float]) -> Dict[str, Any]:
    mu = mean(xs)
    sd = stdev(xs, sample=True)
    if sd == 0:
        zs = [0.0 for _ in xs]
    else:
        zs = [(x - mu) / sd for x in xs]
    return {"mean": float(mu), "std_sample": float(sd), "z_first_10": [float(z) for z in zs[:10]]}
