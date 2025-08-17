# preprocess.py

import pandas as pd

def load_data():
    # Load movies and ratings
    movies = pd.read_csv("../../data/movies.csv", sep=",", header=None, names=["movieId", "title", "genres"])
    ratings = pd.read_csv("../../data/ratings.csv", sep=",", header=None, names=["userId", "movieId", "rating", "timestamp"])

    # Drop timestamp (not needed)
    ratings = ratings.drop("timestamp", axis=1)

    return movies, ratings

if __name__ == "__main__":
    movies, ratings = load_data()

    print("Movies dataset:")
    print(movies.head())

    print("\nRatings dataset:")
    print(ratings.head())
