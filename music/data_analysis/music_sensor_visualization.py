import csv
import matplotlib.pyplot as plt
import numpy as np

# Define the CSV file name
DATA_FILE = "flute_test.csv"

# Lists to store data
distances = []
notes = []
note_mapping = {"C4": 1, "D4": 2, "E4": 3, "F4": 4}  # Mapping notes to numeric values

# Read CSV file
with open(DATA_FILE, "r") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header row
    for row in reader:
        distances.append(float(row[0]))  # Convert distance to integer
        notes.append(note_mapping[row[1]])  # Convert notes to numeric values for plotting

# Create scatter plot
plt.figure(figsize=(8, 5))
plt.scatter(distances, notes, color="blue", edgecolors="black", s=100)

# Annotate each point with its x-value
for i, txt in enumerate(distances):
    plt.annotate(txt, (distances[i], notes[i]), textcoords="offset points", xytext=(5,5), ha='right')

# Formatting
plt.xlabel("Distance (cm)")
plt.ylabel("Music Note")
plt.title("Scatter Plot: Distance to Music Note Mapping")
plt.yticks(list(note_mapping.values()), list(note_mapping.keys()))  # Set y-axis labels to note names
plt.grid(axis="y", linestyle="--", alpha=0.7)

# Show plot
plt.show()
