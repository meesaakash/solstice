#!/usr/bin/env python3
"""
Example script for comparing different datacenter configurations.

This script demonstrates how to use the SolsticeDatacenterModel framework to:
1. Compare datacenters in different geographic locations
2. Compare different cooling systems
3. Compare different workload patterns
4. Save and visualize results
"""

import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import copy

# Add parent directory to path to import the model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solstice_framework import SolsticeDatacenterModel

# Set up output directory
OUTPUT_DIR = 'comparison_results'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def compare_locations():
    """Compare datacenter performance across different geographic locations."""
    # Base configuration
    base_config = {
        'datacenter_capacity_mw': 5.0,
        'cooling_type': 'air',
        'simulation_start_date': '2023-06-01'
    }
    
    # Locations to compare
    locations = ['TX']
    location_names = {
        'TX': 'Texas',
    }
    
    # Location-specific configurations
    locations_configs = {
        'TX': {'location': 'TX'},
    }
    
    results = []
    
    # Run simulations for each location
    for location in locations:
        config = base_config.copy()
        config.update(locations_configs[location])
        
        print(f"\nRunning simulation for {location}...")
        model = SolsticeDatacenterModel(**config)
        model.run_simulation()  # Run with default workload pattern
        
        summary = model.query("summary")
        # Add necessary fields that might be missing
        if 'total_carbon_emissions' not in summary:
            summary['total_carbon_emissions'] = sum(model.simulation_results['carbon_emissions'])
        if 'average_power_kw' not in summary:
            summary['average_power_kw'] = sum(model.simulation_results['total_energy']) / len(model.simulation_results['total_energy']) / 1000
        
        summary['location'] = location_names[location]
        results.append(summary)
        
        # Save individual results
        model.save_results_to_csv(f"{OUTPUT_DIR}/{location}_results.csv")
        model.plot_energy_consumption(f"{OUTPUT_DIR}/{location}_energy.png")
        model.plot_carbon_emissions(f"{OUTPUT_DIR}/{location}_carbon.png")
    
    # Create comparison dataframe
    comparison_df = pd.DataFrame(results)
    comparison_df.to_csv(f"{OUTPUT_DIR}/location_comparison.csv", index=False)
    
    # Debug column names
    print("Available columns in location comparison dataframe:")
    print(comparison_df.columns)
    
    # Plot comparison
    plt.figure(figsize=(12, 6))
    plt.bar(comparison_df['location'], comparison_df['total_carbon_emissions'])
    plt.title('Carbon Emissions by Location')
    plt.ylabel('Carbon Emissions (tons CO2)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/location_carbon_comparison.png")
    
    plt.figure(figsize=(12, 6))
    plt.bar(comparison_df['location'], comparison_df['average_power_kw'])
    plt.title('Average Power Consumption by Location')
    plt.ylabel('Average Power (kW)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/location_power_comparison.png")
    
    return comparison_df

def compare_cooling_systems():
    """Compare datacenter performance with different cooling systems."""
    # Base configuration
    base_config = {
        'datacenter_capacity_mw': 5.0,
        'location': 'TX',
        'simulation_start_date': '2023-06-01'
    }
    
    # Cooling systems to compare
    cooling_types = ['air', 'water', 'hybrid']
    cooling_names = {
        'air': 'Air Cooling',
        'water': 'Water Cooling',
        'hybrid': 'Hybrid Cooling'
    }
    
    # Cooling-specific configurations
    cooling_configs = {
        'air': {
            'cooling_type': 'air',
            'cooling_efficiency_factor': 0.6,  # Lower efficiency for air cooling
            'pue_overhead': 1.7               # Higher PUE for air cooling
        },
        'water': {
            'cooling_type': 'water',
            'cooling_efficiency_factor': 0.8,  # Better efficiency for water cooling
            'pue_overhead': 1.3               # Lower PUE for water cooling
        },
        'hybrid': {
            'cooling_type': 'hybrid',
            'cooling_efficiency_factor': 0.85, # Best efficiency for hybrid
            'pue_overhead': 1.25              # Best PUE for hybrid systems
        }
    }
    
    results = []
    
    # Run simulations for each cooling type
    for cooling in cooling_types:
        config = base_config.copy()
        config.update(cooling_configs[cooling])
        
        print(f"\nRunning simulation for {cooling} cooling...")
        model = SolsticeDatacenterModel(**config)
        model.run_simulation()  # Run with default workload pattern
        
        summary = model.query("summary")
        # Add necessary fields that might be missing
        if 'total_carbon_emissions' not in summary:
            summary['total_carbon_emissions'] = sum(model.simulation_results['carbon_emissions'])
        if 'average_power_kw' not in summary:
            summary['average_power_kw'] = sum(model.simulation_results['total_energy']) / len(model.simulation_results['total_energy']) / 1000
            
        summary['cooling_type'] = cooling_names[cooling]
        results.append(summary)
        
        # Save individual results
        model.save_results_to_csv(f"{OUTPUT_DIR}/{cooling}_cooling_results.csv")
        model.plot_energy_consumption(f"{OUTPUT_DIR}/{cooling}_cooling_energy.png")
        model.plot_carbon_emissions(f"{OUTPUT_DIR}/{cooling}_cooling_carbon.png")
    
    # Create comparison dataframe
    comparison_df = pd.DataFrame(results)
    comparison_df.to_csv(f"{OUTPUT_DIR}/cooling_comparison.csv", index=False)
    
    # Debug column names
    print("Available columns in cooling comparison dataframe:")
    print(comparison_df.columns)
    
    # Plot comparison
    plt.figure(figsize=(10, 6))
    
    cooling_types = comparison_df['cooling_type']
    
    # Extract energy breakdown using DataFrame indexing instead of itertuples
    datacenter_energy = []
    cooling_energy = []
    
    for _, row in comparison_df.iterrows():
        if 'energy_breakdown' in row and isinstance(row['energy_breakdown'], dict):
            datacenter_energy.append(row['energy_breakdown'].get('datacenter_percent', 0))
            cooling_energy.append(row['energy_breakdown'].get('cooling_percent', 0))
        else:
            # Use default values if energy_breakdown is missing or not a dict
            datacenter_energy.append(75)  # Assume 75% for datacenter by default
            cooling_energy.append(25)     # Assume 25% for cooling by default
    
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(cooling_types, datacenter_energy, width, label='IT Equipment')
    ax.bar(cooling_types, cooling_energy, width, bottom=datacenter_energy, label='Cooling')
    ax.set_ylabel('Percentage of Total Energy')
    ax.set_title('Energy Breakdown by Cooling Type')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/cooling_energy_comparison.png")
    
    return comparison_df

def compare_workload_patterns():
    """
    Compare different datacenter workload patterns.
    """
    patterns = ['constant', 'diurnal', 'weekly']
    
    # Base configuration for the datacenter
    base_config = {
        'location': 'CA',
        'cooling_type': 'air',
        'datacenter_capacity_mw': 3,
        'simulation_start_date': '2023-01-01',
        'simulation_days': 7,
        'NUM_RACKS': 10,
        'RACK_SUPPLY_APPROACH_TEMP_LIST': [5.0] * 10,
        'RACK_RETURN_APPROACH_TEMP_LIST': [-3.0] * 10,
        'CPUS_PER_RACK': 20,
        'MAX_W_PER_RACK': 10000,
        'RACK_CPU_CONFIG': [
            [{'full_load_pwr': 200, 'idle_pwr': 100} for _ in range(20)]
            for _ in range(10)
        ]
    }
    
    workload_configs = {
        'constant': [75] * 24 * 7,  # Constant 75% load all week
        'diurnal': [50 + 25 * (1 if 8 <= h % 24 < 20 else 0) for h in range(24 * 7)],  # Higher during day
        'weekly': [75 + 15 * (1 if 0 <= (h // 24) % 7 < 5 else -1) for h in range(24 * 7)]  # Higher on weekdays
    }
    
    results = []
    
    for pattern in patterns:
        # Use the base configuration
        config = copy.deepcopy(base_config)
        
        print(f"Running simulation with workload pattern: {pattern}")
        
        # Create a model with the configuration
        model = SolsticeDatacenterModel(config)
        
        # Run the simulation with the specified workload pattern
        workload = workload_configs[pattern]
        model.run_simulation(workload)
        
        # Get summary data or calculate it if not available
        summary = model.query("summary") if hasattr(model, 'query') else {}
        
        # Add necessary fields that might be missing
        if 'total_carbon_emissions' not in summary:
            summary['total_carbon_emissions'] = sum(model.simulation_results['carbon_emissions'])
        if 'average_power_kw' not in summary:
            summary['average_power_kw'] = sum(model.simulation_results['total_energy']) / len(model.simulation_results['total_energy']) / 1000
        
        # Add the workload pattern name to the results
        summary['workload_pattern'] = pattern
        results.append(summary)
    
    # Create a DataFrame from the results
    comparison_df = pd.DataFrame(results)
    
    # Print the available columns for debugging
    print("Available columns in workload comparison dataframe:")
    print(comparison_df.columns)
    
    # Plot the average power consumption instead of total energy
    plt.figure(figsize=(10, 6))
    plt.bar(comparison_df['workload_pattern'], comparison_df['average_power_kw'])
    plt.title('Average Power Consumption by Workload Pattern')
    plt.xlabel('Workload Pattern')
    plt.ylabel('Average Power (kW)')
    plt.savefig(f"{OUTPUT_DIR}/workload_power_comparison.png")
    plt.close()
    
    # Plot carbon emissions
    plt.figure(figsize=(10, 6))
    plt.bar(comparison_df['workload_pattern'], comparison_df['total_carbon_emissions'])
    plt.title('Carbon Emissions by Workload Pattern')
    plt.xlabel('Workload Pattern')
    plt.ylabel('Carbon Emissions (tons CO2)')
    plt.savefig(f"{OUTPUT_DIR}/workload_carbon_comparison.png")
    plt.close()
    
    return comparison_df

def main():
    """Main function to run the comparisons."""
    print("Starting datacenter configuration comparisons...")
    
    # Compare datacenters in different locations
    print("\n=== Comparing Locations ===")
    location_results = compare_locations()
    print("\nLocation comparison summary:")
    print(location_results[['location', 'average_power_kw', 'total_carbon_emissions']])
    
    # Compare cooling systems
    print("\n=== Comparing Cooling Systems ===")
    cooling_results = compare_cooling_systems()
    print("\nCooling systems comparison summary:")
    print(cooling_results[['cooling_type', 'average_power_kw', 'total_carbon_emissions']])
    
    # Compare workload patterns
    print("\n=== Comparing Workload Patterns ===")
    workload_results = compare_workload_patterns()
    print("\nWorkload patterns comparison summary:")
    print(workload_results[['workload_pattern', 'average_power_kw', 'total_carbon_emissions']])
    
    print(f"\nAll comparison results saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main() 