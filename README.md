# Solstice Datacenter Model

A scalable framework for datacenter energy modeling with location-specific data, cooling system options, and carbon intensity tracking.

## Overview

The Solstice Datacenter Model is designed to simulate and analyze energy consumption and carbon emissions for datacenters in various geographic locations, considering factors such as:

- Compute load and workload patterns
- Datacenter hardware energy use
- Datacenter size and capacity
- Cooling system type (air-cooled vs. water-cooled)
- Geographic location (with a focus on Texas and ERCOT)
- Location-specific weather data
- Carbon intensity by region

The framework provides tools for:
- Running simulations over specific time periods
- Analyzing energy consumption patterns
- Calculating carbon emissions
- Comparing different datacenter configurations
- Visualizing results with plots and charts
- Processing natural language queries about simulation results

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/solstice.git
cd solstice/solstice_model

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from solstice_framework import SolsticeDatacenterModel

# Create a model for a datacenter in Texas with air cooling
model = SolsticeDatacenterModel(
    location='TX',
    cooling_type='air',
    datacenter_capacity_mw=1.0,
    simulation_start_date='2023-06-01',
    simulation_days=7
)

# Run the simulation
results = model.run_simulation()

# Save and visualize results
model.save_results_to_csv('tx_datacenter_results.csv')
model.plot_energy_consumption('tx_energy_consumption.png')
model.plot_carbon_emissions('tx_carbon_emissions.png')

# Get summary information
summary = model.query("summary")
print(f"Average Energy Consumption: {summary['average_power_kw']:.2f} kW")
print(f"Total Carbon Emissions: {summary['total_carbon_emissions_tons']:.2f} tons CO2")
```

### Custom Configurations

You can create and load custom datacenter configurations:

```python
# Generate a configuration template
model.create_config_template('custom_config_template.json')

# Create a model with a custom configuration
custom_config = {
    'NUM_RACKS': 10,
    'NUM_ROWS': 2,
    'NUM_RACKS_PER_ROW': 5,
    'MAX_W_PER_RACK': 15000,
    'CPUS_PER_RACK': 200,
    # Additional configuration parameters
}

custom_model = SolsticeDatacenterModel(
    config=custom_config,
    location='TX',
    cooling_type='water',
    datacenter_capacity_mw=2.0
)
```

### Natural Language Queries

The framework provides a natural language query interface for extracting insights:

```python
# Query the model
energy_info = model.query("What is the average energy consumption?")
carbon_info = model.query("Tell me about the carbon emissions")
water_info = model.query("How much water does the datacenter use?")
```

## Examples

The `examples` directory contains several example scripts demonstrating different use cases:

- `compare_datacenter_configs.py`: Compare different datacenter configurations (locations, cooling systems, workload patterns)
- `custom_datacenter_config.py`: Work with custom datacenter configurations and research paper models
- `llm_query_interface.py`: Demonstrates a simulated LLM interface for natural language queries

To run an example:

```bash
cd solstice_model
python examples/compare_datacenter_configs.py
```

## Framework Components

### Core Components

- `SolsticeDatacenterModel`: Main class for datacenter energy modeling
- `LocationManager`: Manages location-specific data (weather, etc.)
- `CoolingManager`: Handles different cooling system types
- `EnergyAnalyzer`: Analyzes and visualizes energy consumption data
- `CarbonIntensityTracker`: Tracks carbon intensity for different regions

### Data Sources

- `data/Weather/`: EPW weather files for different locations
- `data/CarbonIntensity/`: Carbon intensity data by region
- `data/Workload/`: Example workload patterns

## Future Extensions

The framework is designed to be scalable for future extensions, including:

- Integration with LLM tools for text-to-query functionality
- Support for additional cooling technologies
- Integration of more detailed workload models
- Real-time carbon intensity data
- Optimization of datacenter operations for carbon reduction

## References

The model is based on research and approaches from:
- Postema, Björn Frits. "Energy-efficient data centres: model-based analysis of power-performance trade-offs." (2018).
- Sun, Kaiyu, et al. "Prototype energy models for data centers." Energy and Buildings 231 (2021): 110603.
- Breen, Thomas J., et al. "From chip to cooling tower data center modeling: Part I influence of server inlet temperature and temperature rise across cabinet." 2010 12th IEEE Intersociety Conference on Thermal and Thermomechanical Phenomena in Electronic Systems. IEEE, 2010.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 