import os
import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple, Union, Any
import openai

# Import the Solstice datacenter model
from solstice_framework import SolsticeDatacenterModel

class DatacenterQueryProcessor:
    """
    Process natural language queries about datacenter modeling using ChatGPT,
    extract configuration parameters, and use them to run the SolsticeDatacenterModel.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the query processor with OpenAI API key.
        
        Args:
            api_key: OpenAI API key. If None, will try to get from OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided either directly or through OPENAI_API_KEY environment variable")
        
        openai.api_key = self.api_key
        
        # Default configuration parameters
        self.default_params = {
            'location': 'TX',
            'cooling_type': 'air',
            'datacenter_capacity_mw': 1.0,
            'simulation_start_date': '2023-01-01',
            'simulation_days': 7,
            'cooling_efficiency_factor': 1.0,
            'pue_overhead': 1.1
        }
        
        # Define parameter mappings for different ways users might refer to parameters
        self.param_mappings = {
            'location': ['location', 'region', 'area', 'place', 'where', 'geographic', 'state', 'country'],
            'cooling_type': ['cooling', 'cooled', 'cooling system', 'cooling method', 'heat removal'],
            'datacenter_capacity_mw': ['capacity', 'size', 'power', 'megawatt', 'mw', 'megawatts'],
            'simulation_start_date': ['start date', 'begin date', 'starting on', 'starting from'],
            'simulation_days': ['days', 'duration', 'period', 'how long', 'time period', 'simulation length'],
            'cooling_efficiency_factor': ['cooling efficiency', 'efficiency factor', 'efficiency of cooling'],
            'pue_overhead': ['pue', 'power usage effectiveness', 'overhead']
        }
        
        # State code mappings (abbreviated)
        self.state_code_mappings = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
            'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
            'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
            'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
            'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
            'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
            'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
            'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
        }
    
    def parse_query(self, query: str) -> Dict:
        """
        Parse a natural language query using ChatGPT to extract datacenter configuration parameters.
        
        Args:
            query: Natural language query about datacenter modeling
            
        Returns:
            Dictionary of extracted parameters
        """
        # Define the prompt for ChatGPT
        prompt = f"""
        You are an AI assistant that helps extract datacenter configuration parameters from natural language queries.
        Extract the following parameters (if mentioned) from the query:
        
        1. Location (state or country code, e.g., 'TX' for Texas)
        2. Cooling type ('air' or 'water')
        3. Datacenter capacity in megawatts (MW). If the capacity is specified in gigawatts (GW), convert it to megawatts (1 GW = 1000 MW)
        4. Simulation start date (in format YYYY-MM-DD)
        5. Simulation duration in days
        6. Cooling efficiency factor (a number between 0 and 1, default is 1.0)
        7. PUE overhead (a number typically between 1.0 and 2.0, default is 1.1)
        
        For any parameter that is not explicitly mentioned, don't include it in your response.
        
        The query is: "{query}"
        
        Respond in the following JSON format:
        {{
            "location": "extracted location code",
            "cooling_type": "extracted cooling type",
            "datacenter_capacity_mw": extracted capacity value (in megawatts),
            "simulation_start_date": "extracted start date",
            "simulation_days": extracted number of days,
            "cooling_efficiency_factor": extracted efficiency factor,
            "pue_overhead": extracted PUE value
        }}
        
        Only include parameters that were explicitly mentioned in the query.
        """
        
        # Call ChatGPT API
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",  # or appropriate model name
                messages=[
                    {"role": "system", "content": "You are a datacenter configuration parameter extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic outputs
                max_tokens=500
            )
            
            # Extract the response
            extracted_json_str = response.choices[0].message['content'].strip()
            
            # Find JSON in the response if it's not a clean JSON response
            import re
            json_match = re.search(r'```json\n(.*?)\n```', extracted_json_str, re.DOTALL)
            if json_match:
                extracted_json_str = json_match.group(1)
            
            # In case the assistant just prints {} with parameter values
            json_match = re.search(r'{\s*".*?}\s*', extracted_json_str, re.DOTALL)
            if json_match:
                extracted_json_str = json_match.group(0)
            
            extracted_params = json.loads(extracted_json_str)
            return extracted_params
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Fall back to a rule-based approach if API call fails
            return self._fallback_parsing(query)
    
    def _fallback_parsing(self, query: str) -> Dict:
        """
        Fallback method for parsing query if API call fails.
        Uses simple rule-based parsing.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary of extracted parameters
        """
        extracted_params = {}
        query_lower = query.lower()
        
        # Check for location
        for state_name, state_code in self.state_code_mappings.items():
            if state_name in query_lower:
                extracted_params['location'] = state_code
                break
        
        # Check for cooling type
        if any(term in query_lower for term in ['water cool', 'liquid cool', 'water-cool']):
            extracted_params['cooling_type'] = 'water'
        elif any(term in query_lower for term in ['air cool', 'air-cool']):
            extracted_params['cooling_type'] = 'air'
        
        # Extract datacenter capacity with unit conversion
        import re
        
        # Look for gigawatt (GW) specifications first
        gw_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:gw|gigawatt)', query_lower)
        if gw_match:
            # Convert GW to MW (1 GW = 1000 MW)
            gw_value = float(gw_match.group(1))
            extracted_params['datacenter_capacity_mw'] = gw_value * 1000
        else:
            # Try to find megawatt specifications
            mw_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:mw|megawatt)', query_lower)
            if mw_match:
                extracted_params['datacenter_capacity_mw'] = float(mw_match.group(1))
            else:
                # Try to find kilowatt specifications
                kw_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kw|kilowatt)', query_lower)
                if kw_match:
                    # Convert kW to MW (1 MW = 1000 kW)
                    kw_value = float(kw_match.group(1))
                    extracted_params['datacenter_capacity_mw'] = kw_value / 1000
        
        # Check for cooling efficiency 
        efficiency_match = re.search(r'(\d+(?:\.\d+)?)%\s*(?:cooling efficiency|efficiency)', query_lower)
        if efficiency_match:
            efficiency_value = float(efficiency_match.group(1)) / 100  # Convert percentage to decimal
            extracted_params['cooling_efficiency_factor'] = efficiency_value
        
        # Check for PUE
        pue_match = re.search(r'pue\s*(?:of|:|\s)\s*(\d+(?:\.\d+)?)', query_lower)
        if pue_match:
            extracted_params['pue_overhead'] = float(pue_match.group(1))
        
        return extracted_params
    
    def build_datacenter_model(self, query: str) -> Tuple[SolsticeDatacenterModel, Dict]:
        """
        Process a natural language query, extract parameters, and build a datacenter model.
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (SolsticeDatacenterModel, extracted_params)
        """
        # Parse the query to extract parameters
        extracted_params = self.parse_query(query)
        
        # Merge with default parameters
        model_params = self.default_params.copy()
        model_params.update(extracted_params)
        
        # Print the parameters being used
        print("\n=== Datacenter Model Configuration ===")
        for param, value in model_params.items():
            print(f"{param}: {value}")
        print("=======================================\n")
        
        # Create and return the datacenter model
        model = SolsticeDatacenterModel(
            location=model_params['location'],
            cooling_type=model_params['cooling_type'],
            datacenter_capacity_mw=model_params['datacenter_capacity_mw'],
            simulation_start_date=model_params['simulation_start_date'],
            simulation_days=model_params['simulation_days'],
            cooling_efficiency_factor=model_params['cooling_efficiency_factor'],
            pue_overhead=model_params['pue_overhead']
        )
        
        return model, model_params
    
    def process_query(self, query: str, run_simulation: bool = True, save_results: bool = False) -> Dict:
        """
        Process a natural language query, build a datacenter model, and optionally run a simulation.
        
        Args:
            query: Natural language query
            run_simulation: Whether to run the simulation
            save_results: Whether to save the simulation results
            
        Returns:
            Dictionary with results
        """
        # Build the datacenter model
        model, params = self.build_datacenter_model(query)
        
        results = {
            "query": query,
            "extracted_parameters": params,
            "message": f"Created datacenter model with {params['datacenter_capacity_mw']} MW capacity, {params['cooling_type']} cooling in {params['location']}"
        }
        
        # Run the simulation if requested
        if run_simulation:
            print("Running datacenter simulation...")
            simulation_results = model.run_simulation()
            
            # Get summary statistics
            df = model.get_results_dataframe()
            
            summary = {
                "avg_energy_consumption_kw": df['total_energy'].mean() / 1000,
                "peak_energy_consumption_kw": df['total_energy'].max() / 1000,
                "total_carbon_emissions_tons": df['carbon_emissions'].sum()
            }
            
            if params['cooling_type'] == 'water':
                summary["total_water_usage_liters"] = df['water_usage'].sum()
            
            results["simulation_summary"] = summary
            
            # Save results if requested
            if save_results:
                output_dir = f"results_{params['location']}_{params['cooling_type']}_{params['datacenter_capacity_mw']}MW"
                os.makedirs(output_dir, exist_ok=True)
                
                model.save_results_to_csv(f"{output_dir}/simulation_results.csv")
                model.plot_energy_consumption(f"{output_dir}/energy_consumption.png")
                model.plot_carbon_emissions(f"{output_dir}/carbon_emissions.png")
                
                results["output_directory"] = output_dir
        
        return results

def main():
    """Command-line interface for the datacenter query processor."""
    parser = argparse.ArgumentParser(description='Process natural language queries about datacenter modeling')
    parser.add_argument('query', type=str, help='Natural language query about datacenter modeling')
    parser.add_argument('--api-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    parser.add_argument('--no-sim', action='store_true', help='Skip running the simulation')
    parser.add_argument('--save', action='store_true', help='Save simulation results')
    
    args = parser.parse_args()
    
    processor = DatacenterQueryProcessor(api_key=args.api_key)
    results = processor.process_query(args.query, run_simulation=not args.no_sim, save_results=args.save)
    
    # Print results
    print("\n=== Query Results ===")
    print(f"Query: {results['query']}")
    print(f"Message: {results['message']}")
    
    if 'simulation_summary' in results:
        print("\n=== Simulation Summary ===")
        for key, value in results['simulation_summary'].items():
            print(f"{key}: {value:.2f}")
        
        if 'output_directory' in results:
            print(f"\nResults saved to: {results['output_directory']}")
    
    print("\nDone!")

if __name__ == "__main__":
    main() 