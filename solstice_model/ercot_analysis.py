import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def load_generation_data(filepath):
    """Loads ERCOT solar and wind generation data."""
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
    df = pd.read_csv(filepath, skiprows=4)
    df.columns = [
        "UTC_Timestamp", "Local_Begin", "Local_End", "Local_Date", "Hour_Number",
        "Bus_Avg_LMP", "Houston_LMP", "Hub_Avg_LMP", "North_LMP", "Panhandle_LMP", 
        "South_LMP", "West_LMP"
    ]
    df["UTC_Timestamp"] = pd.to_datetime(df["UTC_Timestamp"])
    return df

def merge_data(gen_df, lmp_df):
    """Merges generation and LMP datasets on timestamp."""
    return pd.merge_asof(
        gen_df.sort_values("UTC_Timestamp"), 
        lmp_df.sort_values("UTC_Timestamp"), 
        on="UTC_Timestamp"
    )

def plot_generation_vs_lmp(merged_df):
    """Plots solar and wind generation against LMPs for different regions."""
    regions = [
        ("North_Wind_Gen_MW", "North_LMP", "North Wind Generation vs. North LMP"),
        ("South_Houston_Wind_Gen_MW", "Houston_LMP", "South Houston Wind Generation vs. Houston LMP"),
        ("West_Wind_Gen_MW", "West_LMP", "West Wind Generation vs. West LMP"),
        ("Solar_Gen_MW", "Hub_Avg_LMP", "Solar Generation vs. Hub Average LMP")
    ]
    
    for gen_col, lmp_col, title in regions:
        plt.figure(figsize=(12, 6))
        plt.plot(merged_df["UTC_Timestamp"], merged_df[gen_col], label=gen_col, alpha=0.7)
        plt.plot(merged_df["UTC_Timestamp"], merged_df[lmp_col], label=lmp_col, linestyle="dashed", alpha=0.7)
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.title(title)
        plt.legend()
        plt.grid()
        plt.show()

def plot_correlation_matrix(merged_df):
    """Plots the correlation between generation and LMP values."""
    correlation_data = merged_df[[
        "Solar_Gen_MW", "North_Wind_Gen_MW", "South_Houston_Wind_Gen_MW", "West_Wind_Gen_MW",
        "North_LMP", "Houston_LMP", "West_LMP", "Hub_Avg_LMP"
    ]].corr()
    
    plt.figure(figsize=(10, 6))
    sns.heatmap(correlation_data, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
    plt.title("Correlation Between Generation and Locational Marginal Prices")
    plt.show()

def main():
    """Main function to load data, process, and visualize trends."""
    data_dir = "data/ERCOT_data/"
    gen_filepath = os.path.join(data_dir, "ercot_gen_sun-wnd_5min_2025Q1.csv")
    lmp_filepath = os.path.join(data_dir, "ercot_lmp_rt_15min_hubs_2025Q1.csv")
    
    # Load datasets
    gen_df = load_generation_data(gen_filepath)
    lmp_df = load_lmp_data(lmp_filepath)
    
    # Merge datasets
    merged_df = merge_data(gen_df, lmp_df)
    
    # Plot trends
    plot_generation_vs_lmp(merged_df)
    plot_correlation_matrix(merged_df)

if __name__ == "__main__":
    main()
