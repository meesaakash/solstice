import os
import csv
from datetime import datetime
import numpy as np
import pandas as pd
import psychrolib as psy

# Initialize psychrolib
psy.SetUnitSystem(psy.SI)

class LocationManager:
    """
    Manages location-specific data like weather and geographical information.
    
    This class is responsible for loading and providing weather data (temperature,
    humidity, etc.) for a specific geographic location.
    """
    
    # Mapping of location codes to full names for display
    LOCATION_NAMES = {
        'TX': 'Texas',
        'NY': 'New York',
        'CA': 'California',
        'AZ': 'Arizona',
        'IL': 'Illinois',
        'GA': 'Georgia',
        'WA': 'Washington',
        'VA': 'Virginia'
    }
    
    # Mapping from location codes to EPW weather files
    WEATHER_FILES = {
        'TX': 'USA_TX_Dallas-Fort.Worth.epw',
        'NY': 'USA_NY_New.York-LaGuardia.epw',
        'CA': 'USA_CA_San.Jose-Mineta.epw',
        'AZ': 'USA_AZ_Phoenix-Sky.Harbor.epw',
        'IL': 'USA_IL_Chicago.OHare.epw',
        'GA': 'USA_GA_Atlanta-Hartsfield-Jackson.epw',
        'WA': 'USA_WA_Seattle-Tacoma.epw',
        'VA': 'USA_VA_Leesburg.Exec.epw'
    }
    
    def __init__(self, location_code):
        """
        Initialize with a specific location.
        
        Args:
            location_code: Two-letter location code (e.g., 'TX', 'NY')
        """
        self.location_code = location_code
        self.location_name = self.LOCATION_NAMES.get(location_code, f"Unknown ({location_code})")
        
        # Load weather data for this location
        self.weather_data = self._load_weather_data()
        
    def _load_weather_data(self):
        """
        Load weather data from the EPW file for the specified location.
        
        Returns:
            Pandas DataFrame with weather data
        """
        weather_file = self.WEATHER_FILES.get(self.location_code)
        if not weather_file:
            raise ValueError(f"No weather data available for location code: {self.location_code}")
        
        # Get full path to the weather file
        weather_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'Weather', weather_file
        )
        
        if not os.path.exists(weather_path):
            raise FileNotFoundError(f"Weather file not found: {weather_path}")
        
        # Parse the EPW file
        epw_data = []
        with open(weather_path, 'r') as f:
            epw_reader = csv.reader(f)
            # Skip header rows
            for _ in range(8):
                next(epw_reader)
            
            # Read data rows
            for row in epw_reader:
                if len(row) >= 35:  # EPW files have multiple columns
                    year = int(row[0])
                    month = int(row[1])
                    day = int(row[2])
                    hour = int(row[3]) - 1  # EPW hours are 1-24, convert to 0-23
                    
                    # Extract weather data
                    try:
                        dry_bulb_temp = float(row[6])  # Dry bulb temperature (°C)
                        rel_humidity = float(row[8])   # Relative humidity (%)
                        pressure = float(row[9])       # Atmospheric pressure (Pa)
                        
                        # Create timestamp and add data
                        timestamp = datetime(year, month, day, hour)
                        epw_data.append({
                            'timestamp': timestamp,
                            'temperature': dry_bulb_temp,
                            'humidity': rel_humidity,
                            'pressure': pressure
                        })
                    except (ValueError, IndexError):
                        # Skip rows with invalid data
                        continue
        
        # Convert to DataFrame
        df = pd.DataFrame(epw_data)
        
        # Calculate wet bulb temperature
        df['wet_bulb'] = df.apply(
            lambda row: psy.GetTWetBulbFromRelHum(
                row['temperature'], row['humidity']/100, row['pressure']
            ), 
            axis=1
        )
        
        return df
    
    def get_temperature(self, timestamp):
        """
        Get the temperature for a specific timestamp.
        
        Args:
            timestamp: Datetime object representing the time
            
        Returns:
            Temperature in Celsius
        """
        # Find the closest timestamp in the weather data
        # For simplicity, we're just matching the month, day, and hour
        matching_data = self.weather_data[
            (self.weather_data['timestamp'].dt.month == timestamp.month) &
            (self.weather_data['timestamp'].dt.day == timestamp.day) &
            (self.weather_data['timestamp'].dt.hour == timestamp.hour)
        ]
        
        if len(matching_data) > 0:
            # Return the average if multiple matches
            return matching_data['temperature'].mean()
        else:
            # If no exact match, use a default value based on the month
            month_data = self.weather_data[self.weather_data['timestamp'].dt.month == timestamp.month]
            if len(month_data) > 0:
                return month_data['temperature'].mean()
            else:
                # Fallback: return a reasonable default
                return 20.0  # 20°C as default
    
    def get_wet_bulb_temperature(self, timestamp):
        """
        Get the wet bulb temperature for a specific timestamp.
        
        Args:
            timestamp: Datetime object representing the time
            
        Returns:
            Wet bulb temperature in Celsius
        """
        # Find the closest timestamp in the weather data
        matching_data = self.weather_data[
            (self.weather_data['timestamp'].dt.month == timestamp.month) &
            (self.weather_data['timestamp'].dt.day == timestamp.day) &
            (self.weather_data['timestamp'].dt.hour == timestamp.hour)
        ]
        
        if len(matching_data) > 0:
            # Return the average if multiple matches
            return matching_data['wet_bulb'].mean()
        else:
            # If no exact match, use a default value based on the month
            month_data = self.weather_data[self.weather_data['timestamp'].dt.month == timestamp.month]
            if len(month_data) > 0:
                return month_data['wet_bulb'].mean()
            else:
                # Fallback: return a reasonable default
                return 15.0  # 15°C as default
    
    def get_humidity(self, timestamp):
        """
        Get the relative humidity for a specific timestamp.
        
        Args:
            timestamp: Datetime object representing the time
            
        Returns:
            Relative humidity (0-100%)
        """
        matching_data = self.weather_data[
            (self.weather_data['timestamp'].dt.month == timestamp.month) &
            (self.weather_data['timestamp'].dt.day == timestamp.day) &
            (self.weather_data['timestamp'].dt.hour == timestamp.hour)
        ]
        
        if len(matching_data) > 0:
            return matching_data['humidity'].mean()
        else:
            month_data = self.weather_data[self.weather_data['timestamp'].dt.month == timestamp.month]
            if len(month_data) > 0:
                return month_data['humidity'].mean()
            else:
                return 50.0  # 50% as default
    
    def get_location_info(self):
        """
        Get information about the current location.
        
        Returns:
            Dictionary with location information
        """
        return {
            'code': self.location_code,
            'name': self.location_name,
            'weather_file': self.WEATHER_FILES.get(self.location_code, 'None')
        } 