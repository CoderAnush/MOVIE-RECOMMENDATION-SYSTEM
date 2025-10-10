#!/usr/bin/env python3
"""MovieLens 10M data preparation utilities.

This script loads the official MovieLens 10M (ml-10M100K) dataset, performs
lightweight preprocessing, and writes optimized parquet files along with
dataset statistics that will be consumed by the recommendation engines.

The goals are:
    • Load movies.dat, ratings.dat, and tags.dat (if available)
    • Extract useful metadata such as release year and genre indicators
    • Compute aggregate statistics for movies and users (avg rating, counts)
    • Persist the cleaned tables in the `processed/` directory for fast reload
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR_CANDIDATES = (
    Path("data/ml-10M100K"),
    Path("../data/ml-10M100K"),
    Path("../../data/ml-10M100K"),
    Path("data"),
)

OUTPUT_DIR = Path("processed")
OUTPUT_DIR.mkdir(exist_ok=True)

PREPROCESSED_CSV = OUTPUT_DIR / "preprocessed_movielens10M.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger("prepare_dataset")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def locate_dataset(explicit_path: Optional[str]) -> Path:
    """Return the directory containing the MovieLens 10M .dat files."""

    if explicit_path:
        candidate = Path(explicit_path).expanduser().resolve()
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Specified data path does not exist: {candidate}")

    for candidate in DATA_DIR_CANDIDATES:
        candidate = candidate.resolve()
        if (candidate / "movies.dat").exists() and (candidate / "ratings.dat").exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate MovieLens dataset. Please place the ml-10M100K folder "
        "inside the repository's data/ directory or pass --data-path explicitly."
    )


def parse_movies(movies_path: Path) -> pd.DataFrame:
    """Load and enrich movies table."""

    LOGGER.info("Loading movies from %s", movies_path)
    movies_df = pd.read_csv(
        movies_path,
        sep="::",
        engine="python",
        names=["movie_id", "title", "genres"],
        dtype={"movie_id": np.int32, "title": "string", "genres": "string"},
        encoding="latin-1",
    )

    # Extract release year from title (e.g., "Toy Story (1995)")
    movies_df["year"] = (
        movies_df["title"].str.extract(r"\((\d{4})\)").astype("float32")
    )
    movies_df["title"] = movies_df["title"].str.replace(r"\s*\(\d{4}\)", "", regex=True)
    movies_df["year"] = movies_df["year"].fillna(0).astype(np.int16)

    # Expand genres into a list and indicator columns
    movies_df["genre_list"] = (
        movies_df["genres"].fillna("").apply(lambda g: g.split("|") if g else [])
    )
    unique_genres = sorted({genre for genres in movies_df["genre_list"] for genre in genres})
    for genre in unique_genres:
        col = f"genre_{genre.lower().replace('-', '_')}"
        movies_df[col] = movies_df["genre_list"].apply(lambda genres: genre in genres)

    LOGGER.info("Movies loaded: %d", len(movies_df))
    LOGGER.info("Detected %d unique genres", len(unique_genres))
    return movies_df


def parse_ratings(ratings_path: Path, limit: Optional[int] = None) -> pd.DataFrame:
    """Load ratings table, optionally limiting the number of rows for testing."""

    LOGGER.info("Loading ratings from %s", ratings_path)
    ratings_df = pd.read_csv(
        ratings_path,
        sep="::",
        engine="python",
        names=["user_id", "movie_id", "rating", "timestamp"],
        dtype={"user_id": np.int32, "movie_id": np.int32, "rating": np.float32, "timestamp": np.int64},
        nrows=limit,
    )

    ratings_df["datetime"] = pd.to_datetime(ratings_df["timestamp"], unit="s")
    LOGGER.info("Ratings loaded: %d", len(ratings_df))
    return ratings_df


def parse_tags(tags_path: Path) -> pd.DataFrame:
    """Load tags table if available."""

    if not tags_path.exists():
        LOGGER.warning("Tags file not found at %s; continuing without tags", tags_path)
        return pd.DataFrame(columns=["user_id", "movie_id", "tag", "timestamp"])

    LOGGER.info("Loading tags from %s", tags_path)
    tags_df = pd.read_csv(
        tags_path,
        sep="::",
        engine="python",
        names=["user_id", "movie_id", "tag", "timestamp"],
        dtype={"user_id": np.int32, "movie_id": np.int32, "tag": "string", "timestamp": np.int64},
        encoding="latin-1",
    )
    tags_df["datetime"] = pd.to_datetime(tags_df["timestamp"], unit="s")
    LOGGER.info("Tags loaded: %d", len(tags_df))
    return tags_df


def compute_movie_statistics(movies_df: pd.DataFrame, ratings_df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregated statistics per movie."""

    LOGGER.info("Computing movie statistics (mean rating, counts, etc.)")
    movie_stats = ratings_df.groupby("movie_id").agg(
        avg_rating=("rating", "mean"),
        rating_count=("rating", "count"),
        rating_std=("rating", "std"),
        rating_min=("rating", "min"),
        rating_max=("rating", "max"),
        first_rating=("datetime", "min"),
        last_rating=("datetime", "max"),
        n_users=("user_id", "nunique"),
    ).reset_index()

    movie_stats["avg_rating"] = movie_stats["avg_rating"].fillna(0)
    movie_stats["rating_std"] = movie_stats["rating_std"].fillna(0)

    enriched_movies = movies_df.merge(movie_stats, on="movie_id", how="left")
    LOGGER.info("Movie statistics computed")
    return enriched_movies


