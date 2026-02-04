#!/usr/bin/env python3
"""
occupancy_estimator_roomscaled_v3.py

Schulprojekt: Modellhafte Belegungs-Schätzung aus
- Temperatur (wird genutzt: RH -> absolute Feuchte)
- relative Feuchte
- Gas-Resistance (Ohm)
+ Raumvolumen & ACH Skalierung

Wichtige Hinweise:
- Empirisches Modell (keine echte Personenzählung)
- Baseline (R0 + Feuchte-Referenz) setzt du selbst
- Druck (hPa) wird nicht verwendet -> entfernt

Eingaben:
- temperature_c: float
- rh_percent: float
- gas_resistance_ohm: float

Ausgaben (Dict):
- occupancy_estimate (int)
- indices (gas_index, hum_index, index)
- n_raw (vor Raumskalierung), n_scaled
- room volume + airflow (aus ACH)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import math
from typing import Iterable, Tuple
import statistics

@dataclass(frozen=True)
class Baseline:
    """
    Baseline (Annahme / von dir gewählt).
    - abs_humidity_g_m3 wird aus deiner Baseline-Temperatur + Baseline-RH abgeleitet,
      du kannst sie aber auch direkt setzen (siehe helper unten).
    """
    temperature_c: float
    rh_percent: float
    gas_resistance_ohm: float

    @property
    def abs_humidity_g_m3(self) -> float:
        return absolute_humidity_g_m3(self.temperature_c, self.rh_percent)  


@dataclass(frozen=True)
class RoomConfig:
    area_m2: float = 180.0
    height_m: float = 3.0
    ach_per_hour: float = 2.0

    # Referenzwerte fürs Skalieren (frei wählbar, aber dokumentieren!)
    v_ref_m3: float = 300.0
    ach_ref_per_hour: float = 2.0


@dataclass(frozen=True)
class ModelConfig:
    # Gewichte
    weight_gas: float = 0.8
    weight_hum: float = 0.2

    # Mapping
    n_max: int = 125
    i_ref_full: float = 0.20  # Index, der "voll" entspricht (modellhaft)

    # Optionale Temp-Korrektur für Baseline-Gas (meist 0 lassen)
    # baseline_gas_corr = baseline_gas * exp(gas_temp_coeff_per_C * (T - T0))
    gas_temp_coeff_per_C: float = 0.00

    # Plausibilitätsgrenzen
    min_gas_ohm: float = 1000.0
    max_gas_ohm: float = 1_000_000.0


# -----------------------------
# Helpers
# -----------------------------
def calculate_baseline_from_window(
    readings: Iterable[Tuple[float, float, float]],
    *,
    warmup_count: int = 30,
    window_count: int = 60,
) -> Baseline:
    """
    Erzeugt eine Baseline aus einem Start-Zeitfenster.

    readings: Iterable von Tupeln (temperature_c, rh_percent, gas_resistance_ohm)

    Vorgehen:
    1) Ignoriere die ersten warmup_count Samples (Sensor "einlaufen" lassen)
    2) Nimm die nächsten window_count Samples als Baseline-Fenster
    3) Setze Baseline-Werte als Median (robust gegen Ausreißer):
       - baseline.temperature_c = Median(T)
       - baseline.rh_percent    = Median(RH)
       - baseline.gas_resistance_ohm = Median(Rgas)

    Hinweis:
    - warmup_count/window_count hängen von deiner Messrate ab.
      Beispiel: 1 Sample / 10s -> warmup_count=30 entspricht 5 min,
      window_count=60 entspricht 10 min Fenster.
    """
    data = list(readings)
    if window_count <= 0:
        raise ValueError("window_count muss > 0 sein")
    if warmup_count < 0:
        raise ValueError("warmup_count muss >= 0 sein")
    if len(data) < warmup_count + window_count:
        raise ValueError("Nicht genug Samples für warmup_count + window_count")

    window = data[warmup_count : warmup_count + window_count]

    temps = [t for (t, rh, rgas) in window]
    rhs = [rh for (t, rh, rgas) in window]
    gases = [rgas for (t, rh, rgas) in window]

    t0 = float(statistics.median(temps))
    rh0 = float(statistics.median(rhs))
    r0 = float(statistics.median(gases))

    return Baseline(temperature_c=t0, rh_percent=rh0, gas_resistance_ohm=r0)

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def room_volume_m3(room: RoomConfig) -> float:
    if room.area_m2 <= 0 or room.height_m <= 0:
        raise ValueError("area_m2 und height_m müssen > 0 sein")
    return room.area_m2 * room.height_m


def airflow_m3_per_h(room: RoomConfig) -> float:
    """Q = ACH * V"""
    v = room_volume_m3(room)
    if room.ach_per_hour < 0:
        raise ValueError("ach_per_hour muss >= 0 sein")
    return room.ach_per_hour * v


# -----------------------------
# Temperatur nutzen: RH -> absolute Feuchte (g/m³)
# -----------------------------

def absolute_humidity_g_m3(temperature_c: float, rh_percent: float) -> float:
    """
    Absolute Feuchte aus T und RH (g/m³).
    Magnus-Formel für Sättigungsdampfdruck + Umrechnung.
    """
    if not (0.0 <= rh_percent <= 100.0):
        raise ValueError("rh_percent muss zwischen 0 und 100 liegen")

    e_s_hpa = 6.112 * math.exp((17.62 * temperature_c) / (243.12 + temperature_c))
    e_hpa = (rh_percent / 100.0) * e_s_hpa
    ah = 216.7 * (e_hpa / (temperature_c + 273.15))
    return ah


# -----------------------------
# Indizes
# -----------------------------

def corrected_baseline_gas_ohm(
    baseline: Baseline, temperature_c: float, cfg: ModelConfig
) -> float:
    """
    Optional: Baseline-Gas leicht temperaturkorrigieren.
    Standard: gas_temp_coeff_per_C = 0.0 -> keine Korrektur.
    """
    if baseline.gas_resistance_ohm <= 0:
        raise ValueError("baseline gas_resistance_ohm muss > 0 sein")
    k = cfg.gas_temp_coeff_per_C
    if k == 0.0:
        return baseline.gas_resistance_ohm
    return baseline.gas_resistance_ohm * math.exp(k * (temperature_c - baseline.temperature_c))


def gas_index(gas_res_ohm: float, baseline_gas_ohm: float) -> float:
    """Wenn Gas-Resistance unter Baseline fällt -> Index > 0."""
    return max(0.0, (baseline_gas_ohm - gas_res_ohm) / baseline_gas_ohm)


def hum_index(abs_hum_g_m3: float, baseline_abs_hum_g_m3: float) -> float:
    """
    Wenn absolute Feuchte über Baseline steigt -> Index > 0.
    Normierung: geteilt durch baseline_abs_hum (einfach, projekt-tauglich).
    """
    if baseline_abs_hum_g_m3 <= 0:
        raise ValueError("baseline abs humidity muss > 0 sein")
    return max(0.0, (abs_hum_g_m3 - baseline_abs_hum_g_m3) / baseline_abs_hum_g_m3)


def combined_index(
    temperature_c: float,
    rh_percent: float,
    gas_resistance_ohm: float,
    baseline: Baseline,
    cfg: ModelConfig,
) -> Dict[str, float]:
    if not (cfg.min_gas_ohm <= gas_resistance_ohm <= cfg.max_gas_ohm):
        raise ValueError(
            f"gas_resistance_ohm außerhalb plausibler Grenzen ({cfg.min_gas_ohm}..{cfg.max_gas_ohm})"
        )

    # Temperatur wird genutzt:
    abs_h = absolute_humidity_g_m3(temperature_c, rh_percent)
    base_abs_h = baseline.abs_humidity_g_m3

    base_gas_corr = corrected_baseline_gas_ohm(baseline, temperature_c, cfg)

    ig = gas_index(gas_resistance_ohm, base_gas_corr)
    ih = hum_index(abs_h, base_abs_h)

    w_sum = cfg.weight_gas + cfg.weight_hum
    if w_sum <= 0:
        raise ValueError("Summe der Gewichte muss > 0 sein")
    wg = cfg.weight_gas / w_sum
    wh = cfg.weight_hum / w_sum

    i_total = wg * ig + wh * ih

    return {
        "gas_index": ig,
        "hum_index": ih,
        "index": i_total,
        "abs_humidity_g_m3": abs_h,
        "baseline_abs_humidity_g_m3": base_abs_h,
        "baseline_gas_corrected_ohm": base_gas_corr,
    }


# -----------------------------
# Mapping Index -> Personen + Raumskalierung
# -----------------------------

def estimate_occupancy_from_index(index_value: float, cfg: ModelConfig) -> float:
    """Roh-Schätzung (float) vor Raumskalierung."""
    if cfg.i_ref_full <= 0:
        raise ValueError("i_ref_full muss > 0 sein")
    return cfg.n_max * (index_value / cfg.i_ref_full)


def scale_occupancy_by_room(n_est: float, room: RoomConfig) -> float:
    """
    Skaliert Personen nach Raumvolumen und Luftwechsel:
    N_scaled = N * (V/Vref) * (ACH/ACHref)
    """
    v = room_volume_m3(room)
    if room.v_ref_m3 <= 0 or room.ach_ref_per_hour <= 0:
        raise ValueError("Referenzwerte müssen > 0 sein")
    return n_est * (v / room.v_ref_m3) * (room.ach_per_hour / room.ach_ref_per_hour)


def estimate_people(
    temperature_c: float,
    rh_percent: float,
    gas_resistance_ohm: float,
    baseline: Baseline,
    cfg: ModelConfig,
    room: RoomConfig,
) -> Dict[str, Any]:
    idx = combined_index(
        temperature_c=temperature_c,
        rh_percent=rh_percent,
        gas_resistance_ohm=gas_resistance_ohm,
        baseline=baseline,
        cfg=cfg,
    )

    n_raw = estimate_occupancy_from_index(idx["index"], cfg)
    n_scaled = scale_occupancy_by_room(n_raw, room)
    n_final = int(round(clamp(n_scaled, 0.0, float(cfg.n_max))))

    return n_final


if __name__ == "__main__":
    room = RoomConfig(area_m2=180.0, height_m=3.0, ach_per_hour=2.0, v_ref_m3=300.0, ach_ref_per_hour=2.0)
    cfg = ModelConfig(weight_gas=0.8, weight_hum=0.2, n_max=125, i_ref_full=0.20, gas_temp_coeff_per_C=0.0)
    baseline = Baseline(temperature_c=21.0, rh_percent=35.0, gas_resistance_ohm=22000.0)

    res = estimate_people(
        temperature_c=21.0,
        rh_percent=37.0,
        gas_resistance_ohm=19959.0,
        baseline=baseline,
        cfg=cfg,
        room=room,
    )
    print(res)
