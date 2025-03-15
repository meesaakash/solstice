import os
import pandas as pd
from datetime import datetime

class CarbonIntensityTracker:
    """
    Tracks carbon intensity data for different geographic locations.
    
    This class is responsible for loading and providing carbon intensity data
    for specific geographic locations and time periods.
    """
    
    # Mapping of location codes to carbon intensity file names
    CI_FILES = {
        'TX': 'TX_NG_&_avgCI.csv',  # Texas
        'NY': 'NY_NG_&_avgCI.csv',  # New York
        'CA': 'CA_NG_&_avgCI.csv',  # California
        'AZ': 'AZ_NG_&_avgCI.csv',  # Arizona
        'IL': 'IL_NG_&_avgCI.csv',  # Illinois
        'GA': 'GA_NG_&_avgCI.csv',  # Georgia
        'WA': 'WA_NG_&_avgCI.csv',  # Washington
        'VA': 'VA_NG_&_avgCI.csv'   # Virginia
    }
    
    # Mapping of location codes to grid regions for ERCOT specificity
    GRID_REGIONS = {
        'TX': 'ERCO',  # ERCOT for Texas
        'NY': 'NYIS',  # New York ISO
        'CA': 'CISO',  # California ISO
        'AZ': 'AZPS',  # Arizona Public Service
        'IL': 'MISO',  # Midcontinent ISO
        'GA': 'SOCO',  # Southern Company
        'WA': 'BPAT',  # Bonneville Power Administration
        'VA': 'PJM'    # PJM Interconnection
    }
    
    def __init__(self, location_code):
        """
        Initialize with a specific location.
        
        Args:
            location_code: Two-letter location code (e.g., 'TX', 'NY')
        """
        self.location_code = location_code
        self.grid_region = self.GRID_REGIONS.get(location_code, location_code)
        
        # Load carbon intensity data
        self.carbon_data = self._load_carbon_data()
        
        # Calculate statistics for forecasting
        self._calculate_statistics()
    
    def _load_carbon_data(self):
        """
        Load carbon intensity data from CSV file.
        
        Returns:
            Pandas DataFrame with carbon intensity data
        """
        # Determine the file to load based on the grid region if available, or fall back to location code
        ci_file = None
        
        # First try with the grid region
        if self.grid_region in self.CI_FILES:
            ci_file = self.CI_FILES[self.grid_region]
        # Then try with the location code
        elif self.location_code in self.CI_FILES:
            ci_file = self.CI_FILES[self.location_code]
        
        if not ci_file:
            # Use a default file if no match is found
            ci_file = 'TX_NG_&_avgCI.csv'  # Default to Texas
        
        # Get full path to the carbon intensity file
        ci_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'CarbonIntensity', ci_file
        )
        
        if not os.path.exists(ci_path):
            raise FileNotFoundError(f"Carbon intensity file not found: {ci_path}")
        
        # Load the CSV file
        df = pd.read_csv(ci_path)
        
        # Process the data to have a datetime index
        # Assuming the first column is a datetime string
        df['timestamp'] = pd.to_datetime(df.iloc[:, 0])
        
        # Simplify to keep only timestamp and carbon intensity
        # Assuming the carbon intensity is in a column named 'avgCI' or similar
        ci_column = [col for col in df.columns if 'CI' in col or 'carbon' in col.lower()]
        
        if ci_column:
            df = df[['timestamp', ci_column[0]]]
            df.columns = ['timestamp', 'carbon_intensity']
        else:
            # If no CI column found, use the second column (adjust if needed)
            df = df[['timestamp', df.columns[1]]]
            df.columns = ['timestamp', 'carbon_intensity']
        
        return df
    
    def _calculate_statistics(self):
        """
        Calculate statistical measures for carbon intensity.
        """
        self.min_ci = self.carbon_data['carbon_intensity'].min()
        self.max_ci = self.carbon_data['carbon_intensity'].max()
        self.mean_ci = self.carbon_data['carbon_intensity'].mean()
        self.median_ci = self.carbon_data['carbon_intensity'].median()
        
        # Calculate hourly averages for forecasting
        self.carbon_data['hour'] = self.carbon_data['timestamp'].dt.hour
        self.hourly_avg = self.carbon_data.groupby('hour')['carbon_intensity'].mean()
    
    def get_carbon_intensity(self, timestamp):
        """
        Get carbon intensity for a specific timestamp.
        
        Args:
            timestamp: Datetime object representing the time
            
        Returns:
            Carbon intensity value (g CO2/kWh)
        """
        # Find the closest timestamp in the data
        matching_data = self.carbon_data[
            (self.carbon_data['timestamp'].dt.date == timestamp.date()) &
            (self.carbon_data['timestamp'].dt.hour == timestamp.hour)
        ]
        
        if len(matching_data) > 0:
            # Return the average if multiple matches
            return matching_data['carbon_intensity'].mean()
        else:
            # If no exact match, estimate based on the hour of day
            hour = timestamp.hour
            if hour in self.hourly_avg.index:
                return self.hourly_avg[hour]
            else:
                # Fallback to the mean
                return self.mean_ci
    
    def forecast_carbon_intensity(self, timestamp, days_ahead=0, hours_ahead=1):
        """
        Forecast carbon intensity for a future timestamp.
        
        Args:
            timestamp: Base datetime object
            days_ahead: Number of days ahead to forecast
            hours_ahead: Number of hours ahead to forecast
            
        Returns:
            Forecasted carbon intensity value (g CO2/kWh)
        """
        # This is a simple forecast based on historical averages
        # For more accurate forecasts, a time series model could be used
        
        target_datetime = timestamp.replace(
            day=timestamp.day + days_ahead,
            hour=(timestamp.hour + hours_ahead) % 24
        )
        
        # Get the hour of the target time
        target_hour = target_datetime.hour
        
        # Use the hourly average for that hour
        if target_hour in self.hourly_avg.index:
            forecast = self.hourly_avg[target_hour]
        else:
            forecast = self.mean_ci
        
        return forecast
    
    def get_best_time_window(self, start_time, window_hours=24, duration_hours=4):
        """
        Find the best time window with lowest carbon intensity.
        
        Args:
            start_time: Starting datetime for the search window
            window_hours: Total hours to consider for the search
            duration_hours: Required consecutive hours with low carbon intensity
            
        Returns:
            Tuple of (best_start_time, average_carbon_intensity)
        """
        best_ci = float('inf')
        best_start = None
        
        # Get all hours in the window
        hours = []
        current_time = start_time
        for _ in range(window_hours):
            hours.append(current_time.hour)
            current_time = current_time.replace(hour=(current_time.hour + 1) % 24)
        
        # Find the best consecutive window
        for i in range(window_hours - duration_hours + 1):
            window_hours = hours[i:i+duration_hours]
            window_ci = [self.hourly_avg.get(h, self.mean_ci) for h in window_hours]
            avg_ci = sum(window_ci) / len(window_ci)
            
            if avg_ci < best_ci:
                best_ci = avg_ci
                best_start = i
        
        if best_start is not None:
            best_time = start_time.replace(hour=(start_time.hour + best_start) % 24)
            return (best_time, best_ci)
        else:
            return (start_time, self.mean_ci) 