def encode_ids(data: pd.DataFrame) -> Tuple[pd.DataFrame, LabelEncoder, LabelEncoder]:
    """Create contiguous integer IDs for users and movies."""

    LOGGER.info("Encoding user and movie IDs")
    user_encoder = LabelEncoder()
    movie_encoder = LabelEncoder()

    data["user"] = user_encoder.fit_transform(data["user_id"])
    data["movie"] = movie_encoder.fit_transform(data["movie_id"])

    LOGGER.info(
        "Encoded %d unique users and %d unique movies",
        data["user"].nunique(),
        data["movie"].nunique(),
    )

    return data, user_encoder, movie_encoder


def expand_genres(data: pd.DataFrame) -> Tuple[pd.DataFrame, Tuple[str, ...]]:
    """Expand pipe-delimited genres into binary indicator columns."""

    LOGGER.info("Expanding genres into indicator columns")
    data["genre_list"] = data["genre_list"].apply(
        lambda value: value if isinstance(value, list) else []
    )
    all_genres = sorted({genre for genres in data["genre_list"] for genre in genres})

    for genre in all_genres:
        column_name = f"genre_{genre.lower().replace('-', '_')}"
        data[column_name] = data["genre_list"].apply(lambda genres: 1 if genre in genres else 0)

    LOGGER.info("Created %d genre indicator columns", len(all_genres))
    return data, tuple(all_genres)


