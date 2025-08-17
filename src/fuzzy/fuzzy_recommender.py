import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import pandas as pd

# Load dataset
movies = pd.read_csv("../../data/movies.csv")
ratings = pd.read_csv("../../data/ratings.csv")

# Compute movie stats
movie_stats = ratings.groupby("movieId").agg({
    "rating": "mean",
    "userId": "count"
}).rename(columns={"rating": "avg_rating", "userId": "num_ratings"}).reset_index()

# Merge with movie titles
movie_stats = pd.merge(movie_stats, movies, on="movieId")

# Define fuzzy variables
rating = ctrl.Antecedent(np.arange(0, 5.1, 0.1), "rating")
popularity = ctrl.Antecedent(np.arange(0, 1000, 10), "popularity")
recommend = ctrl.Consequent(np.arange(0, 101, 1), "recommend")

# Membership functions for rating
rating["low"] = fuzz.trimf(rating.universe, [0, 0, 2.5])
rating["medium"] = fuzz.trimf(rating.universe, [2, 2.5, 3.5])
rating["high"] = fuzz.trimf(rating.universe, [3, 5, 5])

# Membership functions for popularity
popularity["unpopular"] = fuzz.trimf(popularity.universe, [0, 0, 300])
popularity["average"] = fuzz.trimf(popularity.universe, [200, 500, 800])
popularity["popular"] = fuzz.trimf(popularity.universe, [600, 1000, 1000])

# Membership functions for recommendation
recommend["low"] = fuzz.trimf(recommend.universe, [0, 0, 40])
recommend["medium"] = fuzz.trimf(recommend.universe, [30, 50, 70])
recommend["high"] = fuzz.trimf(recommend.universe, [60, 100, 100])

# Define fuzzy rules
rule1 = ctrl.Rule(rating["high"] & popularity["popular"], recommend["high"])
rule2 = ctrl.Rule(rating["medium"] & popularity["average"], recommend["medium"])
rule3 = ctrl.Rule(rating["low"] & popularity["unpopular"], recommend["low"])
rule4 = ctrl.Rule(rating["high"] & popularity["unpopular"], recommend["medium"])
rule5 = ctrl.Rule(rating["medium"] & popularity["popular"], recommend["high"])

# Build control system
recommend_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5])
recommend_sim = ctrl.ControlSystemSimulation(recommend_ctrl)

# Example: Recommend score for a movie
def get_recommend_score(avg_rating, num_ratings):
    recommend_sim.input["rating"] = avg_rating
    recommend_sim.input["popularity"] = min(num_ratings, 1000)  # cap popularity
    recommend_sim.compute()
    return recommend_sim.output["recommend"]

# Apply fuzzy logic to all movies
movie_stats["recommend_score"] = movie_stats.apply(
    lambda row: get_recommend_score(row["avg_rating"], row["num_ratings"]), axis=1
)

# Show top recommended movies
top_movies = movie_stats.sort_values("recommend_score", ascending=False).head(10)
print(top_movies[["title", "avg_rating", "num_ratings", "recommend_score"]])
