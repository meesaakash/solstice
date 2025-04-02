# Solstice Model LLM Interface

This module provides a natural language interface to the Solstice Datacenter Energy Model. It uses ChatGPT to parse natural language queries into configuration parameters for the datacenter model.

## Overview

The LLM interface allows you to interact with the Solstice datacenter energy model using natural language. For example, you can simply ask:

> "Can you model me the energy needs for a 500 MW sized datacenter that is water cooled in Texas?"

The interface will:
1. Parse your query using ChatGPT
2. Extract relevant configuration parameters
3. Set up a datacenter model with those parameters
4. Run a simulation
5. Return the results

## Setup

### Requirements

- Python 3.8+
- An OpenAI API key

### Installation

1. Ensure you have all the required dependencies installed:

```bash
pip install -r requirements.txt
pip install openai
```

2. Set up your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Command-line Interface

You can use the LLM interface directly from the command line:

```bash
python llm_datacenter_interface.py "Model a 500 MW datacenter with water cooling in Texas"
```

Optional arguments:
- `--api-key`: Directly provide your OpenAI API key
- `--no-sim`: Skip running the simulation
- `--save`: Save simulation results to files

### Python API

You can also use the interface in your Python code:

```python
from llm_datacenter_interface import DatacenterQueryProcessor

# Initialize the processor
processor = DatacenterQueryProcessor()

# Process a query
results = processor.process_query(
    "Can you model me the energy needs for a 500 MW sized datacenter that is water cooled?",
    run_simulation=True,
    save_results=False
)

# Access the results
print(results["extracted_parameters"])
print(results["simulation_summary"])
```

## Example Queries

The interface supports a wide range of natural language queries:

- "Model a 10 MW datacenter in California with air cooling"
- "What would the power consumption be for a 50 MW water-cooled datacenter in Washington?"
- "Compare the energy efficiency of a 5 MW datacenter in Arizona over 30 days"
- "Simulate a hyperscale datacenter in Texas with a PUE of 1.2"
- "What's the carbon impact of a 100 MW datacenter in New York with 85% cooling efficiency?"

## Parameter Extraction

The LLM interface can extract the following parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| location | Geographic location code (e.g., 'TX' for Texas) | 'TX' |
| cooling_type | Type of cooling system ('air' or 'water') | 'air' |
| datacenter_capacity_mw | Datacenter capacity in megawatts | 1.0 |
| simulation_start_date | Start date for the simulation (YYYY-MM-DD) | '2023-01-01' |
| simulation_days | Number of days to simulate | 7 |
| cooling_efficiency_factor | Factor to adjust cooling system efficiency | 1.0 |
| pue_overhead | Additional PUE overhead factor | 1.1 |

If a parameter is not explicitly mentioned in the query, a default value will be used.

## Examples

See the `examples/llm_query_example.py` file for working examples of using the LLM interface.

## Troubleshooting

- **API Key Issues**: Make sure your OpenAI API key is correctly set as an environment variable or passed directly.
- **JSON Parsing Errors**: If the API response doesn't parse correctly, the interface will fall back to a rule-based approach.
- **Rate Limiting**: Be mindful of OpenAI's rate limits if making many queries in succession.

## Advanced Usage

### Customizing Default Parameters

You can customize the default parameters by modifying the `default_params` dictionary in the `DatacenterQueryProcessor` class:

```python
processor = DatacenterQueryProcessor()
processor.default_params['location'] = 'CA'
processor.default_params['simulation_days'] = 14
```

### Saving Results

To save simulation results to files:

```python
results = processor.process_query(
    "Model a 100 MW datacenter in Florida",
    run_simulation=True,
    save_results=True
)
```

This will create a directory with CSV data and visualization plots. 