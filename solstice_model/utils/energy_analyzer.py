import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class EnergyAnalyzer:
    """
    Analyzes and visualizes datacenter energy consumption data.
    
    This class provides methods for analyzing energy consumption patterns,
    calculating metrics, and creating visualizations.
    """
    
    def __init__(self):
        """
        Initialize the energy analyzer.
        """
        # Set matplotlib style
        plt.style.use('ggplot')
        
        # Color palette for consistent visualization
        self.colors = {
            'it_power': '#1f77b4',  # Blue
            'cooling': '#ff7f0e',   # Orange
            'total': '#2ca02c',     # Green
            'carbon': '#d62728',    # Red
            'water': '#9467bd',     # Purple
            'pue': '#8c564b',       # Brown
            'background': '#f5f5f5' # Light gray
        }
    
    def calculate_metrics(self, results_data):
        """
        Calculate various energy and efficiency metrics.
        
        Args:
            results_data: Simulation results dictionary
            
        Returns:
            Dictionary of calculated metrics
        """
        metrics = {}
        
        # Extract data
        datacenter_energy = np.array(results_data['datacenter_energy'])
        cooling_energy = np.array(results_data['cooling_energy'])
        total_energy = np.array(results_data['total_energy'])
        carbon_emissions = np.array(results_data['carbon_emissions'])
        
        if 'water_usage' in results_data:
            water_usage = np.array(results_data['water_usage'])
            metrics['total_water_usage'] = water_usage.sum()
            metrics['avg_water_usage'] = water_usage.mean()
            metrics['max_water_usage'] = water_usage.max()
        
        # Basic energy metrics
        metrics['total_energy_consumption'] = total_energy.sum()
        metrics['avg_energy_consumption'] = total_energy.mean()
        metrics['peak_energy_consumption'] = total_energy.max()
        metrics['min_energy_consumption'] = total_energy.min()
        
        # IT vs. cooling metrics
        metrics['total_it_energy'] = datacenter_energy.sum()
        metrics['total_cooling_energy'] = cooling_energy.sum()
        metrics['cooling_to_it_ratio'] = metrics['total_cooling_energy'] / metrics['total_it_energy']
        
        # PUE (Power Usage Effectiveness)
        metrics['avg_pue'] = total_energy.mean() / datacenter_energy.mean()
        
        # Carbon metrics
        metrics['total_carbon_emissions'] = carbon_emissions.sum()
        metrics['avg_carbon_intensity'] = metrics['total_carbon_emissions'] / (metrics['total_energy_consumption'] / 1000000)
        
        return metrics
    
    def plot_energy_consumption(self, results_data, cooling_type, location, save_path=None):
        """
        Plot energy consumption over time.
        
        Args:
            results_data: Simulation results dictionary
            cooling_type: Type of cooling system
            location: Geographic location code
            save_path: Optional path to save the plot
        """
        timestamps = results_data['timestamps']
        datacenter_energy = results_data['datacenter_energy']
        cooling_energy = results_data['cooling_energy']
        total_energy = results_data['total_energy']
        
        # Create the figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot the data
        ax.plot(timestamps, [e/1000 for e in datacenter_energy], 
                label='IT Equipment', color=self.colors['it_power'], linewidth=2)
        ax.plot(timestamps, [e/1000 for e in cooling_energy], 
                label='Cooling System', color=self.colors['cooling'], linewidth=2)
        ax.plot(timestamps, [e/1000 for e in total_energy], 
                label='Total Energy', color=self.colors['total'], linewidth=2, linestyle='--')
        
        # Add shaded area for datacenter energy
        ax.fill_between(timestamps, [0] * len(timestamps), [e/1000 for e in datacenter_energy], 
                        color=self.colors['it_power'], alpha=0.3)
        
        # Add shaded area for cooling energy (stacked on top of datacenter energy)
        ax.fill_between(timestamps, [e/1000 for e in datacenter_energy], 
                       [d/1000 + c/1000 for d, c in zip(datacenter_energy, cooling_energy)], 
                       color=self.colors['cooling'], alpha=0.3)
        
        # Customize the plot
        location_name = {'TX': 'Texas', 'NY': 'New York'}.get(location, location)
        cooling_name = {'air': 'Air-Cooled', 'water': 'Water-Cooled'}.get(cooling_type, cooling_type)
        
        ax.set_title(f'Datacenter Energy Consumption - {location_name} ({cooling_name})', fontsize=16)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Power (kW)', fontsize=12)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format the x-axis to show dates nicely
        fig.autofmt_xdate()
        
        # Add metrics as text
        metrics = self.calculate_metrics(results_data)
        avg_pue = metrics['avg_pue']
        cooling_ratio = metrics['cooling_to_it_ratio'] * 100
        
        metrics_text = (f"Avg. PUE: {avg_pue:.2f}\n"
                       f"Cooling: {cooling_ratio:.1f}% of IT Load\n"
                       f"Peak Power: {metrics['peak_energy_consumption']/1000:.1f} kW")
        
        ax.text(0.02, 0.95, metrics_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='white', alpha=0.8))
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    def plot_carbon_emissions(self, results_data, location, save_path=None):
        """
        Plot carbon emissions over time.
        
        Args:
            results_data: Simulation results dictionary
            location: Geographic location code
            save_path: Optional path to save the plot
        """
        timestamps = results_data['timestamps']
        carbon_emissions = results_data['carbon_emissions']
        carbon_intensity = results_data['carbon_intensity']
        workload = results_data['workload']
        
        # Create the figure with two y-axes
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax2 = ax1.twinx()
        
        # Plot carbon emissions
        emissions_line = ax1.plot(timestamps, carbon_emissions, 
                               label='Carbon Emissions', color=self.colors['carbon'], linewidth=2)
        ax1.fill_between(timestamps, [0] * len(timestamps), carbon_emissions, 
                        color=self.colors['carbon'], alpha=0.2)
        
        # Plot workload on secondary axis as a dotted line
        workload_line = ax2.plot(timestamps, workload, 
                              label='Workload', color=self.colors['it_power'], 
                              linewidth=1.5, linestyle='--')
        
        # Customize the primary axis
        location_name = {'TX': 'Texas', 'NY': 'New York'}.get(location, location)
        ax1.set_title(f'Datacenter Carbon Emissions - {location_name}', fontsize=16)
        ax1.set_xlabel('Time', fontsize=12)
        ax1.set_ylabel('Carbon Emissions (tons CO2)', fontsize=12)
        ax1.tick_params(axis='y')
        
        # Customize the secondary axis
        ax2.set_ylabel('Workload (utilization %)', fontsize=12)
        ax2.tick_params(axis='y')
        ax2.set_ylim(0, 1.0)
        
        # Add a combined legend
        lines = emissions_line + workload_line
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=12)
        
        # Add grid
        ax1.grid(True, alpha=0.3)
        
        # Format the x-axis to show dates nicely
        fig.autofmt_xdate()
        
        # Add metrics as text
        metrics = self.calculate_metrics(results_data)
        total_emissions = metrics['total_carbon_emissions']
        avg_intensity = metrics['avg_carbon_intensity']
        
        metrics_text = (f"Total Emissions: {total_emissions:.2f} tons CO2\n"
                       f"Avg. Carbon Intensity: {avg_intensity:.1f} gCO2/kWh")
        
        ax1.text(0.02, 0.95, metrics_text, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='white', alpha=0.8))
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    def create_report(self, results_data, model_config, output_path=None):
        """
        Create a comprehensive report with multiple visualizations and metrics.
        
        Args:
            results_data: Simulation results dictionary
            model_config: Model configuration dictionary
            output_path: Optional path to save the report
            
        Returns:
            Pandas DataFrame with report data
        """
        # Calculate metrics
        metrics = self.calculate_metrics(results_data)
        
        # Create a DataFrame for the report
        report_data = pd.DataFrame({
            'Metric': list(metrics.keys()),
            'Value': list(metrics.values())
        })
        
        # Create visualizations
        fig, axs = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Energy consumption over time
        ax1 = axs[0, 0]
        timestamps = results_data['timestamps']
        ax1.plot(timestamps, [e/1000 for e in results_data['datacenter_energy']], 
                label='IT Equipment', color=self.colors['it_power'])
        ax1.plot(timestamps, [e/1000 for e in results_data['cooling_energy']], 
                label='Cooling', color=self.colors['cooling'])
        ax1.plot(timestamps, [e/1000 for e in results_data['total_energy']], 
                label='Total', color=self.colors['total'], linestyle='--')
        ax1.set_title('Energy Consumption Over Time')
        ax1.set_ylabel('Power (kW)')
        ax1.legend()
        
        # Plot 2: Carbon emissions
        ax2 = axs[0, 1]
        ax2.plot(timestamps, results_data['carbon_emissions'], color=self.colors['carbon'])
        ax2.fill_between(timestamps, [0] * len(timestamps), results_data['carbon_emissions'], 
                        color=self.colors['carbon'], alpha=0.3)
        ax2.set_title('Carbon Emissions Over Time')
        ax2.set_ylabel('Emissions (tons CO2)')
        
        # Plot 3: Energy breakdown pie chart
        ax3 = axs[1, 0]
        labels = ['IT Equipment', 'Cooling']
        sizes = [metrics['total_it_energy'], metrics['total_cooling_energy']]
        ax3.pie(sizes, labels=labels, autopct='%1.1f%%', colors=[self.colors['it_power'], self.colors['cooling']])
        ax3.set_title('Energy Consumption Breakdown')
        
        # Plot 4: PUE calculation
        ax4 = axs[1, 1]
        # Create a bar chart for PUE
        pue_components = ['IT Power', 'Cooling Power']
        pue_values = [1.0, metrics['cooling_to_it_ratio']]  # IT power is the baseline (1.0)
        ax4.bar(pue_components, pue_values, color=[self.colors['it_power'], self.colors['cooling']])
        ax4.set_title(f'PUE Components (Total PUE: {metrics["avg_pue"]:.2f})')
        ax4.set_ylabel('Contribution to PUE')
        
        # Add a title to the figure
        cooling_name = {'air': 'Air-Cooled', 'water': 'Water-Cooled'}.get(
            model_config.get('cooling_type', 'unknown'), 'Unknown')
        location_name = {'TX': 'Texas', 'NY': 'New York'}.get(
            model_config.get('location', 'unknown'), 'Unknown')
        
        fig.suptitle(f'Datacenter Performance Report - {location_name} ({cooling_name})', 
                    fontsize=16, y=0.98)
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save or show the report
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
        
        return report_data
    
    def analyze_workload_efficiency(self, results_data):
        """
        Analyze the relationship between workload and energy efficiency.
        
        Args:
            results_data: Simulation results dictionary
            
        Returns:
            Dictionary with workload efficiency metrics
        """
        workload = np.array(results_data['workload'])
        datacenter_energy = np.array(results_data['datacenter_energy'])
        cooling_energy = np.array(results_data['cooling_energy'])
        total_energy = np.array(results_data['total_energy'])
        
        # Create workload bins
        bins = np.linspace(0, 1, 11)  # 10 bins from 0 to 1
        bin_indices = np.digitize(workload, bins) - 1
        
        # Calculate metrics for each bin
        bin_metrics = []
        for i in range(len(bins)-1):
            bin_mask = (bin_indices == i)
            if np.sum(bin_mask) > 0:  # If there are points in this bin
                bin_workload_avg = np.mean(workload[bin_mask])
                bin_datacenter_avg = np.mean(datacenter_energy[bin_mask])
                bin_cooling_avg = np.mean(cooling_energy[bin_mask])
                bin_total_avg = np.mean(total_energy[bin_mask])
                bin_pue = bin_total_avg / bin_datacenter_avg if bin_datacenter_avg > 0 else 0
                
                bin_metrics.append({
                    'workload_bin': f"{bins[i]:.1f}-{bins[i+1]:.1f}",
                    'workload_avg': bin_workload_avg,
                    'datacenter_energy_avg': bin_datacenter_avg,
                    'cooling_energy_avg': bin_cooling_avg,
                    'total_energy_avg': bin_total_avg,
                    'pue': bin_pue,
                    'samples': np.sum(bin_mask)
                })
        
        # Convert to DataFrame for easier analysis
        efficiency_df = pd.DataFrame(bin_metrics)
        
        # Calculate energy per workload unit (efficiency)
        if not efficiency_df.empty:
            efficiency_df['energy_per_workload'] = efficiency_df['total_energy_avg'] / efficiency_df['workload_avg']
            
            # Find the most efficient workload bin
            most_efficient_bin = efficiency_df.loc[efficiency_df['energy_per_workload'].idxmin()]
            
            return {
                'efficiency_by_workload': efficiency_df,
                'most_efficient_workload': most_efficient_bin['workload_avg'],
                'most_efficient_pue': most_efficient_bin['pue'],
                'most_efficient_energy_per_workload': most_efficient_bin['energy_per_workload']
            }
        else:
            return {
                'efficiency_by_workload': pd.DataFrame(),
                'most_efficient_workload': 0,
                'most_efficient_pue': 0,
                'most_efficient_energy_per_workload': 0
            } 