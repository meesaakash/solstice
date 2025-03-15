#!/usr/bin/env python3
"""
Example script for using the SolsticeDatacenterModel with an LLM-based query interface.

This script demonstrates how to:
1. Run a datacenter simulation
2. Process natural language queries about the simulation results
3. Structure the responses in a way that could be integrated with an LLM API

This is a simplified example of how you could integrate the SolsticeDatacenterModel
with an LLM system for text-to-query functionality.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add parent directory to path to import the model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solstice_framework import SolsticeDatacenterModel

# Set up output directory
OUTPUT_DIR = 'llm_interface'
os.makedirs(OUTPUT_DIR, exist_ok=True)

class LLMQueryInterface:
    """
    A simulated LLM interface for natural language queries to the datacenter model.
    
    This class demonstrates how you might structure a real LLM interface
    in the future. It processes natural language queries and routes them
    to the appropriate datacenter model method.
    """
    
    def __init__(self):
        """Initialize the LLM query interface."""
        self.models = {}  # Storage for multiple datacenter models
        self.active_model = None  # Currently active model
        
        # Example prompt templates for LLM integration
        self.prompt_templates = {
            'query': (
                "You are a datacenter energy analysis assistant. "
                "The user has asked: '{query}' "
                "Based on the datacenter simulation data, provide a concise response "
                "with relevant metrics and insights."
            ),
            'compare': (
                "You are a datacenter energy analysis assistant. "
                "The user wants to compare {item1} and {item2}. "
                "Based on the simulation data, provide a comparison of key metrics "
                "and explain the differences."
            )
        }
    
    def create_model(self, model_id, **model_params):
        """
        Create a new datacenter model with the given parameters.
        
        Args:
            model_id: Identifier for the model
            **model_params: Parameters for the SolsticeDatacenterModel
        """
        print(f"Creating datacenter model '{model_id}'...")
        
        # Create the model
        model = SolsticeDatacenterModel(**model_params)
        
        # Store the model
        self.models[model_id] = {
            'model': model,
            'params': model_params,
            'has_data': False
        }
        
        # Set as active model if it's the first one
        if self.active_model is None:
            self.active_model = model_id
        
        return model_id
    
    def run_simulation(self, model_id=None, **sim_params):
        """
        Run a simulation for the specified model.
        
        Args:
            model_id: Identifier for the model (uses active model if None)
            **sim_params: Additional simulation parameters
        """
        model_id = model_id or self.active_model
        
        if model_id not in self.models:
            return {'error': f"Model '{model_id}' not found."}
        
        print(f"Running simulation for model '{model_id}'...")
        model_data = self.models[model_id]
        model = model_data['model']
        
        # Run the simulation
        results = model.run_simulation(**sim_params)
        
        # Mark the model as having data
        model_data['has_data'] = True
        
        # Save results to CSV
        csv_file = f"{OUTPUT_DIR}/{model_id}_results.csv"
        model.save_results_to_csv(csv_file)
        
        return {'status': 'success', 'model_id': model_id, 'results_file': csv_file}
    
    def set_active_model(self, model_id):
        """
        Set the active model for queries.
        
        Args:
            model_id: Identifier for the model to set as active
        """
        if model_id not in self.models:
            return {'error': f"Model '{model_id}' not found."}
        
        self.active_model = model_id
        return {'status': 'success', 'active_model': model_id}
    
    def process_query(self, query_text, model_id=None):
        """
        Process a natural language query about the datacenter model.
        
        Args:
            query_text: Natural language query
            model_id: Identifier for the model to query (uses active model if None)
            
        Returns:
            Dictionary with query results and formatted response
        """
        model_id = model_id or self.active_model
        
        if model_id not in self.models:
            return {'error': f"Model '{model_id}' not found."}
        
        model_data = self.models[model_id]
        model = model_data['model']
        
        if not model_data['has_data']:
            return {'error': f"No simulation data available for model '{model_id}'. Please run a simulation first."}
        
        print(f"Processing query: '{query_text}'")
        
        # Process the query using the model's query method
        query_results = model.query(query_text)
        
        # Format the response in a way that could be used with an LLM
        formatted_response = self._format_response(query_text, query_results, model_id)
        
        return {
            'query': query_text,
            'model_id': model_id,
            'results': query_results,
            'response': formatted_response
        }
    
    def _format_response(self, query, results, model_id):
        """
        Format the query results into a natural language response.
        
        In a real LLM integration, this would be done by the LLM itself.
        This is a simplified version to demonstrate the concept.
        
        Args:
            query: Original query text
            results: Query results dictionary
            model_id: Identifier for the model
            
        Returns:
            Formatted response string
        """
        model_params = self.models[model_id]['params']
        location = model_params.get('location', 'unknown location')
        cooling_type = model_params.get('cooling_type', 'unknown cooling type')
        
        # Check for error
        if 'error' in results:
            return f"Error: {results['error']}"
        
        # If it's a summary query
        if any(word in query.lower() for word in ['summary', 'overview', 'tell me about']):
            return (
                f"Based on the simulation of a {model_params.get('datacenter_capacity_mw', 1.0)} MW datacenter "
                f"in {location} using {cooling_type} cooling:\n\n"
                f"- Average power consumption: {results.get('average_power_kw', 0):.2f} kW\n"
                f"- Peak power consumption: {results.get('peak_power_kw', 0):.2f} kW\n"
                f"- Total energy usage: {results.get('total_energy_kwh', 0):.2f} kWh\n"
                f"- Total carbon emissions: {results.get('total_carbon_emissions_tons', 0):.2f} tons CO2\n"
                f"- IT equipment accounts for {results.get('energy_breakdown', {}).get('datacenter_percent', 0):.1f}% "
                f"of the energy consumption, while cooling accounts for "
                f"{results.get('energy_breakdown', {}).get('cooling_percent', 0):.1f}%."
            )
        
        # If it's about energy
        elif any(word in query.lower() for word in ['energy', 'power', 'consumption']):
            if 'average' in query.lower():
                return f"The average power consumption of the datacenter in {location} is {results.get('average_power_kw', 0):.2f} kW."
            elif 'peak' in query.lower() or 'maximum' in query.lower():
                return f"The peak power consumption of the datacenter in {location} is {results.get('peak_power_kw', 0):.2f} kW."
            elif 'total' in query.lower():
                return f"The total energy consumption of the datacenter in {location} is {results.get('total_energy_kwh', 0):.2f} kWh."
            else:
                return (
                    f"The datacenter in {location} consumes an average of {results.get('average_power_kw', 0):.2f} kW, "
                    f"with a peak of {results.get('peak_power_kw', 0):.2f} kW, "
                    f"for a total of {results.get('total_energy_kwh', 0):.2f} kWh over the simulation period."
                )
        
        # If it's about carbon
        elif any(word in query.lower() for word in ['carbon', 'emissions', 'co2']):
            return f"The datacenter in {location} emits a total of {results.get('total_carbon_emissions_tons', 0):.2f} tons of CO2 during the simulation period."
        
        # If it's about water usage
        elif any(word in query.lower() for word in ['water', 'usage', 'consumption']):
            if 'total_water_usage_liters' in results:
                return f"The datacenter in {location} using {cooling_type} cooling consumes {results.get('total_water_usage_liters', 0):.2f} liters of water during the simulation period."
            else:
                return f"This datacenter uses {cooling_type} cooling, which does not directly consume water."
        
        # Default response
        else:
            return (
                f"Here's information about the datacenter in {location} using {cooling_type} cooling:\n\n"
                f"Average power: {results.get('average_power_kw', 0):.2f} kW\n"
                f"Total energy: {results.get('total_energy_kwh', 0):.2f} kWh\n"
                f"Carbon emissions: {results.get('total_carbon_emissions_tons', 0):.2f} tons CO2"
            )
    
    def compare_models(self, model_id1, model_id2, aspect=None):
        """
        Compare two datacenter models.
        
        Args:
            model_id1: First model to compare
            model_id2: Second model to compare
            aspect: Specific aspect to compare (e.g., 'energy', 'carbon', 'water')
            
        Returns:
            Dictionary with comparison results
        """
        if model_id1 not in self.models:
            return {'error': f"Model '{model_id1}' not found."}
        
        if model_id2 not in self.models:
            return {'error': f"Model '{model_id2}' not found."}
        
        model1_data = self.models[model_id1]
        model2_data = self.models[model_id2]
        
        if not model1_data['has_data'] or not model2_data['has_data']:
            return {'error': "Both models must have simulation data for comparison."}
        
        model1 = model1_data['model']
        model2 = model2_data['model']
        
        # Get summary data for both models
        summary1 = model1.query("summary")
        summary2 = model2.query("summary")
        
        # Prepare comparison data
        comparison = {
            'models': {
                model_id1: {
                    'params': model1_data['params'],
                    'summary': summary1
                },
                model_id2: {
                    'params': model2_data['params'],
                    'summary': summary2
                }
            },
            'differences': {
                'average_power_kw': summary2['average_power_kw'] - summary1['average_power_kw'],
                'peak_power_kw': summary2['peak_power_kw'] - summary1['peak_power_kw'],
                'total_energy_kwh': summary2['total_energy_kwh'] - summary1['total_energy_kwh'],
                'total_carbon_emissions_tons': summary2['total_carbon_emissions_tons'] - summary1['total_carbon_emissions_tons']
            }
        }
        
        # Add water usage comparison if both models use water cooling
        if 'total_water_usage_liters' in summary1 and 'total_water_usage_liters' in summary2:
            comparison['differences']['total_water_usage_liters'] = summary2['total_water_usage_liters'] - summary1['total_water_usage_liters']
        
        # Format a response
        response = self._format_comparison(model_id1, model_id2, comparison, aspect)
        comparison['response'] = response
        
        return comparison
    
    def _format_comparison(self, model_id1, model_id2, comparison, aspect=None):
        """
        Format the comparison results into a natural language response.
        
        Args:
            model_id1: First model ID
            model_id2: Second model ID
            comparison: Comparison results dictionary
            aspect: Specific aspect being compared
            
        Returns:
            Formatted comparison string
        """
        model1_params = comparison['models'][model_id1]['params']
        model2_params = comparison['models'][model_id2]['params']
        
        # Get key parameters for each model
        loc1 = model1_params.get('location', 'unknown')
        loc2 = model2_params.get('location', 'unknown')
        cool1 = model1_params.get('cooling_type', 'unknown')
        cool2 = model2_params.get('cooling_type', 'unknown')
        cap1 = model1_params.get('datacenter_capacity_mw', 0)
        cap2 = model2_params.get('datacenter_capacity_mw', 0)
        
        # Create a description of the models
        model1_desc = f"{cap1} MW datacenter in {loc1} using {cool1} cooling"
        model2_desc = f"{cap2} MW datacenter in {loc2} using {cool2} cooling"
        
        # General comparison text
        response = f"Comparing a {model1_desc} with a {model2_desc}:\n\n"
        
        # Filter based on the aspect if specified
        if aspect == 'energy' or aspect is None:
            diff_energy = comparison['differences']['total_energy_kwh']
            pct_diff = (diff_energy / comparison['models'][model_id1]['summary']['total_energy_kwh']) * 100 if comparison['models'][model_id1]['summary']['total_energy_kwh'] > 0 else 0
            
            response += (
                f"Energy Consumption:\n"
                f"- Model '{model_id1}': {comparison['models'][model_id1]['summary']['total_energy_kwh']:.2f} kWh\n"
                f"- Model '{model_id2}': {comparison['models'][model_id2]['summary']['total_energy_kwh']:.2f} kWh\n"
                f"- Difference: {diff_energy:.2f} kWh ({abs(pct_diff):.1f}% {'higher' if diff_energy > 0 else 'lower'})\n\n"
            )
        
        if aspect == 'carbon' or aspect is None:
            diff_carbon = comparison['differences']['total_carbon_emissions_tons']
            pct_diff = (diff_carbon / comparison['models'][model_id1]['summary']['total_carbon_emissions_tons']) * 100 if comparison['models'][model_id1]['summary']['total_carbon_emissions_tons'] > 0 else 0
            
            response += (
                f"Carbon Emissions:\n"
                f"- Model '{model_id1}': {comparison['models'][model_id1]['summary']['total_carbon_emissions_tons']:.2f} tons CO2\n"
                f"- Model '{model_id2}': {comparison['models'][model_id2]['summary']['total_carbon_emissions_tons']:.2f} tons CO2\n"
                f"- Difference: {diff_carbon:.2f} tons CO2 ({abs(pct_diff):.1f}% {'higher' if diff_carbon > 0 else 'lower'})\n\n"
            )
        
        if aspect == 'water' and 'total_water_usage_liters' in comparison['differences']:
            diff_water = comparison['differences']['total_water_usage_liters']
            water1 = comparison['models'][model_id1]['summary'].get('total_water_usage_liters', 0)
            water2 = comparison['models'][model_id2]['summary'].get('total_water_usage_liters', 0)
            pct_diff = (diff_water / water1) * 100 if water1 > 0 else 0
            
            response += (
                f"Water Usage:\n"
                f"- Model '{model_id1}': {water1:.2f} liters\n"
                f"- Model '{model_id2}': {water2:.2f} liters\n"
                f"- Difference: {diff_water:.2f} liters ({abs(pct_diff):.1f}% {'higher' if diff_water > 0 else 'lower'})\n\n"
            )
        
        # Add a conclusion
        if aspect is None:
            response += (
                f"In summary, the {model2_desc} "
                f"{'consumes more energy' if comparison['differences']['total_energy_kwh'] > 0 else 'consumes less energy'} and "
                f"{'produces more carbon emissions' if comparison['differences']['total_carbon_emissions_tons'] > 0 else 'produces fewer carbon emissions'} "
                f"compared to the {model1_desc}."
            )
        
        return response


def demonstrate_llm_interface():
    """
    Demonstrate how to use the LLMQueryInterface with datacenter models.
    """
    print("Initializing LLM Query Interface...")
    interface = LLMQueryInterface()
    
    # Create datacenter models
    print("\n=== Creating Datacenter Models ===")
    tx_air_model = interface.create_model(
        'tx_air',
        location='TX',
        cooling_type='air',
        datacenter_capacity_mw=1.0,
        simulation_start_date='2023-06-01',
        simulation_days=7
    )
    
    tx_water_model = interface.create_model(
        'tx_water',
        location='TX',
        cooling_type='water',
        datacenter_capacity_mw=1.0,
        simulation_start_date='2023-06-01',
        simulation_days=7
    )
    
    ca_air_model = interface.create_model(
        'ca_air',
        location='CA',
        cooling_type='air',
        datacenter_capacity_mw=1.0,
        simulation_start_date='2023-06-01',
        simulation_days=7
    )
    
    # Run simulations
    print("\n=== Running Simulations ===")
    for model_id in [tx_air_model, tx_water_model, ca_air_model]:
        interface.run_simulation(model_id)
    
    # Process natural language queries
    print("\n=== Processing Natural Language Queries ===")
    
    queries = [
        "What is the total energy consumption of the datacenter?",
        "Tell me about the carbon emissions in Texas.",
        "How much water does the water-cooled datacenter use?",
        "What is the average power consumption?",
        "Give me a summary of the Texas datacenter with air cooling."
    ]
    
    for query in queries:
        # Set the appropriate model based on the query
        if 'water' in query.lower():
            interface.set_active_model('tx_water')
        elif 'texas' in query.lower() or 'tx' in query.lower():
            interface.set_active_model('tx_air')
        elif 'california' in query.lower() or 'ca' in query.lower():
            interface.set_active_model('ca_air')
        
        # Process the query
        result = interface.process_query(query)
        
        print(f"\nQuery: {query}")
        print(f"Response: {result['response']}")
        print("-" * 80)
    
    # Compare models
    print("\n=== Comparing Models ===")
    
    # Compare Texas air vs water cooling
    comparison = interface.compare_models('tx_air', 'tx_water')
    print("\nComparison: Texas Air vs Water Cooling")
    print(comparison['response'])
    print("-" * 80)
    
    # Compare Texas vs California (air cooling)
    comparison = interface.compare_models('tx_air', 'ca_air')
    print("\nComparison: Texas vs California (Air Cooling)")
    print(comparison['response'])
    print("-" * 80)
    
    # Demo of how this could be integrated with an LLM
    print("\n=== Example LLM Integration ===")
    print(
        "In a full implementation, the LLM would receive the query, extract the intent,\n"
        "choose the appropriate model, and generate a response based on the simulation data.\n\n"
        "Example LLM prompt template:\n"
        f"{interface.prompt_templates['query'].format(query='What is the carbon impact of using water cooling vs air cooling in Texas?')}\n\n"
        "The LLM would then use the data from the compare_models() function to generate a detailed,\n"
        "contextual response about the differences in carbon emissions between cooling types."
    )


if __name__ == "__main__":
    demonstrate_llm_interface() 