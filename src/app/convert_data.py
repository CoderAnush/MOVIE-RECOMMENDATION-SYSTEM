import pandas as pd

# File paths
movies_file = "../../data/movies.dat"
ratings_file = "../../data/ratings.dat"
tags_file = "../../data/tags.dat"

# Load datasets with proper separators
movies = pd.read_csv(movies_file, sep="::", engine="python", header=None, names=["movieId", "title", "genres"])
ratings = pd.read_csv(ratings_file, sep="::", engine="python", header=None, names=["userId", "movieId", "rating", "timestamp"])
tags = pd.read_csv(tags_file, sep="::", engine="python", header=None, names=["userId", "movieId", "tag", "timestamp"])

# Save them as CSV
movies.to_csv("../../data/movies.csv", index=False)
ratings.to_csv("../../data/ratings.csv", index=False)
tags.to_csv("../../data/tags.csv", index=False)

print("✅ Conversion complete! Files saved as movies.csv, ratings.csv, tags.csv")
