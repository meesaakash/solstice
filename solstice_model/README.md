# Solstice Datacenter Model

A scalable framework for datacenter energy modeling with location-specific data, cooling system options, carbon intensity tracking, and interactive ERCOT energy data visualization.

## Overview

The Solstice Datacenter Model is designed to simulate and analyze energy consumption and carbon emissions for datacenters in various geographic locations, with a particular focus on Texas and the ERCOT grid. The framework includes both modeling components and visualization tools.

### Key Features

- **Datacenter Modeling**:
  - Compute load and workload pattern simulation
  - Datacenter hardware energy consumption analysis
  - Cooling system modeling (air-cooled vs. water-cooled)
  - Carbon emissions calculation

- **ERCOT Energy Visualization**:
  - Interactive map of ERCOT regions
  - Visualization of renewable generation, energy consumption, LMP prices
  - Interconnection queue data visualization
  - Project filtering by energy type (solar, wind, gas, battery, etc.)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/solstice.git
cd solstice/solstice_model

# Install dependencies
pip install -r requirements.txt
```

### Running the Datacenter Model

```bash
# Run a basic datacenter simulation
python examples/compare_datacenter_configs.py

# The results will be saved in the comparison_results directory
```

### Running the ERCOT Energy Visualization

```bash
# Navigate to the map visualization directory
cd map_visualization

# Process ERCOT Interconnection Queue data (if available)
python process_interconnection_data.py

# Process ERCOT energy data
python process_data.py

# Start a local web server
python -m http.server 8000

# Open your browser and navigate to:
# http://localhost:8000
```

## Datacenter Modeling

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

## ERCOT Energy Visualization

The visualization tool provides an interactive map of the ERCOT grid with various data layers:

### Features

- **Regional Data Visualization**:
  - Renewable Generation (MW)
  - Locational Marginal Price ($/MWh)
  - Energy Consumption (MWh)
  - Temperature (°F)

- **Interconnection Queue**:
  - View and filter projects in the ERCOT interconnection queue
  - Project details: name, capacity, energy type, status
  - Capacity statistics by region and energy type
  - Filter by energy type (solar, wind, gas, battery, etc.)

### Running the Visualization

1. **Prepare the Data**:

```bash
# Navigate to the map visualization directory
cd map_visualization

# Process interconnection queue data
python process_interconnection_data.py

# Process ERCOT energy data
python process_data.py
```

2. **Start the Web Server**:

```bash
# Start a local web server on port 8000
python -m http.server 8000
```

3. **View the Visualization**:
   - Open your web browser
   - Navigate to: http://localhost:8000

### Using the Visualization

1. **Toggle Data Types**:
   - Use the dropdown menu to select data type (renewable generation, LMP, etc.)
   - Select a region or view all regions
   - Select a date to view historical data

2. **View Interconnection Queue**:
   - Toggle the "Interconnection Queue" switch
   - Use checkboxes to filter by energy type
   - Hover over projects to see details
   - Click on projects or regions for more information

3. **Data Analysis**:
   - View charts and statistics in the right panel
   - Toggle between different views and filters
   - See capacity breakdowns by energy type and region

### Adding Custom Data

To add your own ERCOT data or interconnection queue information:

1. **ERCOT Data**:
   - Place CSV files in `solstice/solstice_model/data/ERCOT_data/`
   - Modify `process_data.py` if needed to handle your specific format

2. **Interconnection Queue Data**:
   - Place spreadsheet in `solstice/solstice_model/data/ERCOT_data/Interconnection/`
   - The script will automatically detect and process it

## Example Scripts

The `examples` directory contains several example scripts demonstrating different use cases:

- `compare_datacenter_configs.py`: Compare different datacenter configurations
- `custom_datacenter_config.py`: Work with custom datacenter configurations
- `llm_query_interface.py`: Demonstrates a simulated LLM interface for natural language queries

To run an example:

```bash
cd solstice_model
python examples/compare_datacenter_configs.py
```

## Data Sources

- `data/Weather/`: EPW weather files for different locations
- `data/CarbonIntensity/`: Carbon intensity data by region
- `data/Workload/`: Example workload patterns
- `data/ERCOT_data/`: ERCOT energy data and interconnection queue information

## Troubleshooting

- **Port already in use**: If you see "Address already in use" when starting the web server, try a different port:
  ```bash
  python -m http.server 8001
  ```
  Then navigate to http://localhost:8001

- **Missing dependencies**: If you encounter errors about missing modules, make sure you've installed all requirements:
  ```bash
  pip install -r requirements.txt
  ```

- **Data processing errors**: For issues with Excel files, ensure you have openpyxl installed:
  ```bash
  pip install openpyxl
  ```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 