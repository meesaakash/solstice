class CoolingManager:
    """
    Manages different cooling systems for datacenter simulations.
    
    This class provides specialized calculations and parameters for different
    cooling system types (air-cooled, water-cooled, etc.).
    """
    
    # Cooling types and their efficiency factors
    COOLING_TYPES = {
        'air': {
            'name': 'Air-Cooled',
            'efficiency_factor': 1.0,  # Baseline efficiency
            'pue_range': (1.4, 1.8),   # Typical PUE range for air cooling
            'water_usage': 0.0,        # No direct water usage
            'description': 'Traditional air cooling with CRAC units and chillers'
        },
        'water': {
            'name': 'Water-Cooled',
            'efficiency_factor': 0.7,  # More efficient than air cooling
            'pue_range': (1.2, 1.5),   # Typical PUE range for water cooling
            'water_usage': 1.0,        # Baseline water usage
            'description': 'Water cooling with cooling towers'
        },
        'immersion': {
            'name': 'Immersion Cooling',
            'efficiency_factor': 0.5,  # Very efficient
            'pue_range': (1.05, 1.2),  # Very low PUE
            'water_usage': 0.3,        # Less water usage than traditional water cooling
            'description': 'Servers immersed in dielectric fluid'
        },
        'hybrid': {
            'name': 'Hybrid Cooling',
            'efficiency_factor': 0.8,  # Between air and water cooling
            'pue_range': (1.3, 1.6),   # Intermediate PUE
            'water_usage': 0.5,        # Half the water usage of water cooling
            'description': 'Combination of air and water cooling approaches'
        }
    }
    
    def __init__(self, cooling_type, config):
        """
        Initialize the cooling manager with a specific cooling type.
        
        Args:
            cooling_type: Type of cooling system ('air', 'water', 'immersion', 'hybrid')
            config: Configuration dictionary
        """
        if cooling_type not in self.COOLING_TYPES:
            cooling_type = 'air'  # Default to air cooling if type not recognized
            
        self.cooling_type = cooling_type
        self.cooling_info = self.COOLING_TYPES[cooling_type]
        self.config = config
        
        # Initialize cooling-specific parameters
        self._initialize_cooling_params()
    
    def _initialize_cooling_params(self):
        """
        Initialize cooling-specific parameters based on the selected cooling type.
        """
        if self.cooling_type == 'air':
            # Default air-cooling parameters
            self.coef_of_performance = 3.0  # COP for air-cooled chillers
            self.fan_power_factor = 1.0
            
        elif self.cooling_type == 'water':
            # Water-cooling specific parameters
            self.coef_of_performance = 5.0  # Higher COP for water-cooled chillers
            self.fan_power_factor = 0.7
            self.water_usage_factor = 1.0
            self.evaporation_rate = 0.05  # 5% evaporation rate
            
        elif self.cooling_type == 'immersion':
            # Immersion cooling specific parameters
            self.coef_of_performance = 7.0  # Very high COP for immersion cooling
            self.fan_power_factor = 0.3
            self.water_usage_factor = 0.3
            
        elif self.cooling_type == 'hybrid':
            # Hybrid cooling specific parameters
            self.coef_of_performance = 4.5  # Between air and water
            self.fan_power_factor = 0.8
            self.water_usage_factor = 0.5
    
    def get_cooling_parameters(self):
        """
        Get cooling system parameters.
        
        Returns:
            Dictionary with cooling system parameters
        """
        return {
            'type': self.cooling_type,
            'name': self.cooling_info['name'],
            'efficiency_factor': self.cooling_info['efficiency_factor'],
            'pue_range': self.cooling_info['pue_range'],
            'water_usage': self.cooling_info['water_usage'],
            'description': self.cooling_info['description'],
            'coef_of_performance': getattr(self, 'coef_of_performance', 3.0),
            'fan_power_factor': getattr(self, 'fan_power_factor', 1.0)
        }
    
    def calculate_pue(self, it_power, cooling_power, other_power=0):
        """
        Calculate Power Usage Effectiveness (PUE).
        
        Args:
            it_power: IT equipment power (servers, networking, etc.)
            cooling_power: Cooling system power
            other_power: Other datacenter power consumption (lighting, etc.)
            
        Returns:
            PUE value
        """
        total_power = it_power + cooling_power + other_power
        if it_power > 0:
            pue = total_power / it_power
        else:
            pue = 1.0  # Default if IT power is zero
            
        return pue
    
    def estimate_water_usage(self, heat_rejected, ambient_temp, humidity):
        """
        Estimate water usage for cooling.
        
        Args:
            heat_rejected: Heat energy to be removed (watts)
            ambient_temp: Ambient temperature (°C)
            humidity: Relative humidity (0-100%)
            
        Returns:
            Estimated water usage in liters
        """
        if self.cooling_type != 'water' and self.cooling_type != 'hybrid':
            return 0.0  # No water usage for non-water cooling
        
        # Base water usage calculation
        # About 1.8 liters of water per kWh of heat rejected is a typical value
        base_water_usage = heat_rejected * 1.8 / 1000  # Convert watts to kW
        
        # Adjust for temperature and humidity
        # Higher temperatures and lower humidity increase water usage
        temp_factor = 1.0 + max(0, (ambient_temp - 20) / 100)  # Increase usage by 1% per degree above 20°C
        humidity_factor = 1.0 - min(0.3, humidity / 100)  # Reduce usage by up to 30% at high humidity
        
        adjusted_usage = base_water_usage * temp_factor * humidity_factor
        
        # Apply cooling-specific factor
        return adjusted_usage * getattr(self, 'water_usage_factor', 1.0)
    
    def adjust_chiller_power(self, chiller_power, ambient_temp):
        """
        Adjust chiller power based on ambient temperature and cooling type.
        
        Args:
            chiller_power: Base chiller power calculation
            ambient_temp: Ambient temperature (°C)
            
        Returns:
            Adjusted chiller power
        """
        # Chillers are more efficient at lower temperatures
        temp_factor = 1.0 + max(0, (ambient_temp - 15) / 50)  # Increase by up to 50% at high temperatures
        
        # Apply cooling type efficiency factor
        efficiency_factor = self.cooling_info['efficiency_factor']
        
        return chiller_power * temp_factor * efficiency_factor 