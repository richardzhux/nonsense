import numpy as np

# Constants
c = 299_792_458  # Speed of light in m/s
m = 70_000  # Mass of the ship in kg
t_final = 1.0  # Time duration for acceleration in seconds
v_final = 0.999999 * c  # Final velocity close to the speed of light
a = v_final / t_final  # Constant acceleration

# Time step for numerical integration
dt = 1e-3  # Small time step for accuracy
num_steps = int(t_final / dt)

# Lorentz factor function
def lorentz_gamma(v):
    return 1 / np.sqrt(1 - (v / c)**2)

# Force calculation for F = ma
def classical_force(a):
    return m * a

# Force calculation for F = sqrt(ma)
def sqrt_force(a):
    return np.sqrt(m * a)

# Force calculation for F = cubed root(ma)
def cubed_root_force(a):
    return np.cbrt(m * a)

# Power calculation for each force type
def power_classical(v):
    F = classical_force(a)
    return F * v

def power_sqrt(v):
    F = sqrt_force(a)
    return F * v

def power_cubed_root(v):
    F = cubed_root_force(a)
    return F * v

# Initialize variables
v = 0  # Initial velocity
x = 0  # Initial position
t_ship = 0  # Time on the ship
total_energy_classical = 0  # Total energy for classical force
total_energy_sqrt = 0  # Total energy for sqrt force
total_energy_cubed_root = 0  # Total energy for cubed root force

# Numerical integration over 1 second of constant acceleration
for step in range(num_steps):
    # Time in this step
    time = step * dt
    
    # Calculate the Lorentz factor for the current velocity
    gamma = lorentz_gamma(v)
    
    # Calculate instantaneous power for each force type
    P_classical = power_classical(v)
    P_sqrt = power_sqrt(v)
    P_cubed_root = power_cubed_root(v)
    
    # Update total energy for each force type
    total_energy_classical += P_classical * dt
    total_energy_sqrt += P_sqrt * dt
    total_energy_cubed_root += P_cubed_root * dt
    
    # Update velocity and position
    v += a * dt  # Constant acceleration applied to velocity
    x += v * dt  # Update position based on velocity
    
    # Calculate proper time on the ship
    t_ship += dt / gamma

# Output results in scientific notation and rounded to 2 decimal places
print(f"Total Energy (J) - Classical F = ma: {total_energy_classical:.2e}")
print(f"Total Energy (J) - Square Root F = sqrt(ma): {total_energy_sqrt:.2e}")
print(f"Total Energy (J) - Cubed Root F = cubed_root(ma): {total_energy_cubed_root:.2e}")
print(f"Final Velocity (m/s): {v:.2e}")
print(f"Distance Traveled (m): {x:.2e}")
print(f"Ship Time (s): {t_ship:.2e}")
