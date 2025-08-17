# ann_recommender.py
import pandas as pd
import numpy as np
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Flatten, Dot, Dense, Concatenate
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split

class ANNRecommender:
    def __init__(self, movies_csv, ratings_csv, embedding_size=50):
        self.movies_csv = movies_csv
        self.ratings_csv = ratings_csv
        self.embedding_size = embedding_size
        self.model = None
        self.users_map = {}
        self.movies_map = {}
        self.reverse_users_map = {}
        self.reverse_movies_map = {}
        self.n_users = 0
        self.n_movies = 0
        self._prepare_data()
        self._build_model()

    def _prepare_data(self):
        # Load datasets
        movies = pd.read_csv(self.movies_csv)
        ratings = pd.read_csv(self.ratings_csv)
        
        # Map user and movie IDs to integers
        unique_users = ratings['userId'].unique()
        unique_movies = ratings['movieId'].unique()
        self.users_map = {uid: idx for idx, uid in enumerate(unique_users)}
        self.movies_map = {mid: idx for idx, mid in enumerate(unique_movies)}
        self.reverse_users_map = {idx: uid for uid, idx in self.users_map.items()}
        self.reverse_movies_map = {idx: mid for mid, idx in self.movies_map.items()}
        
        self.n_users = len(unique_users)
        self.n_movies = len(unique_movies)
        
        # Encode ratings
        ratings['user'] = ratings['userId'].map(self.users_map)
        ratings['movie'] = ratings['movieId'].map(self.movies_map)
        self.ratings_data = ratings[['user', 'movie', 'rating']]
        
        # Train/test split
        self.train_data, self.test_data = train_test_split(
            self.ratings_data, test_size=0.2, random_state=42
        )

    def _build_model(self):
        # Inputs
        user_input = Input(shape=(1,), name='user_input')
        movie_input = Input(shape=(1,), name='movie_input')
        
        # Embeddings
        user_embedding = Embedding(self.n_users, self.embedding_size, name='user_embedding')(user_input)
        movie_embedding = Embedding(self.n_movies, self.embedding_size, name='movie_embedding')(movie_input)
        
        # Flatten embeddings
        user_vec = Flatten()(user_embedding)
        movie_vec = Flatten()(movie_embedding)
        
        # Concatenate
        concat = Concatenate()([user_vec, movie_vec])
        dense = Dense(128, activation='relu')(concat)
        dense = Dense(64, activation='relu')(dense)
        output = Dense(1, activation='linear')(dense)
        
        # Build model
        self.model = Model(inputs=[user_input, movie_input], outputs=output)
        self.model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        print("✅ ANN model built successfully!")

    def train(self, epochs=5, batch_size=256):
        self.model.fit(
            [self.train_data['user'], self.train_data['movie']],
            self.train_data['rating'],
            validation_data=(
                [self.test_data['user'], self.test_data['movie']],
                self.test_data['rating']
            ),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )

    def predict(self, user_id, movie_id):
        if user_id not in self.users_map or movie_id not in self.movies_map:
            return None
        user_idx = self.users_map[user_id]
        movie_idx = self.movies_map[movie_id]
        pred = self.model.predict([np.array([user_idx]), np.array([movie_idx])], verbose=0)
        return float(pred[0][0])

if __name__ == "__main__":
    ann = ANNRecommender("../../data/movies.csv", "../../data/ratings.csv")
    ann.train(epochs=3)  # Quick test
    print("Sample Prediction (User 1, Movie 1):", ann.predict(1, 1))
