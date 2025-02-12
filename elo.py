import glob
import math
import os
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def preprocess_results():
    """Preprocess the raw results into the key1/key2 format."""
    # Create processed directory if it doesn't exist
    Path("processed").mkdir(exist_ok=True)

    # Process each CSV in results folder
    for csv_path in Path("results").glob("*.csv"):
        # Read input CSV
        df = pd.read_csv(csv_path)

        # Create output dataframe
        output_rows = []

        # Process each row
        for _, row in df.iterrows():
            # Create key1 using algorithm1's value
            key1 = f"nv{row['n_views']:02d}_{row['algorithm1']}_walnut{row['walnut_id']:02d}"

            # Create key2 using algorithm2's value
            key2 = f"nv{row['n_views']:02d}_{row['algorithm2']}_walnut{row['walnut_id']:02d}"

            # Add row with the two keys and score
            output_rows.append({"key1": key1, "key2": key2, "score": row["score"]})

        # Convert to dataframe and save
        output_df = pd.DataFrame(output_rows)
        output_path = Path("processed") / csv_path.name
        output_df.to_csv(output_path, index=False)


def create_calibration_csv():
    """Create a calibration CSV file comparing same algorithm at different view counts."""
    algorithms = [
        "siddon",
        "trilinear",
        "sax",
        "naf",
        "cgls",
        "nesterov",
        "sirt",
        "fdk",
    ]
    n_views = [5, 10, 15, 20, 30, 60]
    walnut_ids = range(3, 43)

    calibration_rows = []

    # Generate pairs for each algorithm
    for algo in algorithms:
        for walnut_id in walnut_ids:
            # Compare each view count with higher view counts
            for i, n_view1 in enumerate(n_views[:-1]):  # All except last
                for n_view2 in n_views[i + 1 :]:  # All higher view counts
                    key1 = f"nv{n_view1:02d}_{algo}_walnut{walnut_id:02d}"
                    key2 = f"nv{n_view2:02d}_{algo}_walnut{walnut_id:02d}"
                    calibration_rows.append({"key1": key1, "key2": key2, "score": 1.0})

    # Convert to dataframe and save
    calibration_df = pd.DataFrame(calibration_rows)
    output_path = Path("processed") / "calibration.csv"
    calibration_df.to_csv(output_path, index=False)


def compute_elo_ratings(results_dir="processed"):
    # Initialize dictionary to store ELO ratings for each n_views
    elo_ratings = {}

    # Process each results file
    for results_file in glob.glob(os.path.join(results_dir, "*.csv")):
        df = pd.read_csv(results_file)

        # Process each comparison
        for _, row in df.iterrows():
            # Parse n_views and algorithm names from keys
            key1_parts = row["key1"].split("_")
            key2_parts = row["key2"].split("_")

            # Extract n_views (assuming format 'nv05' -> 5)
            n_views = int(key1_parts[0][2:])

            # Extract algorithm names (ignore subject part)
            algo1 = key1_parts[1]
            algo2 = key2_parts[1]

            # Initialize ratings dict for this n_views if needed
            if n_views not in elo_ratings:
                elo_ratings[n_views] = {}

            # Initialize ratings for new algorithms
            if algo1 not in elo_ratings[n_views]:
                elo_ratings[n_views][algo1] = 1500
            if algo2 not in elo_ratings[n_views]:
                elo_ratings[n_views][algo2] = 1500

            # Calculate ELO updates
            k_factor = 32  # Standard chess K-factor
            r1 = elo_ratings[n_views][algo1]
            r2 = elo_ratings[n_views][algo2]

            # Expected scores
            e1 = 1 / (1 + math.pow(10, (r2 - r1) / 400))
            e2 = 1 - e1

            score = row["score"]
            # Actual scores:
            # score=0 means algo1 won
            # score=1 means algo2 won
            # score=0.5 means they tied
            # score=-1 means both lost
            if score == 0:
                s1, s2 = 1, 0
            elif score == 1:
                s1, s2 = 0, 1
            elif score == 0.5:
                s1, s2 = 0.5, 0.5
            else:  # score == -1
                # Both algorithms lose rating points
                s1, s2 = 0, 0

            # Update ratings
            elo_ratings[n_views][algo1] += k_factor * (s1 - e1)
            elo_ratings[n_views][algo2] += k_factor * (s2 - e2)

    # Convert to DataFrame for easier viewing
    results = []
    for n_views, ratings in elo_ratings.items():
        for algo, rating in ratings.items():
            results.append(
                {"n_views": n_views, "algorithm": algo, "elo_rating": round(rating, 1)}
            )

    return pd.DataFrame(results)


if __name__ == "__main__":
    # First preprocess the raw results
    preprocess_results()

    # Create calibration file
    create_calibration_csv()

    # Create outputs directory if it doesn't exist
    Path("outputs").mkdir(exist_ok=True)

    # Then compute and display ELO ratings
    ratings_df = compute_elo_ratings()
    
    # Save to CSV in outputs directory
    output_path = Path("outputs") / "elo_ratings.csv"
    ratings_df.sort_values(["n_views", "elo_rating"], ascending=[True, False]).to_csv(output_path, index=False)
    
    # Display results
    print("\nELO Ratings by number of views:")
    print(ratings_df.sort_values(["n_views", "elo_rating"], ascending=[True, False]))
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Get all unique algorithms
    algorithms = ratings_df['algorithm'].unique()
    
    # Plot one line per algorithm
    for algorithm in algorithms:
        algo_data = ratings_df[ratings_df['algorithm'] == algorithm]
        # Sort by n_views to ensure correct line connection
        algo_data = algo_data.sort_values('n_views')
        plt.plot(algo_data['n_views'], algo_data['elo_rating'], 'o-', label=algorithm)
    
    plt.xlabel('Number of Views')
    plt.ylabel('ELO Rating')
    plt.title('Algorithm ELO Ratings vs Number of Views')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    
    # Save plot to outputs directory
    plt.savefig(Path("outputs") / "elo_ratings.png")
    plt.show()