def compute_user_statistics(ratings_df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregated statistics per user."""

    LOGGER.info("Computing user statistics")
    user_stats = ratings_df.groupby("user_id").agg(
        avg_rating_given=("rating", "mean"),
        rating_count=("rating", "count"),
        rating_std=("rating", "std"),
        n_movies=("movie_id", "nunique"),
        first_rating=("datetime", "min"),
        last_rating=("datetime", "max"),
    ).reset_index()

    user_stats["avg_rating_given"] = user_stats["avg_rating_given"].fillna(0)
    user_stats["rating_std"] = user_stats["rating_std"].fillna(0)
    LOGGER.info("User statistics computed")
    return user_stats


def build_dataset_summary(movies_df: pd.DataFrame, ratings_df: pd.DataFrame, tags_df: pd.DataFrame) -> Dict:
    """Create a JSON-serializable summary of the dataset."""

    LOGGER.info("Building dataset summary")
    summary = {
        "movies": int(len(movies_df)),
        "ratings": int(len(ratings_df)),
        "users": int(ratings_df["user_id"].nunique()),
        "genres": sorted(
            {
                genre
                for genres in movies_df.get("genre_list", [])
                for genre in (genres if isinstance(genres, list) else [])
            }
        ),
        "average_rating": float(ratings_df["rating"].mean()),
        "rating_distribution": ratings_df["rating"].value_counts().sort_index().astype(int).to_dict(),
        "time_range": {
            "first_rating": ratings_df["datetime"].min().isoformat(),
            "last_rating": ratings_df["datetime"].max().isoformat(),
        },
        "tags": int(len(tags_df)),
    }
    LOGGER.info(
        "Dataset summary: %d movies, %d ratings, %d users",
        summary["movies"],
        summary["ratings"],
        summary["users"],
    )
    return summary


def save_outputs(
    movies_df: pd.DataFrame,
    ratings_df: pd.DataFrame,
    user_stats: pd.DataFrame,
    summary: Dict,
    merged_encoded: pd.DataFrame,
    genre_columns: Tuple[str, ...],
) -> None:
    """Persist processed data to disk."""

    movies_path = OUTPUT_DIR / "movies_enriched.parquet"
    ratings_path = OUTPUT_DIR / "ratings.parquet"
    user_stats_path = OUTPUT_DIR / "user_stats.parquet"
    summary_path = OUTPUT_DIR / "dataset_summary.json"

    LOGGER.info("Writing movies → %s", movies_path)
    movies_df.to_parquet(movies_path, index=False)

    LOGGER.info("Writing ratings → %s", ratings_path)
    ratings_df.to_parquet(ratings_path, index=False)

    LOGGER.info("Writing user stats → %s", user_stats_path)
    user_stats.to_parquet(user_stats_path, index=False)

    LOGGER.info("Writing summary → %s", summary_path)
    summary_path.write_text(json.dumps(summary, indent=2))

    # Persist merged dataset for downstream models (CSV to simplify inspection)
    feature_columns = [
        "user",
        "movie",
        "rating",
    ] + [f"genre_{g.lower().replace('-', '_')}" for g in genre_columns]

    feature_columns = [col for col in feature_columns if col in merged_encoded.columns]
    LOGGER.info("Writing merged features → %s", PREPROCESSED_CSV)
    merged_encoded[feature_columns].to_csv(PREPROCESSED_CSV, index=False)


def main(data_path: Optional[str], limit: Optional[int]) -> None:
    dataset_dir = locate_dataset(data_path)
    LOGGER.info("Using dataset directory: %s", dataset_dir)

    movies_df = parse_movies(dataset_dir / "movies.dat")
    ratings_df = parse_ratings(dataset_dir / "ratings.dat", limit=limit)
    tags_df = parse_tags(dataset_dir / "tags.dat")

    movies_enriched = compute_movie_statistics(movies_df, ratings_df)
    user_stats = compute_user_statistics(ratings_df)
    summary = build_dataset_summary(movies_enriched, ratings_df, tags_df)

    LOGGER.info("Merging ratings with movie metadata")
    merged = ratings_df.merge(
        movies_enriched[
            [
                "movie_id",
                "title",
                "genres",
                "genre_list",
                "year",
                "avg_rating",
                "rating_count",
            ]
        ],
        on="movie_id",
        how="left",
    )

    merged_encoded, user_encoder, movie_encoder = encode_ids(merged)
    merged_features, genre_columns = expand_genres(merged_encoded)

    summary.update(
        {
            "encoded_users": int(merged_features["user"].nunique()),
            "encoded_movies": int(merged_features["movie"].nunique()),
            "genre_columns": [f"genre_{g.lower().replace('-', '_')}" for g in genre_columns],
        }
    )

    save_outputs(
        movies_enriched,
        ratings_df,
        user_stats,
        summary,
        merged_features,
        genre_columns,
    )
    LOGGER.info("Data preparation finished ✅")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare the MovieLens 10M dataset")
    parser.add_argument(
        "--data-path",
        help="Custom path to the MovieLens data directory (containing movies.dat, ratings.dat, tags.dat)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional limit on number of ratings to load (useful for quick tests)",
    )
    args = parser.parse_args()

    main(data_path=args.data_path, limit=args.limit)
