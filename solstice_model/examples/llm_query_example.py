#!/usr/bin/env python3
"""
Example script demonstrating how to use the LLM datacenter interface
with various natural language queries.
"""

import sys
import os
import time

# Add the parent directory to the Python path to import the model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_datacenter_interface import DatacenterQueryProcessor

def run_example_queries():
    """Run a series of example queries to demonstrate the interface."""
    
    # Initialize the processor (make sure OPENAI_API_KEY is set in your environment)
    try:
        processor = DatacenterQueryProcessor()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the OPENAI_API_KEY environment variable and try again.")
        return
    
    # Example queries of varying complexity
    example_queries = [
        "Model a 500 MW datacenter with water cooling in Texas",
        "What would be the energy needs for a medium-sized datacenter in California using air cooling?",
        "Compare the carbon emissions of a 10 MW datacenter in Washington state with water cooling over 14 days",
        "Can you simulate a 2 MW datacenter in New York with 90% cooling efficiency for the summer months?",
        "I need to design a hyperscale datacenter in Arizona with a PUE of 1.2, what would the energy usage be?"
    ]
    
    # Process each query
    for i, query in enumerate(example_queries):
        print(f"\n\n{'='*80}")
        print(f"EXAMPLE QUERY {i+1}: {query}")
        print(f"{'='*80}\n")
        
        # Process the query
        results = processor.process_query(query, run_simulation=True, save_results=False)
        
        # Print the detailed results
        print("\n--- QUERY RESULTS ---")
        print(f"Query: {results['query']}")
        print("\nExtracted Parameters:")
        for param, value in results['extracted_parameters'].items():
            print(f"  {param}: {value}")
        
        if 'simulation_summary' in results:
            print("\nSimulation Summary:")
            for key, value in results['simulation_summary'].items():
                print(f"  {key}: {value:.2f}")
        
        # Add a delay between queries to avoid API rate limits
        if i < len(example_queries) - 1:
            print("\nWaiting before next query...")
            time.sleep(2)
    
    print("\n\nAll example queries completed!")

if __name__ == "__main__":
    run_example_queries() 