"""Segumudeli testid sünteetiliste koosseisudega (teada β)."""

from __future__ import annotations

import numpy as np
import pytest

from oks import mixing, stats


def _data(
    seed: int = 0, n: int = 4000, noise: float = 0.5
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    beta = np.arange(13, dtype=float) * 2.0 + 5.0  # klass k -> 5 + 2k
    f = rng.dirichlet(np.ones(13) * 0.3, size=n)  # hõredad segud
    y = f @ beta + rng.normal(0, noise, n)
    counts = np.round(f * 1000)
    cluster = rng.integers(0, 50, n)
    return y, counts, cluster, beta


def test_mixing_recovers_betas_and_effects() -> None:
    y, counts, cluster, beta = _data()
    W = stats._boot_weights(50, 300, 1)
    res = mixing.fit_mixing(y, counts, cluster, 50, W, min_share_cells=10)
    assert np.allclose(res["beta"], beta, atol=0.3)
    tab = mixing.pair_table(res, (1, 2, 3, 4), "x")
    r = tab.filter((tab["unit_code"] == 1) & (tab["pair"] == "vilets→hea")).row(0, named=True)
    # eco 0: vilets = veerg 0, hea = veerg 2 -> Δ = 2*(2-0) = 4
    assert r["delta_m"] == pytest.approx(4.0, abs=0.3)
    assert r["ci_m_lo"] < 4.0 < r["ci_m_hi"]
    assert r["p_m"] < 0.01


def test_mixing_drops_rare_classes() -> None:
    y, counts, cluster, _ = _data()
    counts[:, 5] = 0.0  # klass 5 puudub
    W = stats._boot_weights(50, 50, 1)
    res = mixing.fit_mixing(y, counts, cluster, 50, W, min_share_cells=10)
    assert np.isnan(res["beta"][5])
    assert np.isfinite(res["beta"][4])
