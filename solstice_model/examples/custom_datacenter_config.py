#!/usr/bin/env python3
"""
Example script for working with custom datacenter configurations.

This script demonstrates how to:
1. Create a configuration template
2. Load a custom configuration from a JSON file
3. Create a custom datacenter configuration based on research paper specifications
4. Run simulations with the custom configurations
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path to import the model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solstice_framework import SolsticeDatacenterModel

# Set up output directory
OUTPUT_DIR = 'custom_configs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_config_template():
    """
    Create a configuration template file that can be modified.
    """
    print("Creating configuration template...")
    
    # Create a model with default settings
    model = SolsticeDatacenterModel(
        location='TX',
        cooling_type='air',
        datacenter_capacity_mw=1.0,
        simulation_start_date='2023-06-01',
        simulation_days=7
    )
    
    # Create a template configuration file
    template_file = f"{OUTPUT_DIR}/datacenter_config_template.json"
    model.create_config_template(template_file)
    
    print(f"Template created: {template_file}")
    
    # Display contents of the template
    with open(template_file, 'r') as f:
        config = json.load(f)
    
    print("\nTemplate structure:")
    print(json.dumps(config, indent=2, sort_keys=True)[:500] + "...\n")
    
    return template_file

def create_custom_config():
    """
    Create a custom datacenter configuration based on user specifications.
    """
    print("Creating custom datacenter configuration...")
    
    # Define a custom datacenter configuration
    custom_config = {
        'datacenter': {
            'num_racks': 10,
            'num_rows': 2,
            'num_racks_per_row': 5,
            'max_w_per_rack': 15000,
            'cpus_per_rack': 200
        },
        'cooling': {
            'type': 'water',
            'parameters': {
                'coef_of_performance': 6.0,
                'water_usage_factor': 0.8
            }
        },
        'location': {
            'code': 'TX',
        },
        'simulation': {
            'start_date': '2023-07-01',
            'days': 14,
            'capacity_mw': 2.0
        },
        'rack_config': {
            'supply_approach_temps': [5.0] * 10,  # Custom supply approach temps
            'return_approach_temps': [-3.0] * 10,  # Custom return approach temps
            'cpu_specs': {
                'idle_power': 100,
                'full_load_power': 300
            }
        }
    }
    
    # Save the custom configuration to a file
    custom_config_file = f"{OUTPUT_DIR}/custom_datacenter_config.json"
    with open(custom_config_file, 'w') as f:
        json.dump(custom_config, f, indent=2)
    
    print(f"Custom configuration created: {custom_config_file}")
    
    return custom_config_file

def load_custom_config_and_run(config_file):
    """
    Load a custom datacenter configuration from a file and run a simulation.
    
    Args:
        config_file: Path to the configuration file
    """
    print(f"Loading configuration from {config_file}...")
    
    # Load the configuration
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Extract parameters from the configuration
    location_code = config['location']['code']
    cooling_type = config['cooling']['type']
    capacity_mw = config['simulation']['capacity_mw']
    start_date = config['simulation']['start_date']
    days = config['simulation']['days']
    
    # Create datacenter model based on the configuration
    # We need to convert the configuration to the format expected by the model
    dc_config = {
        'NUM_RACKS': config['datacenter']['num_racks'],
        'NUM_ROWS': config['datacenter']['num_rows'],
        'NUM_RACKS_PER_ROW': config['datacenter']['num_racks_per_row'],
        'MAX_W_PER_RACK': config['datacenter']['max_w_per_rack'],
        'CPUS_PER_RACK': config['datacenter']['cpus_per_rack'],
    }
    
    # Add supply and return approach temperatures if specified
    if 'rack_config' in config and 'supply_approach_temps' in config['rack_config']:
        dc_config['RACK_SUPPLY_APPROACH_TEMP_LIST'] = config['rack_config']['supply_approach_temps']
    
    if 'rack_config' in config and 'return_approach_temps' in config['rack_config']:
        dc_config['RACK_RETURN_APPROACH_TEMP_LIST'] = config['rack_config']['return_approach_temps']
    
    # Create CPU configuration if specified
    if 'rack_config' in config and 'cpu_specs' in config['rack_config']:
        idle_power = config['rack_config']['cpu_specs']['idle_power']
        full_load_power = config['rack_config']['cpu_specs']['full_load_power']
        
        # Create CPU configuration for each rack
        cpu_config = []
        for _ in range(dc_config['NUM_RACKS']):
            rack_cpus = []
            for _ in range(dc_config['CPUS_PER_RACK']):
                rack_cpus.append({
                    'idle_pwr': idle_power,
                    'full_load_pwr': full_load_power
                })
            cpu_config.append(rack_cpus)
        
        dc_config['RACK_CPU_CONFIG'] = cpu_config
    
    print("Creating datacenter model with custom configuration...")
    model = SolsticeDatacenterModel(
        config=dc_config,
        location=location_code,
        cooling_type=cooling_type,
        datacenter_capacity_mw=capacity_mw,
        simulation_start_date=start_date,
        simulation_days=days
    )
    
    print("Running simulation...")
    model.run_simulation()
    
    # Save results
    base_filename = os.path.splitext(os.path.basename(config_file))[0]
    results_file = f"{OUTPUT_DIR}/{base_filename}_results.csv"
    model.save_results_to_csv(results_file)
    
    # Generate plots
    energy_plot = f"{OUTPUT_DIR}/{base_filename}_energy.png"
    carbon_plot = f"{OUTPUT_DIR}/{base_filename}_carbon.png"
    model.plot_energy_consumption(energy_plot)
    model.plot_carbon_emissions(carbon_plot)
    
    # Print summary
    summary = model.query("summary")
    print("\nSimulation Results Summary:")
    print(f"Average Power: {summary['average_power_kw']:.2f} kW")
    print(f"Peak Power: {summary['peak_power_kw']:.2f} kW")
    print(f"Total Energy: {summary['total_energy_kwh']:.2f} kWh")
    print(f"Total Carbon Emissions: {summary['total_carbon_emissions_tons']:.2f} tons CO2")
    
    if cooling_type == 'water' and 'total_water_usage_liters' in summary:
        print(f"Total Water Usage: {summary['total_water_usage_liters']:.2f} liters")
    
    print(f"\nResults saved to: {results_file}")
    print(f"Energy plot: {energy_plot}")
    print(f"Carbon plot: {carbon_plot}")

def create_research_paper_model():
    """
    Create a datacenter model based on specifications from a research paper.
    This demonstrates how to incorporate new datacenter models from research.
    """
    print("Creating datacenter model based on research paper specifications...")
    
    # Example research paper specifications
    # These could be loaded from a JSON file or defined programmatically
    research_specs = {
        'server_specs': {
            'cpu_idle_power': 85,  # Watts
            'cpu_full_load_power': 250,  # Watts
            'fan_power_factor': 0.15,  # Fraction of CPU power for fans
            'memory_power': 35  # Watts per server
        },
        'cooling_parameters': {
            'type': 'hybrid',
            'coef_of_performance': 5.5,
            'water_usage_factor': 0.4
        },
        'pue_target': 1.25,  # Target PUE from the paper
        'paper_reference': {
            'title': 'Energy-Efficient Datacenter Design for Cloud Computing',
            'authors': 'Smith et al.',
            'year': 2022,
            'doi': '10.1234/example.doi'
        }
    }
    
    # Save research specifications to a file
    research_file = f"{OUTPUT_DIR}/research_paper_specs.json"
    with open(research_file, 'w') as f:
        json.dump(research_specs, f, indent=2)
    
    # Create base model
    model = SolsticeDatacenterModel(
        location='TX',
        cooling_type='air',  # Will be overridden by research specs
        datacenter_capacity_mw=1.5,
        simulation_start_date='2023-05-01',
        simulation_days=7
    )
    
    # Load research paper model
    model.load_research_paper_model(research_specs)
    
    # Run simulation with research paper model
    print("Running simulation with research paper model...")
    model.run_simulation()
    
    # Save results
    results_file = f"{OUTPUT_DIR}/research_paper_model_results.csv"
    model.save_results_to_csv(results_file)
    
    # Generate plots
    energy_plot = f"{OUTPUT_DIR}/research_paper_model_energy.png"
    carbon_plot = f"{OUTPUT_DIR}/research_paper_model_carbon.png"
    model.plot_energy_consumption(energy_plot)
    model.plot_carbon_emissions(carbon_plot)
    
    # Print summary
    summary = model.query("summary")
    print("\nResearch Paper Model Simulation Results:")
    print(f"Average Power: {summary['average_power_kw']:.2f} kW")
    print(f"Peak Power: {summary['peak_power_kw']:.2f} kW")
    print(f"Total Energy: {summary['total_energy_kwh']:.2f} kWh")
    print(f"Total Carbon Emissions: {summary['total_carbon_emissions_tons']:.2f} tons CO2")
    
    # Calculate actual PUE and compare to target
    avg_dc_power = summary['energy_breakdown']['datacenter_percent'] / 100 * summary['average_power_kw']
    avg_total_power = summary['average_power_kw']
    actual_pue = avg_total_power / avg_dc_power if avg_dc_power > 0 else 1.0
    
    print(f"\nTarget PUE from paper: {research_specs['pue_target']}")
    print(f"Actual PUE from simulation: {actual_pue:.2f}")
    
    print(f"\nResults saved to: {results_file}")
    print(f"Energy plot: {energy_plot}")
    print(f"Carbon plot: {carbon_plot}")

def main():
    """Main function to demonstrate custom datacenter configurations."""
    print("Demonstrating custom datacenter configurations...\n")
    
    # Create a configuration template
    template_file = create_config_template()
    
    # Create a custom configuration
    custom_config_file = create_custom_config()
    
    # Load the custom configuration and run a simulation
    print("\n=== Running Simulation with Custom Configuration ===")
    load_custom_config_and_run(custom_config_file)
    
    # Create and run a research paper model
    print("\n=== Creating Research Paper Model ===")
    create_research_paper_model()
    
    print("\nAll examples completed. Results saved to the output directory.")

if __name__ == "__main__":
    main() 