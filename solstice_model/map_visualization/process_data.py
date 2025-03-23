#!/usr/bin/env python3
"""
Data Processing Script for ERCOT Visualization

This script processes ERCOT data files and datacenter simulation results into
JSON format that can be used by the web visualization.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Paths to data files
ERCOT_DATA_DIR = "../data/ERCOT_data"
COMPARISON_RESULTS_DIR = "../comparison_results"
OUTPUT_DIR = "data"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_generation_data(filepath):
    """Loads ERCOT solar and wind generation data."""
    print(f"Loading generation data from {filepath}")
    df = pd.read_csv(filepath, skiprows=4)
    df.columns = [
        "UTC_Timestamp", "Local_Begin", "Local_End", "Local_Date", "Hour_Number",
        "Solar_Gen_MW", "Solar_HSL_MW", "North_Wind_Gen_MW", "System_Wind_Gen_MW", 
        "System_Wind_HSL_MW", "South_Houston_Wind_Gen_MW", "West_Wind_Gen_MW"
    ]
    df["UTC_Timestamp"] = pd.to_datetime(df["UTC_Timestamp"])
    return df

def load_lmp_data(filepath):
    """Loads ERCOT real-time locational marginal prices (LMP) data."""
    print(f"Loading LMP data from {filepath}")
    df = pd.read_csv(filepath, skiprows=4)
    df.columns = [
        "UTC_Timestamp", "Local_Begin", "Local_End", "Local_Date", "Hour_Number",
        "Bus_Avg_LMP", "Houston_LMP", "Hub_Avg_LMP", "North_LMP", "Panhandle_LMP", 
        "South_LMP", "West_LMP"
    ]
    df["UTC_Timestamp"] = pd.to_datetime(df["UTC_Timestamp"])
    return df

def load_load_data(filepath):
    """Loads ERCOT load data by region."""
    print(f"Loading load data from {filepath}")
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()
    # Ensure datetime column is properly formatted
    if "UTC_Timestamp" in df.columns:
        df["UTC_Timestamp"] = pd.to_datetime(df["UTC_Timestamp"])
    elif "Date" in df.columns:
        df["UTC_Timestamp"] = pd.to_datetime(df["Date"])
    return df

def load_temperature_data(filepath):
    """Loads temperature data by region."""
    print(f"Loading temperature data from {filepath}")
    df = pd.read_csv(filepath)
    # Assuming the temperature data has a timestamp and region-specific temperatures
    return df

def process_gen_data(df):
    """Process generation data into region-specific format."""
    print("Processing generation data...")
    
    # Group by date and aggregate to daily values
    df['date'] = df['UTC_Timestamp'].dt.date
    daily_data = df.groupby('date').agg({
        'Solar_Gen_MW': 'mean',
        'North_Wind_Gen_MW': 'mean',
        'South_Houston_Wind_Gen_MW': 'mean', 
        'West_Wind_Gen_MW': 'mean'
    }).reset_index()
    
    # Calculate the total renewable generation for each region
    result = []
    
    for _, row in daily_data.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        
        # Create an entry for each date
        data_entry = {
            'date': date_str,
            'renewableGen': {
                'north': {
                    'value': round(row['North_Wind_Gen_MW'], 2),
                    'unit': 'MW'
                },
                'west': {
                    'value': round(row['West_Wind_Gen_MW'], 2),
                    'unit': 'MW'
                },
                'south': {
                    'value': round(row['South_Houston_Wind_Gen_MW'] / 2, 2),  # Split between south and houston
                    'unit': 'MW'
                },
                'houston': {
                    'value': round(row['South_Houston_Wind_Gen_MW'] / 2, 2),  # Split between south and houston
                    'unit': 'MW'
                },
                'panhandle': {
                    'value': round(row['North_Wind_Gen_MW'] * 0.3, 2),  # Estimate for panhandle
                    'unit': 'MW'
                }
            }
        }
        
        result.append(data_entry)
    
    return result

def process_lmp_data(df):
    """Process LMP data into region-specific format."""
    print("Processing LMP data...")
    
    # Group by date and aggregate to daily values
    df['date'] = df['UTC_Timestamp'].dt.date
    daily_data = df.groupby('date').agg({
        'Hub_Avg_LMP': 'mean',
        'Houston_LMP': 'mean',
        'North_LMP': 'mean',
        'Panhandle_LMP': 'mean',
        'South_LMP': 'mean',
        'West_LMP': 'mean'
    }).reset_index()
    
    result = []
    
    for _, row in daily_data.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        
        data_entry = {
            'date': date_str,
            'lmp': {
                'north': {
                    'value': round(row['North_LMP'], 2),
                    'unit': '$/MWh'
                },
                'west': {
                    'value': round(row['West_LMP'], 2),
                    'unit': '$/MWh'
                },
                'south': {
                    'value': round(row['South_LMP'], 2),
                    'unit': '$/MWh'
                },
                'houston': {
                    'value': round(row['Houston_LMP'], 2),
                    'unit': '$/MWh'
                },
                'panhandle': {
                    'value': round(row['Panhandle_LMP'], 2),
                    'unit': '$/MWh'
                }
            }
        }
        
        result.append(data_entry)
    
    return result

def process_load_data(df):
    """Process load data into region-specific format."""
    print("Processing load data...")
    
    # Check if we have region-specific columns
    # If not, we'll create synthetic data based on available info
    
    result = []
    
    # Group by date and aggregate to daily values
    if "UTC_Timestamp" in df.columns:
        df['date'] = df['UTC_Timestamp'].dt.date
    else:
        # Assume we have a date column
        df['date'] = pd.to_datetime(df['Date']).dt.date
    
    # If we have region-specific columns, use them
    # Otherwise, create synthetic data
    if all(col in df.columns for col in ['North_Load', 'South_Load', 'West_Load', 'Houston_Load', 'Panhandle_Load']):
        daily_data = df.groupby('date').agg({
            'North_Load': 'mean',
            'South_Load': 'mean',
            'West_Load': 'mean',
            'Houston_Load': 'mean',
            'Panhandle_Load': 'mean'
        }).reset_index()
        
        for _, row in daily_data.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            
            data_entry = {
                'date': date_str,
                'energyConsumption': {
                    'north': {
                        'value': round(row['North_Load'] * 24, 2),  # Convert MW to MWh
                        'unit': 'MWh'
                    },
                    'west': {
                        'value': round(row['West_Load'] * 24, 2),
                        'unit': 'MWh'
                    },
                    'south': {
                        'value': round(row['South_Load'] * 24, 2),
                        'unit': 'MWh'
                    },
                    'houston': {
                        'value': round(row['Houston_Load'] * 24, 2),
                        'unit': 'MWh'
                    },
                    'panhandle': {
                        'value': round(row['Panhandle_Load'] * 24, 2),
                        'unit': 'MWh'
                    }
                }
            }
            
            result.append(data_entry)
    else:
        # Create synthetic data based on total load
        if "ERCOT" in df.columns:
            load_col = "ERCOT"
        else:
            # Use the first numeric column after date
            for col in df.columns:
                if col != 'date' and pd.api.types.is_numeric_dtype(df[col]):
                    load_col = col
                    break
        
        daily_data = df.groupby('date').agg({
            load_col: 'mean'
        }).reset_index()
        
        # Distribution percentages for each region (estimates)
        distribution = {
            'north': 0.35,
            'west': 0.15,
            'south': 0.20,
            'houston': 0.25,
            'panhandle': 0.05
        }
        
        for _, row in daily_data.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            total_load = row[load_col]
            
            data_entry = {
                'date': date_str,
                'energyConsumption': {
                    'north': {
                        'value': round(total_load * distribution['north'] * 24, 2),
                        'unit': 'MWh'
                    },
                    'west': {
                        'value': round(total_load * distribution['west'] * 24, 2),
                        'unit': 'MWh'
                    },
                    'south': {
                        'value': round(total_load * distribution['south'] * 24, 2),
                        'unit': 'MWh'
                    },
                    'houston': {
                        'value': round(total_load * distribution['houston'] * 24, 2),
                        'unit': 'MWh'
                    },
                    'panhandle': {
                        'value': round(total_load * distribution['panhandle'] * 24, 2),
                        'unit': 'MWh'
                    }
                }
            }
            
            result.append(data_entry)
    
    return result

def process_temperature_data(df):
    """Process temperature data into region-specific format."""
    print("Processing temperature data...")
    
    # If we don't have temperature data, create synthetic data
    # based on typical Texas temperatures by region
    
    # Create a date range for the past month
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    date_range = [start_date + timedelta(days=i) for i in range(31)]
    
    result = []
    
    # Average temperatures by region for Texas
    base_temps = {
        'north': 78,
        'west': 85,
        'south': 82,
        'houston': 84,
        'panhandle': 75
    }
    
    for date in date_range:
        date_str = date.strftime('%Y-%m-%d')
        
        # Add some random variation to temperatures
        random_var = np.random.uniform(-5, 5, 5)
        
        data_entry = {
            'date': date_str,
            'temperature': {
                'north': {
                    'value': round(base_temps['north'] + random_var[0], 1),
                    'unit': '°F'
                },
                'west': {
                    'value': round(base_temps['west'] + random_var[1], 1),
                    'unit': '°F'
                },
                'south': {
                    'value': round(base_temps['south'] + random_var[2], 1),
                    'unit': '°F'
                },
                'houston': {
                    'value': round(base_temps['houston'] + random_var[3], 1),
                    'unit': '°F'
                },
                'panhandle': {
                    'value': round(base_temps['panhandle'] + random_var[4], 1),
                    'unit': '°F'
                }
            }
        }
        
        result.append(data_entry)
    
    return result

def merge_all_data(gen_data, lmp_data, load_data, temp_data):
    """Merge all processed data into a single dataset by date."""
    print("Merging all data...")
    
    # Create a dictionary with date as key
    merged_data = {}
    
    # Add generation data
    for item in gen_data:
        date = item['date']
        if date not in merged_data:
            merged_data[date] = {}
        merged_data[date]['renewableGen'] = item['renewableGen']
    
    # Add LMP data
    for item in lmp_data:
        date = item['date']
        if date not in merged_data:
            merged_data[date] = {}
        merged_data[date]['lmp'] = item['lmp']
    
    # Add load data
    for item in load_data:
        date = item['date']
        if date not in merged_data:
            merged_data[date] = {}
        merged_data[date]['energyConsumption'] = item['energyConsumption']
    
    # Add temperature data
    for item in temp_data:
        date = item['date']
        if date not in merged_data:
            merged_data[date] = {}
        merged_data[date]['temperature'] = item['temperature']
    
    # Convert back to list format
    result = []
    for date, data in merged_data.items():
        entry = {'date': date}
        entry.update(data)
        result.append(entry)
    
    # Sort by date
    result.sort(key=lambda x: x['date'])
    
    return result

def create_daily_data_files(merged_data):
    """Create individual JSON files for each date."""
    print("Creating daily data files...")
    
    for entry in merged_data:
        date = entry['date']
        filename = os.path.join(OUTPUT_DIR, f"data_{date}.json")
        
        with open(filename, 'w') as f:
            json.dump(entry, f, indent=2)
    
    print(f"Created {len(merged_data)} daily data files in {OUTPUT_DIR}")

def create_index_file(merged_data):
    """Create an index file with all dates."""
    print("Creating index file...")
    
    dates = [entry['date'] for entry in merged_data]
    
    index = {
        'dates': dates,
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(os.path.join(OUTPUT_DIR, 'index.json'), 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"Created index file with {len(dates)} dates")

def main():
    """Main function to process all data."""
    print("Starting data processing...")
    
    # Find and process generation data
    gen_filepath = os.path.join(ERCOT_DATA_DIR, "ercot_gen_sun-wnd_5min_2025Q1.csv")
    gen_data = None
    if os.path.exists(gen_filepath):
        gen_df = load_generation_data(gen_filepath)
        gen_data = process_gen_data(gen_df)
    else:
        print(f"Warning: Generation data file not found at {gen_filepath}")
        # Create some sample data
        gen_data = []
    
    # Find and process LMP data
    lmp_filepath = os.path.join(ERCOT_DATA_DIR, "ercot_lmp_rt_15min_hubs_2025Q1.csv")
    lmp_data = None
    if os.path.exists(lmp_filepath):
        lmp_df = load_lmp_data(lmp_filepath)
        lmp_data = process_lmp_data(lmp_df)
    else:
        print(f"Warning: LMP data file not found at {lmp_filepath}")
        lmp_data = []
    
    # Find and process load data
    load_filepath = os.path.join(ERCOT_DATA_DIR, "ercot_load_act_hr_2025.csv")
    load_data = None
    if os.path.exists(load_filepath):
        load_df = load_load_data(load_filepath)
        load_data = process_load_data(load_df)
    else:
        print(f"Warning: Load data file not found at {load_filepath}")
        load_data = []
    
    # Process temperature data (synthetic for now)
    temp_data = process_temperature_data(None)
    
    # Merge all data
    merged_data = merge_all_data(gen_data, lmp_data, load_data, temp_data)
    
    # Create output files
    create_daily_data_files(merged_data)
    create_index_file(merged_data)
    
    print("Data processing completed.")

if __name__ == "__main__":
    main() 