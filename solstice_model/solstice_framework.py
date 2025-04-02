import os
import sys
import json
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any

# Import local modules
import datacenter
from dc_config import *  # Import default configuration
from utils.location_manager import LocationManager
from utils.cooling_manager import CoolingManager
from utils.energy_analyzer import EnergyAnalyzer
from utils.carbon_intensity import CarbonIntensityTracker

class SolsticeDatacenterModel:
    """
    A scalable framework for datacenter energy modeling with geographic location awareness,
    multiple cooling system options, and carbon intensity tracking.
    
    This class serves as the main interface for simulating datacenter energy consumption
    across different geographic locations, considering various datacenter configurations,
    workload patterns, and cooling systems.
    """
    
    def __init__(self, 
                 config: Optional[Dict] = None,
                 config_file: Optional[str] = None,
                 location: str = 'TX',  # Default to Texas
                 cooling_type: str = 'air',  # 'air' or 'water'
                 datacenter_capacity_mw: float = 1.0,
                 simulation_start_date: str = '2023-01-01',
                 simulation_days: int = 7,
                 cooling_efficiency_factor: float = 1.0,
                 pue_overhead: float = 1.1):  # Add PUE overhead parameter
        """
        Initialize the datacenter model with the specified configuration.
        
        Args:
            config: Optional custom configuration dictionary. If None, uses default config.
            config_file: Optional path to a configuration file (JSON or YAML)
            location: Geographic location code (e.g., 'TX' for Texas, 'NY' for New York)
            cooling_type: Type of cooling system ('air' or 'water')
            datacenter_capacity_mw: Datacenter capacity in megawatts
            simulation_start_date: Start date for the simulation in YYYY-MM-DD format
            simulation_days: Number of days to simulate
            cooling_efficiency_factor: Factor to adjust cooling system efficiency (default: 1.0)
            pue_overhead: Additional PUE overhead factor for miscellaneous power usage (default: 1.1)
        """
        # First check if we have a config file
        if config_file:
            config = self._load_config_from_file(config_file)
        
        self.config = self._initialize_config(config)
        self.location = location
        self.cooling_type = cooling_type
        self.datacenter_capacity_mw = datacenter_capacity_mw
        self.cooling_efficiency_factor = cooling_efficiency_factor
        self.pue_overhead = pue_overhead  # Store the PUE overhead factor
        
        # Parse the start date and calculate end date
        self.start_date = datetime.strptime(simulation_start_date, '%Y-%m-%d')
        self.end_date = self.start_date + timedelta(days=simulation_days)
        
        # Initialize managers
        self.location_manager = LocationManager(location)
        self.cooling_manager = CoolingManager(cooling_type, self.config)
        self.energy_analyzer = EnergyAnalyzer()
        self.carbon_tracker = CarbonIntensityTracker(location)
        
        # Initialize the datacenter model
        self._initialize_datacenter()
        
        # Storage for simulation results
        self.simulation_results = {
            'timestamps': [],
            'datacenter_energy': [],
            'cooling_energy': [],
            'total_energy': [],
            'carbon_intensity': [],
            'carbon_emissions': [],
            'water_usage': [],
            'ambient_temperature': [],
            'workload': []
        }
    
    def _load_config_from_file(self, config_file: str) -> Dict:
        """
        Load configuration from a JSON or YAML file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        # Determine file type from extension
        if config_file.endswith('.json'):
            with open(config_file, 'r') as f:
                return json.load(f)
        elif config_file.endswith(('.yaml', '.yml')):
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_file}")
    
    def _initialize_config(self, config: Optional[Dict]) -> Dict:
        """
        Initialize configuration with provided or default values.
        
        Args:
            config: Optional custom configuration
            
        Returns:
            Complete configuration dictionary
        """
        if config is None:
            # Use default configuration from dc_config.py
            return {
                'NUM_RACKS': NUM_RACKS,
                'NUM_ROWS': NUM_ROWS,
                'NUM_RACKS_PER_ROW': NUM_RACKS_PER_ROW,
                'MAX_W_PER_RACK': MAX_W_PER_RACK,
                'RACK_SUPPLY_APPROACH_TEMP_LIST': RACK_SUPPLY_APPROACH_TEMP_LIST,
                'RACK_RETURN_APPROACH_TEMP_LIST': RACK_RETURN_APPROACH_TEMP_LIST,
                'CPUS_PER_RACK': CPUS_PER_RACK,
                'RACK_CPU_CONFIG': RACK_CPU_CONFIG,
                # Add other configuration parameters here
            }
        return config
    
    def _initialize_datacenter(self):
        """
        Initialize the datacenter model with the configured parameters.
        """
        # Create datacenter model based on config
        self.dc_model = datacenter.DataCenter_ITModel(
            num_racks=self.config['NUM_RACKS'],
            rack_supply_approach_temp_list=self.config['RACK_SUPPLY_APPROACH_TEMP_LIST'],
            rack_CPU_config=self.config['RACK_CPU_CONFIG'],
            max_W_per_rack=self.config['MAX_W_PER_RACK'],
            DC_ITModel_config=self  # Pass self as config
        )
        
        # Scale the datacenter based on capacity
        self.scaling_factor = self.datacenter_capacity_mw * 1e6 / self.dc_model.total_DC_full_load
        print(f"Datacenter scaling factor: {self.scaling_factor:.2f}")
    
    def run_simulation(self, workload_pattern: Optional[List[float]] = None) -> Dict:
        """
        Run the datacenter simulation over the specified time period.
        
        Args:
            workload_pattern: Optional custom workload pattern. If None, uses a default pattern.
            
        Returns:
            Simulation results as a dictionary
        """
        # Generate timestamps for simulation
        current_date = self.start_date
        time_delta = timedelta(hours=1)  # 1-hour steps
        timestamps = []
        
        while current_date < self.end_date:
            timestamps.append(current_date)
            current_date += time_delta
        
        # Get workload pattern (if not provided, use a default pattern)
        if workload_pattern is None:
            # Generate a default daily pattern with higher during day, lower at night
            day_pattern = []
            for hour in range(24):
                # Higher load during business hours (8am-8pm)
                if 8 <= hour < 20:
                    load = 0.7 + 0.2 * np.sin(np.pi * (hour - 8) / 12)
                else:
                    load = 0.4 + 0.1 * np.sin(np.pi * (hour - 20) / 12)
                day_pattern.append(load)
            
            # Repeat the pattern for each day
            simulation_hours = len(timestamps)
            workload_pattern = []
            for i in range(simulation_hours):
                hour_of_day = i % 24
                workload_pattern.append(day_pattern[hour_of_day])
        
        # Initialize results storage
        self.simulation_results = {
            'timestamps': timestamps,
            'datacenter_energy': [],
            'cooling_energy': [],
            'total_energy': [],
            'carbon_intensity': [],
            'carbon_emissions': [],
            'water_usage': [],
            'ambient_temperature': [],
            'workload': workload_pattern
        }
        
        # Run simulation for each timestamp
        for i, timestamp in enumerate(timestamps):
            # Get time-specific data
            hour_of_day = timestamp.hour
            day_of_year = timestamp.timetuple().tm_yday
            
            # Get weather data for the timestamp
            ambient_temp = self.location_manager.get_temperature(timestamp)
            self.simulation_results['ambient_temperature'].append(ambient_temp)
            
            # Get carbon intensity data
            carbon_intensity = self.carbon_tracker.get_carbon_intensity(timestamp)
            self.simulation_results['carbon_intensity'].append(carbon_intensity)
            
            # Compute datacenter energy based on current workload
            current_workload = workload_pattern[i]
            rack_loads = [current_workload * 100] * self.config['NUM_RACKS']  # Convert to percentage
            
            # Simulate CRAC setpoint based on ambient temperature
            # For simplicity, we use a linear function based on outside temperature
            crac_setpoint = min(22.0, max(16.0, 18.0 + (ambient_temp - 20.0) * 0.2))
            
            # Calculate datacenter IT load and outlet temperatures
            rack_cpu_power, rack_itfan_power, rack_outlet_temps = self.dc_model.compute_datacenter_IT_load_outlet_temp(
                ITE_load_pct_list=rack_loads,
                CRAC_setpoint=crac_setpoint
            )
            
            # Calculate total IT power and apply scaling factor
            it_power = (sum(rack_cpu_power) + sum(rack_itfan_power)) * self.scaling_factor
            self.simulation_results['datacenter_energy'].append(it_power)
            
            # Calculate CRAC return temperature
            avg_crac_return_temp = datacenter.calculate_avg_CRAC_return_temp(
                rack_return_approach_temp_list=self.config['RACK_RETURN_APPROACH_TEMP_LIST'],
                rackwise_outlet_temp=rack_outlet_temps
            )
            
            # Calculate HVAC power
            crac_fan_power, ct_fan_power, crac_cooling_load, chiller_power, cw_pump_power, ct_pump_power = \
                datacenter.calculate_HVAC_power(
                    CRAC_setpoint=crac_setpoint,
                    avg_CRAC_return_temp=avg_crac_return_temp,
                    ambient_temp=ambient_temp,
                    data_center_full_load=self.dc_model.total_DC_full_load * self.scaling_factor,  # Apply scaling factor
                    DC_Config=self
                )
            
            # Calculate cooling power based on cooling type and apply scaling factor
            if self.cooling_type == 'air':
                cooling_power = (crac_fan_power + chiller_power) * self.cooling_efficiency_factor * self.scaling_factor
                water_usage = 0.0  # No water usage for air cooling
            else:  # water cooling
                cooling_power = (crac_fan_power + ct_fan_power + chiller_power + 
                                cw_pump_power + ct_pump_power) * self.cooling_efficiency_factor * self.scaling_factor
                
                # Update cooling tower water parameters for water usage calculation
                self.dc_model.hot_water_temp = avg_crac_return_temp
                self.dc_model.cold_water_temp = crac_setpoint
                self.dc_model.wet_bulb_temp = self.location_manager.get_wet_bulb_temperature(timestamp)
                
                # Calculate water usage and apply scaling factor
                water_usage = self.dc_model.calculate_cooling_tower_water_usage() * self.scaling_factor
            
            self.simulation_results['cooling_energy'].append(cooling_power)
            self.simulation_results['water_usage'].append(water_usage)
            
            # Calculate total energy including PUE overhead
            total_energy = (it_power + cooling_power) * self.pue_overhead
            self.simulation_results['total_energy'].append(total_energy)
            
            # Calculate carbon emissions
            carbon_emissions = total_energy * carbon_intensity / 1000000  # Convert to tons of CO2
            self.simulation_results['carbon_emissions'].append(carbon_emissions)
        
        return self.simulation_results
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """
        Get the simulation results as a pandas DataFrame.
        
        Returns:
            Pandas DataFrame with simulation results
        """
        # Convert timestamp objects to strings
        results = self.simulation_results.copy()
        results['timestamps'] = [t.strftime('%Y-%m-%d %H:%M:%S') for t in results['timestamps']]
        
        return pd.DataFrame(results)
    
    def save_results_to_csv(self, filename: str) -> None:
        """
        Save the simulation results to a CSV file.
        
        Args:
            filename: Output CSV filename
        """
        df = self.get_results_dataframe()
        df.to_csv(filename, index=False)
    
    def save_results_to_json(self, filename: str) -> None:
        """
        Save the simulation results to a JSON file.
        
        Args:
            filename: Output JSON filename
        """
        df = self.get_results_dataframe()
        df.to_json(filename, orient='records', indent=2)
    
    def plot_energy_consumption(self, save_path: Optional[str] = None):
        """
        Plot the energy consumption over time.
        
        Args:
            save_path: Optional path to save the plot. If None, displays the plot.
        """
        self.energy_analyzer.plot_energy_consumption(
            self.simulation_results, 
            self.cooling_type,
            self.location,
            save_path
        )
    
    def plot_carbon_emissions(self, save_path: Optional[str] = None):
        """
        Plot the carbon emissions over time.
        
        Args:
            save_path: Optional path to save the plot. If None, displays the plot.
        """
        self.energy_analyzer.plot_carbon_emissions(
            self.simulation_results,
            self.location,
            save_path
        )
        
    def query(self, query_text: str) -> Dict[str, Any]:
        """
        Process a natural language query about the datacenter model and return results.
        This method is designed to be compatible with future LLM integration.
        
        Args:
            query_text: Natural language query text
            
        Returns:
            Dictionary with query results
        """
        # This is a placeholder for future LLM integration
        # For now, we'll implement some basic keyword-based queries
        query_text = query_text.lower()
        
        results = {}
        
        # Ensure we have simulation results
        if not any(self.simulation_results['datacenter_energy']):
            return {"error": "No simulation data available. Please run a simulation first."}
        
        # Get simulation data as dataframe
        df = self.get_results_dataframe()
        
        # Parse query
        if 'average' in query_text or 'mean' in query_text:
            if 'energy' in query_text or 'power' in query_text:
                results['average_datacenter_energy'] = df['datacenter_energy'].mean()
                results['average_cooling_energy'] = df['cooling_energy'].mean()
                results['average_total_energy'] = df['total_energy'].mean()
                
            if 'carbon' in query_text or 'emissions' in query_text:
                results['average_carbon_intensity'] = df['carbon_intensity'].mean()
                results['average_carbon_emissions'] = df['carbon_emissions'].mean()
                results['total_carbon_emissions'] = df['carbon_emissions'].sum()
                
            if 'water' in query_text:
                results['average_water_usage'] = df['water_usage'].mean()
                results['total_water_usage'] = df['water_usage'].sum()
                
        elif 'peak' in query_text or 'maximum' in query_text or 'max' in query_text:
            if 'energy' in query_text or 'power' in query_text:
                results['peak_datacenter_energy'] = df['datacenter_energy'].max()
                results['peak_cooling_energy'] = df['cooling_energy'].max()
                results['peak_total_energy'] = df['total_energy'].max()
                
            if 'carbon' in query_text or 'emissions' in query_text:
                results['peak_carbon_intensity'] = df['carbon_intensity'].max()
                results['peak_carbon_emissions'] = df['carbon_emissions'].max()
                
            if 'water' in query_text:
                results['peak_water_usage'] = df['water_usage'].max()
                
        elif 'total' in query_text or 'sum' in query_text:
            if 'energy' in query_text or 'power' in query_text:
                results['total_datacenter_energy'] = df['datacenter_energy'].sum()
                results['total_cooling_energy'] = df['cooling_energy'].sum()
                results['total_energy'] = df['total_energy'].sum()
                
            if 'carbon' in query_text or 'emissions' in query_text:
                results['total_carbon_emissions'] = df['carbon_emissions'].sum()
                
            if 'water' in query_text:
                results['total_water_usage'] = df['water_usage'].sum()
                
        elif 'compare' in query_text:
            # This is a placeholder for more complex comparisons
            results['message'] = "Detailed comparisons will be implemented in future versions."
            
        else:
            # Return a summary of all key metrics
            results = {
                'total_energy_kwh': df['total_energy'].sum() / 1000,  # Convert to kWh
                'average_power_kw': df['total_energy'].mean() / 1000,  # Convert to kW
                'peak_power_kw': df['total_energy'].max() / 1000,      # Convert to kW
                'total_carbon_emissions_tons': df['carbon_emissions'].sum(),
                'energy_breakdown': {
                    'datacenter_percent': df['datacenter_energy'].sum() / df['total_energy'].sum() * 100,
                    'cooling_percent': df['cooling_energy'].sum() / df['total_energy'].sum() * 100
                },
                'simulation_duration_hours': len(df),
                'location': self.location,
                'cooling_type': self.cooling_type,
                'datacenter_capacity_mw': self.datacenter_capacity_mw
            }
            
            if self.cooling_type == 'water':
                results['total_water_usage_liters'] = df['water_usage'].sum()
        
        return results
    
    def create_config_template(self, output_file: str = 'datacenter_config_template.json') -> None:
        """
        Create a configuration template file that can be modified and used as input.
        
        Args:
            output_file: Output filename for the template
        """
        # Create a template configuration with all the current settings
        template = {
            'datacenter': {
                'num_racks': self.config['NUM_RACKS'],
                'num_rows': self.config['NUM_ROWS'],
                'num_racks_per_row': self.config['NUM_RACKS_PER_ROW'],
                'max_w_per_rack': self.config['MAX_W_PER_RACK'],
                'cpus_per_rack': self.config['CPUS_PER_RACK']
            },
            'cooling': {
                'type': self.cooling_type,
                'parameters': self.cooling_manager.get_cooling_parameters()
            },
            'location': {
                'code': self.location,
                'info': self.location_manager.get_location_info()
            },
            'simulation': {
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'days': (self.end_date - self.start_date).days,
                'capacity_mw': self.datacenter_capacity_mw
            }
        }
        
        # Save the template
        with open(output_file, 'w') as f:
            if output_file.endswith('.json'):
                json.dump(template, f, indent=2)
            elif output_file.endswith(('.yaml', '.yml')):
                yaml.dump(template, f, default_flow_style=False)
            else:
                # Default to JSON
                json.dump(template, f, indent=2)
    
    def load_research_paper_model(self, model_data: Dict) -> None:
        """
        Load a datacenter model specification from research paper data.
        
        Args:
            model_data: Dictionary with model specifications
        """
        # Update configuration based on research paper model
        if 'server_specs' in model_data:
            # Example: Update CPU configuration based on server specs from paper
            if 'cpu_idle_power' in model_data['server_specs'] and 'cpu_full_load_power' in model_data['server_specs']:
                # Update all racks with the new CPU configuration
                idle_pwr = model_data['server_specs']['cpu_idle_power']
                full_load_pwr = model_data['server_specs']['cpu_full_load_power']
                
                new_rack_cpu_config = []
                for _ in range(self.config['NUM_RACKS']):
                    new_rack_cpu_config.append([
                        {'full_load_pwr': full_load_pwr, 'idle_pwr': idle_pwr}
                        for _ in range(self.config['CPUS_PER_RACK'])
                    ])
                
                self.config['RACK_CPU_CONFIG'] = new_rack_cpu_config
        
        if 'cooling_parameters' in model_data:
            # Example: Update cooling parameters
            cooling_params = model_data['cooling_parameters']
            if 'type' in cooling_params:
                self.cooling_type = cooling_params['type']
                # Reinitialize the cooling manager
                self.cooling_manager = CoolingManager(self.cooling_type, self.config)
        
        # Reinitialize the datacenter model with updated configuration
        self._initialize_datacenter()
    
    # Forward the required attributes from DC_Config class for compatibility with datacenter.py
    @property
    def C_AIR(self):
        return C_AIR
    
    @property
    def RHO_AIR(self):
        return RHO_AIR
    
    @property
    def CRAC_SUPPLY_AIR_FLOW_RATE_pu(self):
        return CRAC_SUPPLY_AIR_FLOW_RATE_pu
    
    @property
    def CRAC_REFRENCE_AIR_FLOW_RATE_pu(self):
        return CRAC_REFRENCE_AIR_FLOW_RATE_pu
    
    @property
    def CRAC_FAN_REF_P(self):
        return CRAC_FAN_REF_P
    
    @property
    def CT_FAN_REF_P(self):
        return CT_FAN_REF_P
    
    @property
    def CT_REFRENCE_AIR_FLOW_RATE(self):
        return CT_REFRENCE_AIR_FLOW_RATE
    
    @property
    def CT_PRESSURE_DROP(self):
        return CT_PRESSURE_DROP
    
    @property
    def CT_WATER_FLOW_RATE(self):
        return CT_WATER_FLOW_RATE
    
    @property
    def CT_PUMP_EFFICIENCY(self):
        return CT_PUMP_EFFICIENCY
    
    @property
    def CW_PRESSURE_DROP(self):
        return CW_PRESSURE_DROP
    
    @property
    def CW_WATER_FLOW_RATE(self):
        return CW_WATER_FLOW_RATE
    
    @property
    def CW_PUMP_EFFICIENCY(self):
        return CW_PUMP_EFFICIENCY
        
    # Add missing CPU properties
    @property
    def CPU_POWER_RATIO_UB(self):
        return CPU_POWER_RATIO_UB
    
    @property
    def CPU_POWER_RATIO_LB(self):
        return CPU_POWER_RATIO_LB
    
    @property
    def IT_FAN_AIRFLOW_RATIO_UB(self):
        return IT_FAN_AIRFLOW_RATIO_UB
    
    @property
    def IT_FAN_AIRFLOW_RATIO_LB(self):
        return IT_FAN_AIRFLOW_RATIO_LB
    
    @property
    def IT_FAN_FULL_LOAD_V(self):
        return IT_FAN_FULL_LOAD_V
    
    @property
    def ITFAN_REF_V_RATIO(self):
        return ITFAN_REF_V_RATIO
    
    @property
    def ITFAN_REF_P(self):
        return ITFAN_REF_P
    
    @property
    def INLET_TEMP_RANGE(self):
        return INLET_TEMP_RANGE
    
    @property
    def HP_PROLIANT(self):
        return HP_PROLIANT


# Example usage
if __name__ == "__main__":
    # Create a model for a datacenter in Texas with air cooling
    model = SolsticeDatacenterModel(
        location='TX',
        cooling_type='air',
        datacenter_capacity_mw=1.0,
        simulation_start_date='2023-06-01',
        simulation_days=7,
        cooling_efficiency_factor=0.85,  # 85% efficiency
        pue_overhead=1.1  # Add PUE overhead
    )
    
    # Run the simulation
    results = model.run_simulation()
    
    # Save and visualize results
    model.save_results_to_csv('tx_datacenter_results.csv')
    model.plot_energy_consumption('tx_energy_consumption.png')
    model.plot_carbon_emissions('tx_carbon_emissions.png')
    
    # Print summary statistics
    df = model.get_results_dataframe()
    print(f"Average Energy Consumption: {df['total_energy'].mean() / 1000:.2f} kW")
    print(f"Peak Energy Consumption: {df['total_energy'].max() / 1000:.2f} kW")
    print(f"Total Carbon Emissions: {df['carbon_emissions'].sum():.2f} tons CO2")
    if model.cooling_type == 'water':
        print(f"Total Water Usage: {df['water_usage'].sum():.2f} liters")
        
    # Example of querying the model
    query_result = model.query("What is the average energy consumption?")
    print("\nQuery Result:")
    for key, value in query_result.items():
        print(f"{key}: {value}")
        
    # Create a configuration template for future use
    model.create_config_template() 