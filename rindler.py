# relativistic_trip_planner.py
# ------------------------------------------------------------
# Constant proper-acceleration (Rindler) trip planner.
# Supports:
#   - Single acceleration leg from rest
#   - Symmetric out-and-back (4 legs: accel, brake, accel back, brake)
#   - Solve for proper acceleration given ship-time & Earth-time
#   - Photon-rocket power & energy bookkeeping
#
# Units: SI (m, s, kg, W, J). Light-years/AU shown in helpers.

from math import sinh, cosh, tanh
from typing import Dict, Any

# --- Constants
C = 299_792_458.0           # m/s
G = 9.80665                 # m/s^2
JULIAN_YEAR_S = 31_557_600.0  # s (365.25 d)
DAY_S = 86_400.0            # s
LY_M = 9.460_730_472_58e15  # 1 ly in meters
AU_M = 1.495_978_707e11     # 1 AU in meters

# --- Utilities

def pretty_time(seconds: float) -> str:
    """Format seconds into d hh:mm:ss.sss."""
    sign = "-" if seconds < 0 else ""
    s = abs(seconds)
    d = int(s // 86400); s -= d*86400
    h = int(s // 3600);  s -= h*3600
    m = int(s // 60);    s -= m*60
    return f"{sign}{d} d {h:02d}:{m:02d}:{s:06.3f} s"

def solve_eta_from_ratio(R: float, tol: float = 1e-13, max_iter: int = 200) -> float:
    """
    Solve for eta > 0 such that  sinh(eta)/eta = R  using bisection.
    For the 4-leg symmetric trip, R = T_earth / tau_ship.
    """
    if R <= 1.0:
        # Degenerate low-speed limit; return small eta.
        return 1e-12

    # f(eta) = sinh(eta)/eta - R is strictly increasing on (0, inf)
    def f(e: float) -> float:
        return (sinh(e)/e) - R if e > 0 else -R

    lo, hi = 0.0, 50.0
    # Expand hi until we bracket the root
    while f(hi) < 0.0 and hi < 2_000.0:
        hi *= 2.0

    for _ in range(max_iter):
        mid = 0.5*(lo + hi)
        fm = f(mid)
        if abs(fm) < tol:
            return mid
        if fm > 0.0:
            hi = mid
        else:
            lo = mid
    return 0.5*(lo + hi)

# --- Single acceleration leg (from rest), constant proper acceleration

def single_leg_from_alpha_tau(alpha: float, tau: float) -> Dict[str, float]:
    """
    One acceleration leg from rest with constant proper acceleration alpha (m/s^2),
    over ship proper time tau (s).
    Returns:
        eta, beta, gamma, t1 (Earth time s), x1 (Earth distance m).
    """
    eta = alpha * tau / C
    beta = tanh(eta)
    gamma = cosh(eta)
    t1 = (C/alpha) * sinh(eta)
    x1 = (C*C/alpha) * (gamma - 1.0)
    return dict(eta=eta, beta=beta, gamma=gamma, t1=t1, x1=x1)

# --- Symmetric out-and-back (4 legs: accel, brake, accel back, brake)

def symmetric_out_and_back_solve_alpha(tau_ship: float, T_earth: float) -> Dict[str, float]:
    """
    Given total ship proper time tau_ship (s) and desired total Earth time T_earth (s),
    solve for the proper acceleration alpha (m/s^2) for a 4-leg symmetric trip.
    Returns:
        alpha, eta (per accel leg), beta_max, gamma_max,
        t1 (Earth time per accel leg), x1 (distance per accel leg),
        T_earth_check (should match T_earth), turnaround_distance (m).
    """
    tau_leg = 0.25 * tau_ship
    R = T_earth / tau_ship              # ratio for equation sinh(eta)/eta = R
    eta = solve_eta_from_ratio(R)
    alpha = (C * eta) / tau_leg         # from eta = alpha * tau_leg / c

    beta_max = tanh(eta)
    gamma_max = cosh(eta)
    t1 = (C/alpha) * sinh(eta)
    x1 = (C*C/alpha) * (gamma_max - 1.0)
    T_earth_check = 4.0 * t1
    turnaround_distance = 2.0 * x1

    return dict(alpha=alpha, eta=eta, beta_max=beta_max, gamma_max=gamma_max,
                t1=t1, x1=x1, T_earth_check=T_earth_check,
                turnaround_distance=turnaround_distance)

def symmetric_out_and_back_from_alpha(tau_ship: float, alpha: float) -> Dict[str, float]:
    """
    Given total ship proper time tau_ship (s) and chosen proper acceleration alpha (m/s^2),
    compute Earth time, distances, and peak speed for the 4-leg symmetric trip.
    Returns:
        eta, beta_max, gamma_max, T_earth, turnaround_distance, t1, x1
    """
    tau_leg = 0.25 * tau_ship
    eta = alpha * tau_leg / C
    beta_max = tanh(eta)
    gamma_max = cosh(eta)
    t1 = (C/alpha) * sinh(eta)
    x1 = (C*C/alpha) * (gamma_max - 1.0)
    T_earth = 4.0 * t1
    turnaround_distance = 2.0 * x1
    return dict(eta=eta, beta_max=beta_max, gamma_max=gamma_max,
                T_earth=T_earth, turnaround_distance=turnaround_distance,
                t1=t1, x1=x1)

# --- Photon-rocket bookkeeping (optional)

def photon_rocket_power_energy(M: float, alpha: float, T_earth: float) -> Dict[str, float]:
    """
    Photon rocket with constant proper acceleration alpha in lab frame:
        Thrust F = M*alpha
        Power    P = F*c = M*alpha*c      (W)
        Energy   E = P*T_earth            (J)
    """
    P = (M * alpha) * C
    E = P * T_earth
    return dict(P=P, E=E)

# --- High-level convenience wrapper

def summarize_out_and_back(tau_ship_days: float, T_earth_years: float, M_kg: float) -> Dict[str, Any]:
    """
    One-shot summary:
      Inputs: total ship proper time (days), total Earth time (years), ship mass (kg)
      Solves alpha; reports speeds, times, distances, and photon-drive power/energy.
    """
    tau_ship = tau_ship_days * DAY_S
    T_earth = T_earth_years * JULIAN_YEAR_S
    sol = symmetric_out_and_back_solve_alpha(tau_ship, T_earth)
    power = photon_rocket_power_energy(M_kg, sol["alpha"], sol["T_earth_check"])

    return dict(
        # inputs
        input_tau_ship_days=tau_ship_days,
        input_T_earth_years=T_earth_years,
        input_mass_kg=M_kg,

        # acceleration & kinematics
        alpha_m_s2=sol["alpha"],
        alpha_in_g=sol["alpha"]/G,
        eta=sol["eta"],
        beta_max=sol["beta_max"],
        gamma_max=sol["gamma_max"],

        # timing
        earth_time_total_s=sol["T_earth_check"],
        earth_time_total_pretty=pretty_time(sol["T_earth_check"]),
        ship_time_total_pretty=pretty_time(tau_ship),

        # distances (to turnaround)
        distance_turnaround_m=sol["turnaround_distance"],
        distance_turnaround_ly=sol["turnaround_distance"]/LY_M,
        distance_turnaround_AU=sol["turnaround_distance"]/AU_M,

        # photon-rocket power & energy
        power_W=power["P"],
        power_in_PW=power["P"]/1e15,
        energy_J=power["E"],
        energy_in_TJ=power["E"]/1e12
    )

# --- Example usage
if __name__ == "__main__":
    # Example: 14 ship-days total, 20 Earth-years total, 50,000 t ship
    summary = summarize_out_and_back(
        tau_ship_days = 30,
        T_earth_years = 10000,
        M_kg = 1e7
    )
    for k, v in summary.items():
        print(f"{k}: {v}")
