import pandas as pd
import numpy as np

def analyze_us_sensor_data(file_path):
    try:
        # Read the file
        data = pd.read_csv(file_path, header=None, names=["Distance (cm)"])
        
        # Compute required statistics
        min_value = data["Distance (cm)"].min()
        max_value = data["Distance (cm)"].max()
        mean_value = data["Distance (cm)"].mean()
        std_dev = data["Distance (cm)"].std()
        
        # Create a summary table
        summary_table = pd.DataFrame({
            "Metric": ["Minimum Value", "Maximum Value", "Mean Value", "Standard Deviation"],
            "Value (cm)": [min_value, max_value, mean_value, std_dev]
        })
        
        # Display the results
        print(f"Results for file: {file_path}")
        print(summary_table.to_string(index=False))
        print("\n")
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

if __name__ == "__main__":
    analyze_us_sensor_data("us_sensor_10.csv")
    analyze_us_sensor_data("us_sensor_20.csv")
    analyze_us_sensor_data("us_sensor_30.csv")
