#!/usr/bin/env python3
"""
Example script demonstrating how different datacenter capacities affect
the energy consumption in the Solstice datacenter model.
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

# Add the parent directory to the Python path to import the model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_datacenter_interface import DatacenterQueryProcessor

def compare_datacenter_capacities():
    """Compare energy consumption for datacenters of different capacities."""
    
    # Initialize the processor (make sure OPENAI_API_KEY is set in your environment)
    try:
        processor = DatacenterQueryProcessor()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the OPENAI_API_KEY environment variable and try again.")
        return
    
    # Test queries with different capacities
    capacity_queries = [
        "Model a 10 MW datacenter with water cooling in Texas",
        "Model a 100 MW datacenter with water cooling in Texas",
        "Model a 500 MW datacenter with water cooling in Texas",
        "Model a 1 GW datacenter with water cooling in Texas",  # Note: 1 GW = 1000 MW
        "Model a 2 GW datacenter with water cooling in Texas"   # Note: 2 GW = 2000 MW
    ]
    
    results = []
    
    # Process each query
    for query in capacity_queries:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}\n")
        
        # Process the query
        query_results = processor.process_query(query, run_simulation=True, save_results=False)
        
        # Print the extracted parameters
        print("\nExtracted Parameters:")
        for param, value in query_results['extracted_parameters'].items():
            print(f"  {param}: {value}")
        
        # Print simulation summary
        if 'simulation_summary' in query_results:
            print("\nSimulation Summary:")
            for key, value in query_results['simulation_summary'].items():
                print(f"  {key}: {value:.2f}")
        
        # Store results for comparison
        capacity = query_results['extracted_parameters']['datacenter_capacity_mw']
        avg_energy = query_results['simulation_summary']['avg_energy_consumption_kw']
        peak_energy = query_results['simulation_summary']['peak_energy_consumption_kw']
        carbon = query_results['simulation_summary']['total_carbon_emissions_tons']
        
        results.append({
            'capacity_mw': capacity,
            'avg_energy_kw': avg_energy,
            'peak_energy_kw': peak_energy,
            'carbon_emissions_tons': carbon,
            'avg_energy_per_mw': avg_energy / capacity,
            'peak_energy_per_mw': peak_energy / capacity,
            'carbon_per_mw': carbon / capacity
        })
    
    # Create a comparison table
    results_df = pd.DataFrame(results)
    print("\n\n=== CAPACITY COMPARISON RESULTS ===")
    print(results_df.to_string(index=False))
    
    # Create visualizations
    plt.figure(figsize=(12, 8))
    
    # Plot absolute energy consumption by capacity
    plt.subplot(2, 2, 1)
    plt.plot(results_df['capacity_mw'], results_df['avg_energy_kw'], marker='o', linewidth=2)
    plt.title('Average Energy Consumption by Datacenter Capacity')
    plt.xlabel('Capacity (MW)')
    plt.ylabel('Energy Consumption (kW)')
    plt.grid(True)
    
    # Plot peak energy consumption by capacity
    plt.subplot(2, 2, 2)
    plt.plot(results_df['capacity_mw'], results_df['peak_energy_kw'], marker='o', color='orange', linewidth=2)
    plt.title('Peak Energy Consumption by Datacenter Capacity')
    plt.xlabel('Capacity (MW)')
    plt.ylabel('Energy Consumption (kW)')
    plt.grid(True)
    
    # Plot energy efficiency (kW per MW capacity)
    plt.subplot(2, 2, 3)
    plt.bar(results_df['capacity_mw'], results_df['avg_energy_per_mw'])
    plt.title('Energy Efficiency by Datacenter Capacity')
    plt.xlabel('Capacity (MW)')
    plt.ylabel('kW per MW capacity')
    plt.grid(True)
    
    # Plot carbon emissions
    plt.subplot(2, 2, 4)
    plt.plot(results_df['capacity_mw'], results_df['carbon_emissions_tons'], marker='s', color='green', linewidth=2)
    plt.title('Carbon Emissions by Datacenter Capacity')
    plt.xlabel('Capacity (MW)')
    plt.ylabel('Carbon Emissions (tons)')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('capacity_comparison.png')
    plt.close()
    
    print(f"\nComparison plot saved as 'capacity_comparison.png'")
    print("\nDone!")

if __name__ == "__main__":
    compare_datacenter_capacities() 