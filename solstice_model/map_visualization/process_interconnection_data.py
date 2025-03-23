#!/usr/bin/env python3
"""
Process ERCOT Interconnection Queue Data

This script processes the ERCOT interconnection queue spreadsheet and converts
it into GeoJSON format for visualization on the map.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re

# Constants
OUTPUT_DIR = "data"
ERCOT_DATA_DIR = "../data/ERCOT_data"
INTERCONNECTION_DIR = os.path.join(ERCOT_DATA_DIR, "Interconnection")
ERCOT_ZONES = ["NORTH", "WEST", "SOUTH", "HOUSTON", "PANHANDLE"]
ENERGY_TYPES = ["SOLAR", "WIND", "GAS", "BATTERY", "OTHER"]

def load_interconnection_data(filepath):
    """
    Load the ERCOT interconnection queue data from the RPT spreadsheet.
    
    Args:
        filepath: Path to the RPT spreadsheet file
        
    Returns:
        Pandas DataFrame with the interconnection queue data
    """
    print(f"Loading interconnection queue data from {filepath}")
    
    # Special handling for ERCOT GIS Report format
    if "GIS_Report" in filepath:
        print("Detected ERCOT GIS Report format")
        # First check the large generators sheet
        try:
            # Headers are at row 30, data starts at row 35
            df_large = pd.read_excel(filepath, sheet_name='Project Details - Large Gen', header=30, skiprows=34)
            print(f"Loaded large generator data with {len(df_large)} rows")
            
            # Try to also load small generators if available
            try:
                df_small = pd.read_excel(filepath, sheet_name='Project Details - Small Gen', header=30, skiprows=34)
                print(f"Loaded small generator data with {len(df_small)} rows")
                
                # Combine large and small generator data
                df = pd.concat([df_large, df_small], ignore_index=True)
                print(f"Combined data: {len(df)} rows")
            except:
                # If small generators fails, just use large generators
                df = df_large
                print("Only using large generator data")
            
            # Clean column names
            df.columns = [str(col).strip().upper().replace(' ', '_') if col is not None else f"COL_{i}" 
                         for i, col in enumerate(df.columns)]
            
            # Display column information
            print(f"Columns after cleaning: {df.columns.tolist()}")
            
            # For GIS reports, rename known columns to standard names for processing
            column_mapping = {
                'INR': 'PROJECT_ID',
                'PROJECT_NAME': 'NAME',
                'PROJECT_CODE': 'PROJECT_ID',
                'GIM_STUDY_PHASE': 'STATUS',
                'RESOURCE_TYPE': 'FUEL_TYPE',
                'COUNTY': 'COUNTY',
                'SUMMER_MW': 'CAPACITY',
                'CAPACITY_MW': 'CAPACITY',
                'GIS_SUMMER_MW': 'CAPACITY',
                'INSTALLED_CAPACITY': 'CAPACITY',
                'GENERATOR_TYPE': 'TECHNOLOGY',
                'TECHNOLOGY_TYPE': 'TECHNOLOGY',
                'POI_LOCATION': 'LOCATION'
            }
            
            # Apply column mapping where columns exist
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and new_col not in df.columns:
                    df[new_col] = df[old_col]
            
            return df
        
        except Exception as e:
            print(f"Error loading ERCOT GIS Report format: {e}")
            print("Trying generic Excel format...")
    
    # Regular handling for other files
    # Determine file type and load accordingly
    if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
        # Try to identify the specific format of the RPT file
        # Some Excel files may have multiple sheets or require specific parameters
        try:
            # First try reading with default parameters
            df = pd.read_excel(filepath)
            
            # Check if we got data
            if df.empty or len(df.columns) < 3:
                # Try again with sheet index 1 if first sheet was empty or had few columns
                df = pd.read_excel(filepath, sheet_name=1)
                
            # Check if this looks like an ERCOT GIS report
            if 'GIS_PROJECT_CODE' in [col.upper() for col in df.columns]:
                print("Detected ERCOT GIS Report format")
            else:
                print("Using generic Excel format")
                
        except Exception as e:
            print(f"Error reading Excel file with default parameters: {e}")
            # Try with specific sheet name that might be in the RPT file
            sheet_names = pd.ExcelFile(filepath).sheet_names
            print(f"Available sheets: {sheet_names}")
            # Try the first non-empty sheet
            for sheet in sheet_names:
                try:
                    df = pd.read_excel(filepath, sheet_name=sheet)
                    if not df.empty and len(df.columns) > 3:
                        print(f"Successfully loaded data from sheet: {sheet}")
                        break
                except:
                    continue
    elif filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}. Please provide an Excel or CSV file.")
    
    # Clean column names
    df.columns = [col.strip().upper().replace(' ', '_') for col in df.columns]
    
    # Display info about loaded data
    print(f"Loaded {len(df)} rows with columns: {df.columns.tolist()}")
    
    return df

def extract_coordinates(location_str, lat_col=None, lon_col=None):
    """
    Extract coordinates from location string or separate latitude/longitude columns.
    
    Args:
        location_str: String containing location information
        lat_col: Value from latitude column if available
        lon_col: Value from longitude column if available
        
    Returns:
        Tuple of (longitude, latitude) or None if precise location cannot be determined
    """
    # First check if we have direct lat/lon values
    if lat_col is not None and lon_col is not None:
        if not pd.isna(lat_col) and not pd.isna(lon_col):
            try:
                lat = float(lat_col)
                lon = float(lon_col)
                # Verify coordinates are in Texas bounds
                if 25.0 <= lat <= 37.0 and -107.0 <= lon <= -93.0:
                    return (lon, lat)
            except (ValueError, TypeError):
                pass  # If conversion fails, continue with other methods
    
    # Texas bounds approximate: 
    # Longitude: -106.65 to -93.51
    # Latitude: 25.84 to 36.50
    
    if pd.isna(location_str):
        # Return None if no location info available
        return None
    
    # Try to extract coordinates if in a standard format
    coord_pattern = r'(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)'
    match = re.search(coord_pattern, str(location_str))
    
    if match:
        # If coordinates are found in the string, use them
        lat, lon = float(match.group(1)), float(match.group(2))
        
        # Verify coordinates are in Texas bounds
        if -107.0 <= lon <= -93.0 and 25.0 <= lat <= 37.0:
            return (lon, lat)
    
    # If we have a county or location string, try to find a match to a known zone
    # and use its central coordinates with a small random offset for visualization
    location_str = str(location_str).upper()
    
    # Central points for each zone (approximate)
    zone_coords = {
        "north": (-97.2, 33.2),
        "west": (-101.5, 32.0),
        "south": (-98.5, 28.5),
        "houston": (-95.5, 29.8),
        "panhandle": (-101.5, 35.5)
    }
    
    # Try to match location string to a zone
    for zone, coords in zone_coords.items():
        if zone.upper() in location_str:
            # Add small randomness around the central point to avoid overlapping markers
            lon = coords[0] + np.random.uniform(-0.2, 0.2)
            lat = coords[1] + np.random.uniform(-0.2, 0.2)
            return (lon, lat)
    
    # If no precise location can be determined, return None
    return None

def determine_zone(data):
    """
    Determine the ERCOT zone for a project.
    
    Args:
        data: Dictionary or DataFrame row with project information
        
    Returns:
        String representing the ERCOT zone
    """
    # Check for columns that might contain zone information in the RPT file
    possible_zone_cols = ['ZONE', 'REGION', 'WEATHER_ZONE', 'AREA', 'LOCATION', 'GIS_ERCOT_ZONE']
    
    # Try all possible zone columns
    for col in possible_zone_cols:
        if col in data and not pd.isna(data[col]):
            zone = str(data[col]).upper()
            for ercot_zone in ERCOT_ZONES:
                if ercot_zone in zone:
                    return ercot_zone.lower()
    
    # Map of counties to zones (expanded with Texas counties)
    county_to_zone = {
        # North Zone counties
        "DALLAS": "north",
        "TARRANT": "north",
        "COLLIN": "north",
        "DENTON": "north",
        "ELLIS": "north",
        "JOHNSON": "north",
        "KAUFMAN": "north",
        "PARKER": "north",
        "ROCKWALL": "north",
        "WISE": "north",
        # Many more counties... (shortened for clarity)
    }
    
    # Check possible county columns
    possible_county_cols = ['COUNTY', 'COUNTIES', 'COUNTY_NAME', 'GIS_COUNTY', 'COUNTY_NAMES']
    for col in possible_county_cols:
        if col in data and not pd.isna(data[col]):
            county_str = str(data[col]).upper()
            # Check for multiple counties (comma-separated)
            counties = [county.strip() for county in county_str.split(',')]
            for county in counties:
                if county in county_to_zone:
                    return county_to_zone[county]
    
    # Some basic city to zone mapping
    city_to_zone = {
        "DALLAS": "north",
        "FORT WORTH": "north",
        "PLANO": "north",
        "ARLINGTON": "north",
        "DENTON": "north",
        
        "MIDLAND": "west",
        "ODESSA": "west",
        "ABILENE": "west",
        "SAN ANGELO": "west",
        
        "SAN ANTONIO": "south",
        "CORPUS CHRISTI": "south",
        "LAREDO": "south",
        "MCALLEN": "south",
        "BROWNSVILLE": "south",
        
        "HOUSTON": "houston",
        "GALVESTON": "houston",
        "BEAUMONT": "houston",
        "PORT ARTHUR": "houston",
        "THE WOODLANDS": "houston",
        "SUGAR LAND": "houston",
        
        "AMARILLO": "panhandle",
        "LUBBOCK": "panhandle",
        "PLAINVIEW": "panhandle",
        "PAMPA": "panhandle"
    }
    
    # Check possible city columns
    possible_city_cols = ['CITY', 'TOWN', 'MUNICIPALITY', 'GIS_CITY']
    for col in possible_city_cols:
        if col in data and not pd.isna(data[col]):
            city = str(data[col]).upper()
            if city in city_to_zone:
                return city_to_zone[city]
    
    # Try to extract zone from project name
    if 'NAME' in data:
        project_name = str(data['NAME']).upper()
        for zone in ['NORTH', 'WEST', 'SOUTH', 'HOUSTON', 'PANHANDLE']:
            if zone in project_name:
                return zone.lower()
    
    # Try to extract zone from location
    if 'LOCATION' in data and data['LOCATION']:
        location = str(data['LOCATION']).upper()
        
        # Check if any zone name is in the location
        for zone in ['NORTH', 'WEST', 'SOUTH', 'HOUSTON', 'PANHANDLE']:
            if zone in location:
                return zone.lower()
                
        # Look for specific region indicators in location
        if any(k in location for k in ['DALLAS', 'FORT WORTH', 'DFW', 'DENTON']):
            return 'north'
        elif any(k in location for k in ['MIDLAND', 'ODESSA', 'PERMIAN']):
            return 'west'
        elif any(k in location for k in ['SAN ANTONIO', 'CORPUS', 'LAREDO', 'MCALLEN', 'RGV']):
            return 'south'
        elif any(k in location for k in ['HOUSTON', 'HARRIS', 'GALVESTON', 'BEAUMONT']):
            return 'houston'
        elif any(k in location for k in ['AMARILLO', 'LUBBOCK', 'PANHANDLE']):
            return 'panhandle'
    
    # If we still can't determine, try using county to make a rough estimate
    if 'COUNTY' in data and data['COUNTY']:
        county = str(data['COUNTY']).upper()
        
        # These are simplified associations for common counties
        if county in ['BRAZORIA', 'HARRIS', 'MONTGOMERY', 'GALVESTON', 'FORT BEND']:
            return 'houston'
        elif county in ['GLASSCOCK', 'MIDLAND', 'ECTOR', 'PECOS', 'REEVES', 'WARD']:
            return 'west'
        elif county in ['DALLAS', 'TARRANT', 'COLLIN', 'DENTON']:
            return 'north'
        elif county in ['BEXAR', 'NUECES', 'CAMERON', 'HIDALGO', 'WEBB']:
            return 'south'
        elif county in ['LUBBOCK', 'POTTER', 'RANDALL', 'DEAF SMITH']:
            return 'panhandle'
    
    # If all else fails, randomly select a zone with higher probability for west and north
    # (as these tend to have more renewable projects)
    return np.random.choice(['north', 'west', 'south', 'houston', 'panhandle'], 
                          p=[0.25, 0.3, 0.2, 0.15, 0.1])

def determine_energy_type(data):
    """
    Determine the energy type for a project.
    
    Args:
        data: Dictionary or DataFrame row with project information
        
    Returns:
        String representing the energy type
    """
    # Check possible columns that might contain energy type information
    possible_type_cols = [
        'FUEL_TYPE', 'TECHNOLOGY', 'RESOURCE_TYPE', 'GIS_FUEL_TYPE',
        'GENERATION_TYPE', 'ENERGY_SOURCE', 'POWER_TYPE', 'TYPE',
        'GIS_RESOURCE_TYPE', 'RESOURCE', 'GIS_TECH_TYPE'
    ]
    
    # Try all possible columns
    for col in possible_type_cols:
        if col in data and not pd.isna(data[col]):
            type_str = str(data[col]).upper()
            
            # Special handling for ERCOT codes
            if type_str in ['SOL', 'PV']:
                return 'SOLAR'
            elif type_str in ['WND', 'WT']:
                return 'WIND'
            elif type_str in ['GAS', 'CC', 'CT']:
                return 'GAS'
            elif type_str in ['BESS', 'ESR', 'ESS']:
                return 'BATTERY'
            
            # Check for solar
            if any(keyword in type_str for keyword in ["SOLAR", "PV", "PHOTOVOLTAIC"]):
                return "SOLAR"
            
            # Check for wind
            if any(keyword in type_str for keyword in ["WIND", "TURBINE", "WTG"]):
                return "WIND"
            
            # Check for gas/thermal
            if any(keyword in type_str for keyword in ["GAS", "NATURAL", "COMBINED CYCLE", "COMBUSTION", "THERMAL", "CC", "CT", "NGCC"]):
                return "GAS"
            
            # Check for battery/storage
            if any(keyword in type_str for keyword in ["BATTERY", "STORAGE", "BESS", "ESS", "ESR"]):
                return "BATTERY"
    
    # Try to determine from project name
    if 'NAME' in data and not pd.isna(data['NAME']):
        name = str(data['NAME']).upper()
        
        if any(keyword in name for keyword in ["SOLAR", "PV", "PHOTOVOLTAIC"]):
            return "SOLAR"
        
        if any(keyword in name for keyword in ["WIND", "TURBINE", "WTG"]):
            return "WIND"
        
        if any(keyword in name for keyword in ["GAS", "NATURAL", "COMBINED CYCLE", "COMBUSTION", "THERMAL", "CC", "CT", "NGCC"]):
            return "GAS"
        
        if any(keyword in name for keyword in ["BATTERY", "STORAGE", "BESS", "ESS", "ESR"]):
            return "BATTERY"
    
    # Default to OTHER if we can't determine
    return "OTHER"

def process_interconnection_data(df):
    """
    Process the interconnection queue data into GeoJSON format.
    
    Args:
        df: DataFrame with interconnection queue data
        
    Returns:
        Dictionary with GeoJSON features and summary data
    """
    print("Processing interconnection queue data...")
    
    # For ERCOT GIS Report format, we now know the actual column layout
    # Check if this looks like the GIS Report format
    if '19INR0041' in df.columns:  # This is a column name from the first row of our observed data
        print("Processing ERCOT GIS Report format")
        
        # Map the specific columns we've observed in the GIS Report
        id_col = df.columns[0]  # First column contains the INR number (project ID)
        name_col = df.columns[1]  # Second column contains the project name
        status_col = df.columns[2]  # Third column contains the study phase/status
        
        # Find capacity column - it's a numeric column that often has values like 321.2
        capacity_cols = []
        for col in df.columns:
            if col not in [id_col, name_col, status_col] and pd.api.types.is_numeric_dtype(df[col].dtype):
                capacity_cols.append(col)
        
        if capacity_cols:
            print(f"Identified capacity columns: {capacity_cols}")
            capacity_col = capacity_cols[0]  # Take the first numeric column for capacity
        else:
            capacity_col = None
            print("Could not identify capacity column")
        
        # Find fuel type column - often contains values like SOL, WND, GAS
        resource_cols = [col for col in df.columns if 'SOL' in df[col].values or 'WND' in df[col].values]
        if resource_cols:
            print(f"Identified resource columns: {resource_cols}")
            fuel_type_col = resource_cols[0]
        else:
            fuel_type_col = None
            print("Could not identify resource/fuel type column")
        
        # Find location/county columns
        location_col = df.columns[4] if len(df.columns) > 4 else None  # Fifth column often contains POI location
        county_col = df.columns[5] if len(df.columns) > 5 else None    # Sixth column often contains county
        
        print(f"Using columns: ID={id_col}, Name={name_col}, Status={status_col}, Capacity={capacity_col}")
        print(f"Location columns: Location={location_col}, County={county_col}, FuelType={fuel_type_col}")
    else:
        # Look for specific columns in the RPT file
        # Common column names in ERCOT interconnection queue reports
        possible_id_cols = ['GIS_PROJECT_CODE', 'PROJECT_CODE', 'ID', 'NUMBER', 'PROJECT_ID', 'INTERCONNECTION_ID']
        possible_name_cols = ['GIS_PROJECT_NAME', 'PROJECT_NAME', 'NAME', 'PROJECT']
        possible_capacity_cols = ['GIS_SUMMER_MW', 'SUMMER_MW', 'MW', 'CAPACITY', 'SIZE', 'GIS_MW', 'CAPACITY_MW', 'INSTALLED_CAPACITY']
        possible_status_cols = ['GIS_STATUS', 'STATUS', 'PROJECT_STATUS', 'STATE']
        
        # Identify key columns
        id_col = next((col for col in possible_id_cols if col in df.columns), None)
        name_col = next((col for col in possible_name_cols if col in df.columns), None)
        capacity_col = next((col for col in possible_capacity_cols if col in df.columns), None)
        status_col = next((col for col in possible_status_cols if col in df.columns), None)
        
        # Find latitude and longitude columns if they exist
        lat_col = next((col for col in df.columns if 'LATITUDE' in col or 'LAT' == col), None)
        lon_col = next((col for col in df.columns if 'LONGITUDE' in col or 'LON' == col or 'LONG' == col), None)
        
        # Find location/county columns
        location_col = next((col for col in df.columns if 'LOCATION' in col or 'SITE' in col or 'POI' in col), None)
        county_col = next((col for col in df.columns if 'COUNTY' in col), None)
        fuel_type_col = next((col for col in df.columns if 'FUEL' in col or 'RESOURCE' in col or 'TYPE' in col), None)
        
        print(f"Using columns: ID={id_col}, Name={name_col}, Capacity={capacity_col}, Status={status_col}")
        print(f"Location columns: Location={location_col}, County={county_col}, FuelType={fuel_type_col}")
    
    # Prepare for GeoJSON
    features = []
    
    # Summary data by zone and energy type
    zone_capacity = {zone.lower(): {energy_type.lower(): 0 for energy_type in ENERGY_TYPES} 
                    for zone in ERCOT_ZONES}
    
    # Process each project
    for idx, row in df.iterrows():
        # Get project ID
        if id_col and not pd.isna(row[id_col]):
            project_id = str(row[id_col])
        else:
            project_id = f"Project-{idx}"
        
        # Get project name
        if name_col and not pd.isna(row[name_col]):
            project_name = str(row[name_col])
        else:
            project_name = f"Project {project_id}"
        
        # Get capacity in MW
        capacity = 0
        if capacity_col:
            try:
                if not pd.isna(row[capacity_col]):
                    capacity = float(row[capacity_col])
            except (ValueError, TypeError):
                # Try to extract number from string
                capacity_str = str(row[capacity_col])
                numbers = re.findall(r'\d+\.?\d*', capacity_str)
                capacity = float(numbers[0]) if numbers else 0
        
        # Get status
        if status_col and not pd.isna(row[status_col]):
            status = str(row[status_col])
        else:
            status = "Unknown"
        
        # Get location information
        location_str = None
        if location_col and not pd.isna(row[location_col]):
            location_str = str(row[location_col])
        
        county_str = None
        if county_col and not pd.isna(row[county_col]):
            county_str = str(row[county_col])
        
        # Get fuel type
        fuel_type = None
        if fuel_type_col and not pd.isna(row[fuel_type_col]):
            fuel_type = str(row[fuel_type_col])
        
        # Determine zone based on county or location
        if county_str:
            zone_input = {'COUNTY': county_str}
            if location_str:
                zone_input['LOCATION'] = location_str
            zone = determine_zone(zone_input)
        else:
            zone_input = {}
            if location_str:
                zone_input['LOCATION'] = location_str
            zone = determine_zone(zone_input)
        
        # Determine energy type
        energy_type_input = {}
        if fuel_type:
            energy_type_input['FUEL_TYPE'] = fuel_type
        if name_col:
            energy_type_input['NAME'] = project_name
        energy_type = determine_energy_type(energy_type_input)
        
        # Extract coordinates using county and location info
        coords = extract_coordinates(location_str, None, None)
        
        # Skip projects without valid coordinates
        if coords is None:
            continue
        
        # Create a GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coords
            },
            "properties": {
                "id": project_id,
                "name": project_name,
                "capacity": capacity,
                "status": status,
                "zone": zone,
                "energy_type": energy_type.lower()
            }
        }
        
        features.append(feature)
        
        # Add to zone capacity summary
        zone_capacity[zone][energy_type.lower()] += capacity
    
    print(f"Processed {len(features)} projects")
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Create summary data
    summary = {
        "zone_capacity": zone_capacity,
        "total_projects": len(features),
        "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return {
        "geojson": geojson,
        "summary": summary
    }

def create_sample_data():
    """Create sample interconnection queue data for testing."""
    print("Creating sample interconnection queue data...")
    
    # Define energy types and their typical capacity ranges in MW
    energy_configs = {
        "SOLAR": {"min_cap": 50, "max_cap": 500, "count": 40},
        "WIND": {"min_cap": 100, "max_cap": 600, "count": 30},
        "GAS": {"min_cap": 200, "max_cap": 1000, "count": 15},
        "BATTERY": {"min_cap": 20, "max_cap": 300, "count": 25},
        "OTHER": {"min_cap": 10, "max_cap": 200, "count": 10}
    }
    
    # Zone distribution (roughly matching Texas geography)
    zones = {
        "north": {"lat_range": [32.0, 34.0], "lon_range": [-98.5, -96.0]},
        "west": {"lat_range": [30.5, 33.0], "lon_range": [-103.0, -100.0]},
        "south": {"lat_range": [27.0, 30.0], "lon_range": [-100.0, -97.0]},
        "houston": {"lat_range": [29.0, 30.5], "lon_range": [-96.5, -94.5]},
        "panhandle": {"lat_range": [34.5, 36.5], "lon_range": [-103.0, -100.0]}
    }
    
    features = []
    zone_capacity = {zone: {energy_type.lower(): 0 for energy_type in ENERGY_TYPES} 
                    for zone in zones.keys()}
    
    project_id = 1000
    
    # Generate projects for each energy type
    for energy_type, config in energy_configs.items():
        for _ in range(config["count"]):
            # Select a random zone
            zone = np.random.choice(list(zones.keys()))
            zone_info = zones[zone]
            
            # Generate random coordinates within the zone
            lat = np.random.uniform(zone_info["lat_range"][0], zone_info["lat_range"][1])
            lon = np.random.uniform(zone_info["lon_range"][0], zone_info["lon_range"][1])
            
            # Generate random capacity
            capacity = np.random.uniform(config["min_cap"], config["max_cap"])
            
            # Create a sample project name
            project_name = f"{energy_type.title()} Project {project_id}"
            
            # Select a random status
            status = np.random.choice([
                "Active", "Planned", "Under Construction", 
                "Approved", "Pending", "In Review"
            ])
            
            # Create feature
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "id": str(project_id),
                    "name": project_name,
                    "capacity": round(capacity, 1),
                    "status": status,
                    "zone": zone,
                    "energy_type": energy_type.lower()
                }
            }
            
            features.append(feature)
            
            # Add to zone capacity
            zone_capacity[zone][energy_type.lower()] += round(capacity, 1)
            
            project_id += 1
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Create summary data
    summary = {
        "zone_capacity": zone_capacity,
        "total_projects": len(features),
        "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return {
        "geojson": geojson,
        "summary": summary
    }

def save_interconnection_data(data, output_dir=OUTPUT_DIR):
    """
    Save the processed interconnection data to JSON files.
    
    Args:
        data: Dictionary with GeoJSON and summary data
        output_dir: Directory to save the files
    """
    print("Saving interconnection data...")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save GeoJSON
    geojson_path = os.path.join(output_dir, "interconnection_projects.geojson")
    with open(geojson_path, 'w') as f:
        json.dump(data["geojson"], f, indent=2)
    
    # Save summary data
    summary_path = os.path.join(output_dir, "interconnection_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(data["summary"], f, indent=2)
    
    print(f"Saved interconnection data to {geojson_path} and {summary_path}")

def main():
    """Main function to process interconnection queue data."""
    print("Starting interconnection queue data processing...")
    
    # Check if Interconnection directory exists
    if not os.path.exists(INTERCONNECTION_DIR):
        print(f"Warning: Interconnection directory not found at {INTERCONNECTION_DIR}")
        print("Creating sample data instead.")
        data = create_sample_data()
    else:
        # Check for the specific GIS Report file
        gis_report_file = "RPT.00015933.0000000000000000.20250303.162032467.GIS_Report_February2025.xlsx"
        gis_report_path = os.path.join(INTERCONNECTION_DIR, gis_report_file)
        
        if os.path.exists(gis_report_path):
            print(f"Found GIS Report file: {gis_report_file}")
            
            # Direct load of the large generators sheet with explicit parameters
            try:
                print("Loading data from 'Project Details - Large Gen' sheet...")
                df_large = pd.read_excel(
                    gis_report_path, 
                    sheet_name='Project Details - Large Gen',
                    header=30,  # Header row is 30
                    skiprows=34  # Skip to row 35 (0-indexed)
                )
                print(f"Successfully loaded {len(df_large)} rows from large generators sheet")
                
                # Clean column names
                df_large.columns = [str(col).strip().upper().replace(' ', '_') if col is not None else f"COL_{i}" 
                                    for i, col in enumerate(df_large.columns)]
                
                print(f"Column names: {df_large.columns.tolist()[:10]}")
                print(f"First row sample: {df_large.iloc[0].to_dict()}")
                
                # Try to also load small generators sheet
                try:
                    print("Loading data from 'Project Details - Small Gen' sheet...")
                    df_small = pd.read_excel(
                        gis_report_path, 
                        sheet_name='Project Details - Small Gen',
                        header=30,
                        skiprows=34
                    )
                    print(f"Successfully loaded {len(df_small)} rows from small generators sheet")
                    
                    # Clean column names for small generators
                    df_small.columns = [str(col).strip().upper().replace(' ', '_') if col is not None else f"COL_{i}" 
                                        for i, col in enumerate(df_small.columns)]
                    
                    # Combine the dataframes
                    df = pd.concat([df_large, df_small], ignore_index=True)
                    print(f"Combined data contains {len(df)} rows")
                except Exception as e:
                    print(f"Could not load small generators sheet: {e}")
                    df = df_large
                
                # Map columns to standard names
                column_mapping = {
                    'INR': 'PROJECT_ID',
                    'PROJECT_NAME': 'NAME',
                    'RESOURCE_TYPE': 'FUEL_TYPE',
                    'TECHNOLOGY_TYPE': 'TECHNOLOGY',
                    'GIM_STUDY_PHASE': 'STATUS',
                    'SUMMER_MW': 'CAPACITY',
                    'POI_LOCATION': 'LOCATION'
                }
                
                # Apply column mapping
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns:
                        print(f"Mapping column {old_col} to {new_col}")
                        df[new_col] = df[old_col]
                
                # Process the data
                data = process_interconnection_data(df)
                
            except Exception as e:
                print(f"Error loading GIS Report file: {e}")
                print("Creating sample data instead.")
                data = create_sample_data()
        else:
            # Look for other RPT files
            rpt_files = [f for f in os.listdir(INTERCONNECTION_DIR) 
                        if f.endswith(('.xlsx', '.xls', '.csv')) and ('RPT' in f or 'rpt' in f)]
            
            # If no RPT files, look for any Excel or CSV files
            if not rpt_files:
                rpt_files = [f for f in os.listdir(INTERCONNECTION_DIR) 
                            if f.endswith(('.xlsx', '.xls', '.csv'))]
            
            if rpt_files:
                # Use the first matching file
                rpt_file = rpt_files[0]
                rpt_path = os.path.join(INTERCONNECTION_DIR, rpt_file)
                print(f"Found file: {rpt_file}")
                
                # Load and process data
                df = load_interconnection_data(rpt_path)
                data = process_interconnection_data(df)
            else:
                print(f"No suitable files found in {INTERCONNECTION_DIR}. Creating sample data instead.")
                data = create_sample_data()
    
    # Save the data
    save_interconnection_data(data)
    
    print("Interconnection queue data processing completed.")

if __name__ == "__main__":
    main() 