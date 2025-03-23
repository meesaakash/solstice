# Texas ERCOT Energy Data Map Visualization

This visualization tool displays energy data from the Electric Reliability Council of Texas (ERCOT) on an interactive map, allowing users to explore renewable generation, energy consumption, pricing, temperature data, and interconnection queue information across different regions of Texas.

## Features

- Interactive map of Texas with ERCOT regions (North, West, South, Houston, Panhandle)
- Visualization of various energy metrics:
  - Renewable Energy Generation (MW)
  - Locational Marginal Prices ($/MWh)
  - Energy Consumption (MWh)
  - Temperature (°F)
- Interconnection Queue visualization:
  - View projects in the ERCOT interconnection queue
  - Filter projects by energy type (solar, wind, gas, battery, etc.)
  - See potential generation capacity by region and energy type
- Date selection for viewing historical data
- Region selection for detailed analysis
- Interactive charts and statistics panels
- Responsive design for desktop and mobile viewing

## Setup and Installation

1. **Dependencies**
   The visualization uses:
   - OpenLayers (v7.3.0) for map rendering
   - Chart.js for data visualization
   - Standard HTML/CSS/JavaScript (no build process required)

2. **Running the Application**
   - Simply open `index.html` in a web browser
   - For proper data loading, you should use a local web server:
     ```
     # Using Python's built-in HTTP server
     python -m http.server
     
     # Or use any other local web server of your choice
     ```

3. **Processing Data**
   To update the data visualization with the latest ERCOT data:
   ```
   python process_data.py
   ```
   This script will:
   - Process ERCOT data files from the `../data/ERCOT_data` directory
   - Generate JSON files in the `data/` directory
   - Create an index file with available dates

4. **Processing Interconnection Queue Data**
   To update the interconnection queue data:
   ```
   python process_interconnection_data.py
   ```
   This script will:
   - Look for a spreadsheet with interconnection queue data (Excel or CSV)
   - Process the data into GeoJSON format
   - Generate interconnection project markers and summary statistics
   - If no interconnection queue file is found, sample data will be created

## Data Sources

This visualization uses:
- ERCOT renewable generation data
- ERCOT locational marginal price (LMP) data
- Texas load data by region
- Temperature data for Texas regions
- Datacenter simulation results from the Solstice model
- ERCOT interconnection queue data (spreadsheet)

## Using the Visualization

1. **Map Navigation**
   - Zoom in/out using mouse wheel or buttons
   - Pan by dragging the map
   - Click on regions to see detailed information

2. **Data Selection**
   - Use the top controls to select:
     - Data type (renewable generation, LMP, energy consumption, temperature)
     - Region (all regions or specific region)
     - Date to view

3. **Interconnection Queue Visualization**
   - Toggle the "Interconnection Queue" switch to show/hide projects
   - Use the energy type checkboxes to filter by project type
   - Click on project markers to see detailed information
   - View the interconnection capacity table showing potential new generation by zone and type
   - The chart will automatically update to show interconnection capacity data

4. **Data Analysis**
   - The right panel shows charts and statistics for the selected data
   - When a region is selected, detailed data for that region is shown
   - When "All Regions" is selected, comparative data across regions is shown

## Customizing the Visualization

The visualization can be extended or customized:

1. **Adding New Data Types**
   - Add new options to the `dataType` select element in `index.html`
   - Add corresponding data processing in `process_data.py`
   - Update the data display functions in `map.js`

2. **Customizing Interconnection Queue Data**
   - Place your interconnection queue data file in the `map_visualization` directory
   - Name it with "interconnection" in the filename (e.g., "ercot_interconnection_queue.xlsx")
   - The script will automatically detect column names for project ID, name, capacity, etc.
   - You can modify `process_interconnection_data.py` to adjust how columns are mapped

3. **Changing Map Appearance**
   - Modify the region definitions in `map.js`
   - Adjust colors in the `ercotRegions` object
   - Customize the map base layer in the `initMap()` function

4. **Adding New Features**
   - The modular code structure allows for easy extension
   - Consider adding time-series animation or heat maps for more advanced visualization

## License

This project is part of the Solstice datacenter modeling framework.

## Acknowledgments

- OpenLayers for providing the mapping library
- Chart.js for the visualization tools
- ERCOT for providing the energy data 