import glob
import math
import os

import pandas as pd


def compute_elo_ratings(results_dir="results"):
    # Initialize dictionary to store ELO ratings for each n_views
    elo_ratings = {}

    # Process each results file
    for results_file in glob.glob(os.path.join(results_dir, "*.csv")):
        df = pd.read_csv(results_file)

        # Group by n_views
        for n_views, group in df.groupby("n_views"):
            if n_views not in elo_ratings:
                # Initialize ELO ratings for algorithms at 1500
                algorithms = set(group["algorithm1"].unique()) | set(
                    group["algorithm2"].unique()
                )
                elo_ratings[n_views] = {algo: 1500 for algo in algorithms}

            # Process each comparison
            for _, row in group.iterrows():
                algo1 = row["algorithm1"]
                algo2 = row["algorithm2"]
                score = row["score"]

                # Calculate ELO updates
                k_factor = 32  # Standard chess K-factor
                r1 = elo_ratings[n_views][algo1]
                r2 = elo_ratings[n_views][algo2]

                # Expected scores
                e1 = 1 / (1 + math.pow(10, (r2 - r1) / 400))
                e2 = 1 - e1

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
    ratings_df = compute_elo_ratings()
    print("\nELO Ratings by number of views:")
    print(ratings_df.sort_values(["n_views", "elo_rating"], ascending=[True, False]))
