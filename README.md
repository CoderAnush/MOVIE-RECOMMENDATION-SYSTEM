# Movie Recommendation System

## Project Title
Fuzzy Movie Recommendation System Using Soft Computing techniques

## Aim
To develop an intelligent movie recommendation system that predicts movies a user might like based on uncertain or imprecise user preferences by leveraging Soft Computing techniques: Fuzzy Logic, Artificial Neural Networks (ANN), and a hybrid approach combining both.

## Software Technologies to be Used:
Programming Language: Python
Libraries & Frameworks: Pandas, NumPy, Scikit-learn, TensorFlow/Keras (for ANN), Matplotlib, Seaborn, scikit-fuzzy
Dataset Management: CSV (MovieLens 10M Dataset)
Development Environment: Jupyter Notebook, VS Code, Google Colab (optional)
Version Control: GitHub

## 📁 Dataset

This project uses the **MovieLens 1M dataset** (ratings.dat ~250 MB), which is **not included** here due to GitHub’s 100 MB file size limit.

## 📁 Dataset

This project uses the **MovieLens 1M dataset** (ratings.dat ~250 MB), which is **not included** here due to GitHub’s 100 MB file size limit.

### How to download:
1. Visit the Kaggle dataset page: [MovieLens-1M Dataset on Kaggle](https://www.kaggle.com/datasets/odedgolden/movielens-1m-dataset)  
2. Download `ratings.dat` (and any other `.dat` files you need, like `users.dat`, `movies.dat`)  
3. Inside the project folder, create a `data/` directory (if it's not there already)  
4. Move `ratings.dat` into that folder so it looks like this:

```
data/
    ratings.dat
    users.dat
    movies.dat
```


## Detailed Summary of the Project
This project implements a Movie Recommendation System using Soft Computing techniques to handle the uncertainty and vagueness inherent in human preferences. Unlike traditional recommendation engines that rely solely on collaborative filtering or content-based filtering, this system uses:

Fuzzy Logic Approach: Captures human-like reasoning by modeling imprecise user preferences, such as “likes action movies moderately” or “prefers comedies strongly.” Fuzzy inference rules are used to calculate membership scores for each genre and movie.

Artificial Neural Networks (ANN): Learns complex patterns from historical user ratings to predict unseen movie preferences with high accuracy.

Hybrid Approach (Fuzzy + ANN): Combines the reasoning capability of fuzzy logic with the predictive power of ANN to provide more accurate and personalized recommendations.

The system is trained on the MovieLens 10M dataset, which contains 10 million ratings from thousands of users across hundreds of movies.
Key attributes of the dataset include:
User Data: User ID, demographics (age, gender, occupation)
Movie Data: Movie ID, title, genres
Rating Data: User ratings (1–5 stars)

## Project Workflow
1) Data Collection & Preprocessing
   Load MovieLens 10M dataset.
   Handle missing values, encode categorical data, and normalize ratings.

2) Fuzzy Logic Model Development
   Define fuzzy sets for user preferences and movie attributes.
   Establish fuzzy rules to compute recommendation scores.
   Aggregate fuzzy outputs to produce preliminary recommendations.

3) ANN Model Development
   Build a neural network to learn latent features of users and movies.
   Train the ANN on the user-movie rating matrix.
   Evaluate performance using metrics like RMSE and MAE.

4) Hybrid Model Integration
   Combine fuzzy inference scores with ANN predictions.
   Generate final ranked movie recommendations.

5) Evaluation & Testing
   Compare predictions with actual user ratings.
   Measure accuracy, precision, recall, and F1-score.

## Fuzzy Rules for Movie Recommendation
### A) User Preference vs. Genre
#### 1. Action Genre

IF Action preference is Very High AND Movie genre is Action THEN Recommendation Score is Very High
Example: User loves action. Movie: “Avengers” → Recommendation: Very High

IF Action preference is High AND Movie genre is Action THEN Recommendation Score is High
Example: User likes action. Movie: “Fast & Furious” → Recommendation: High

IF Action preference is Medium AND Movie genre is Action THEN Recommendation Score is Medium
Example: User sometimes likes action. Movie: “Mission Impossible” → Recommendation: Medium

IF Action preference is Low AND Movie genre is Action THEN Recommendation Score is Low
Example: User rarely watches action. Movie: “Die Hard” → Recommendation: Low

IF Action preference is Very Low AND Movie genre is Action THEN Recommendation Score is Very Low
Example: User dislikes action. Movie: “John Wick” → Recommendation: Very Low

#### 2. Comedy Genre

IF Comedy preference is Very High AND Movie genre is Comedy THEN Recommendation Score is Very High
Example: User loves comedy. Movie: “The Hangover” → Recommendation: Very High

IF Comedy preference is High AND Movie genre is Comedy THEN Recommendation Score is High
Example: User likes comedy. Movie: “Friends: The Movie” → Recommendation: High

IF Comedy preference is Medium AND Movie genre is Comedy THEN Recommendation Score is Medium
Example: User sometimes enjoys comedy. Movie: “Game Night” → Recommendation: Medium

IF Comedy preference is Low AND Movie genre is Comedy THEN Recommendation Score is Low
Example: User rarely watches comedy. Movie: “The Mask” → Recommendation: Low

IF Comedy preference is Very Low AND Movie genre is Comedy THEN Recommendation Score is Very Low
Example: User dislikes comedy. Movie: “Dumb & Dumber” → Recommendation: Very Low

#### 3. Romance Genre

IF Romance preference is Very High AND Movie genre is Romance THEN Recommendation Score is Very High
Example: User loves romance. Movie: “The Notebook” → Recommendation: Very High

IF Romance preference is High AND Movie genre is Romance THEN Recommendation Score is High
Example: User likes romance. Movie: “Titanic” → Recommendation: High

IF Romance preference is Medium AND Movie genre is Romance THEN Recommendation Score is Medium
Example: User sometimes watches romance. Movie: “Pride & Prejudice” → Recommendation: Medium

IF Romance preference is Low AND Movie genre is Romance THEN Recommendation Score is Low
Example: User rarely watches romance. Movie: “Dear John” → Recommendation: Low

IF Romance preference is Very Low AND Movie genre is Romance THEN Recommendation Score is Very Low
Example: User dislikes romance. Movie: “Twilight” → Recommendation: Very Low

#### 4. Thriller Genre

IF Thriller preference is Very High AND Movie genre is Thriller THEN Recommendation Score is Very High
Example: User loves thrillers. Movie: “Se7en” → Recommendation: Very High

IF Thriller preference is High AND Movie genre is Thriller THEN Recommendation Score is High
Example: User likes thrillers. Movie: “Gone Girl” → Recommendation: High

IF Thriller preference is Medium AND Movie genre is Thriller THEN Recommendation Score is Medium
Example: User sometimes watches thrillers. Movie: “The Sixth Sense” → Recommendation: Medium

IF Thriller preference is Low AND Movie genre is Thriller THEN Recommendation Score is Low
Example: User rarely watches thrillers. Movie: “The Ring” → Recommendation: Low

IF Thriller preference is Very Low AND Movie genre is Thriller THEN Recommendation Score is Very Low
Example: User dislikes thrillers. Movie: “Saw” → Recommendation: Very Low

#### 5. Sci-Fi Genre

IF Sci-Fi preference is Very High AND Movie genre is Sci-Fi THEN Recommendation Score is Very High
Example: User loves Sci-Fi. Movie: “Interstellar” → Recommendation: Very High

IF Sci-Fi preference is High AND Movie genre is Sci-Fi THEN Recommendation Score is High
Example: User likes Sci-Fi. Movie: “The Matrix” → Recommendation: High

IF Sci-Fi preference is Medium AND Movie genre is Sci-Fi THEN Recommendation Score is Medium
Example: User sometimes watches Sci-Fi. Movie: “Avatar” → Recommendation: Medium

IF Sci-Fi preference is Low AND Movie genre is Sci-Fi THEN Recommendation Score is Low
Example: User rarely watches Sci-Fi. Movie: “Jupiter Ascending” → Recommendation: Low

IF Sci-Fi preference is Very Low AND Movie genre is Sci-Fi THEN Recommendation Score is Very Low
Example: User dislikes Sci-Fi. Movie: “Transformers” → Recommendation: Very Low

#### 6. Drama Genre

IF Drama preference is Very High AND Movie genre is Drama THEN Recommendation Score is Very High
Example: User loves drama. Movie: “Forrest Gump” → Recommendation: Very High

IF Drama preference is High AND Movie genre is Drama THEN Recommendation Score is High
Example: User likes drama. Movie: “The Pursuit of Happyness” → Recommendation: High

IF Drama preference is Medium AND Movie genre is Drama THEN Recommendation Score is Medium
Example: User sometimes watches drama. Movie: “A Beautiful Mind” → Recommendation: Medium

IF Drama preference is Low AND Movie genre is Drama THEN Recommendation Score is Low
Example: User rarely watches drama. Movie: “The Fault in Our Stars” → Recommendation: Low

IF Drama preference is Very Low AND Movie genre is Drama THEN Recommendation Score is Very Low
Example: User dislikes drama. Movie: “Room” → Recommendation: Very Low

#### 7. Horror Genre

IF Horror preference is Very High AND Movie genre is Horror THEN Recommendation Score is Very High
Example: User loves horror. Movie: “The Conjuring” → Recommendation: Very High

IF Horror preference is High AND Movie genre is Horror THEN Recommendation Score is High
Example: User likes horror. Movie: “IT” → Recommendation: High

IF Horror preference is Medium AND Movie genre is Horror THEN Recommendation Score is Medium
Example: User sometimes watches horror. Movie: “A Quiet Place” → Recommendation: Medium

IF Horror preference is Low AND Movie genre is Horror THEN Recommendation Score is Low
Example: User rarely watches horror. Movie: “Annabelle” → Recommendation: Low

IF Horror preference is Very Low AND Movie genre is Horror THEN Recommendation Score is Very Low
Example: User dislikes horror. Movie: “Paranormal Activity” → Recommendation: Very Low

### B) Popularity & Genre Match
IF Popularity is High AND Genre Match is Excellent THEN Recommendation Score is Very High
Example: A blockbuster action movie that perfectly matches user’s action preference → Recommendation: Very High

IF Popularity is Medium AND Genre Match is Excellent THEN Recommendation Score is High
Example: Moderately popular action movie that fits user’s action preference → Recommendation: High

IF Popularity is Low AND Genre Match is Excellent THEN Recommendation Score is Medium
Example: Niche movie that fits user’s favorite genre → Recommendation: Medium

IF Popularity is High AND Genre Match is Average THEN Recommendation Score is High
Example: Popular action movie but user’s preference is medium → Recommendation: High

IF Popularity is Medium AND Genre Match is Average THEN Recommendation Score is Medium
Example: Moderately popular movie with partial genre match → Recommendation: Medium

IF Popularity is Low AND Genre Match is Average THEN Recommendation Score is Low
Example: Less known movie with partial genre match → Recommendation: Low

IF Popularity is High AND Genre Match is Poor THEN Recommendation Score is Medium
Example: Popular movie outside user’s preferred genre → Recommendation: Medium

IF Popularity is Medium AND Genre Match is Poor THEN Recommendation Score is Low
Example: Moderately popular movie with poor genre match → Recommendation: Low

IF Popularity is Low AND Genre Match is Poor THEN Recommendation Score is Very Low
Example: Obscure movie with poor genre match → Recommendation: Very Low

### C) User Watch History

IF User has watched the movie AND Liked it THEN Recommendation Score is High for similar movies
Example: User liked “Avengers” → Recommend similar action movies → Recommendation: High

IF User has watched the movie AND Disliked it THEN Recommendation Score is Very Low
Example: User disliked “Transformers” → Do not recommend similar Sci-Fi movies → Recommendation: Very Low

IF User has not watched similar genre movies AND Preference is High THEN Recommendation Score is Medium
Example: User loves thrillers but hasn’t watched “Gone Girl” → Recommend cautiously → Recommendation: Medium

IF User has not watched similar genre movies AND Preference is Medium THEN Recommendation Score is Low
Example: User sometimes enjoys romance but hasn’t watched “Pride & Prejudice” → Recommendation: Low

IF User has watched similar genre movies AND Mostly Liked them THEN Recommendation Score is High
Example: User enjoyed multiple action movies → Recommend new action movie → Recommendation: High

IF User has watched similar genre movies AND Mostly Disliked them THEN Recommendation Score is Low
Example: User watched several comedies and disliked them → Recommendation: Low

IF User has watched many movies in the genre AND Preference is Very High THEN Recommendation Score is Very High
Example: User loves Sci-Fi and watched multiple favorites → Recommendation: Very High

IF User has watched many movies in the genre AND Preference is Low THEN Recommendation Score is Medium
Example: User rarely watches thrillers but has watched some → Recommendation: Medium

### D) Hybrid (Fuzzy + ANN)

IF Fuzzy Recommendation is Very High AND ANN Predicted Score is High THEN Final Recommendation Score is Very High
Example: Fuzzy logic strongly recommends “Interstellar” and ANN predicts a high score → Final Recommendation: Very High

IF Fuzzy Recommendation is High AND ANN Predicted Score is High THEN Final Recommendation Score is High
Example: Fuzzy logic recommends “The Matrix” and ANN predicts high → Final Recommendation: High

IF Fuzzy Recommendation is Medium AND ANN Predicted Score is Medium THEN Final Recommendation Score is Medium
Example: Fuzzy logic gives medium score to “Avatar” and ANN also predicts medium → Final Recommendation: Medium

IF Fuzzy Recommendation is Low AND ANN Predicted Score is Medium THEN Final Recommendation Score is Medium
Example: Fuzzy logic gives low score to “Jupiter Ascending” but ANN predicts medium → Final Recommendation: Medium

IF Fuzzy Recommendation is High AND ANN Predicted Score is Low THEN Final Recommendation Score is Medium
Example: Fuzzy logic recommends “Titanic” highly but ANN predicts low → Final Recommendation: Medium

IF Fuzzy Recommendation is Low AND ANN Predicted Score is Low THEN Final Recommendation Score is Very Low
Example: Fuzzy logic gives low score to “Paranormal Activity” and ANN also predicts low → Final Recommendation: Very Low

## Membership Functions
1. User Preference Membership Functions
   User preference indicates how much a user likes a particular genre. Values typically range from 0 to 10 (0 = dislikes, 10 = loves).
   
   | Fuzzy Label | Range (0–10) | MF Shape   | Example                          |
   | ----------- | ------------ | ---------- | -------------------------------- |
   | Very Low    | 0 – 2        | Triangular | User dislikes the genre          |
   | Low         | 1 – 4        | Triangular | User rarely watches the genre    |
   | Medium      | 3 – 7        | Triangular | User sometimes watches the genre |
   | High        | 6 – 9        | Triangular | User likes the genre             |
   | Very High   | 8 – 10       | Triangular | User loves the genre             |


2. Popularity Membership Functions
   Popularity measures how popular a movie is (e.g., based on ratings, views). Range: 0–100 (%).
   
   | Fuzzy Label | Range (0–100) | MF Shape   | Example                       |
   | ----------- | ------------- | ---------- | ----------------------------- |
   | Low         | 0 – 40        | Triangular | Less known or unpopular movie |
   | Medium      | 30 – 70       | Triangular | Moderately popular movie      |
   | High        | 60 – 100      | Triangular | Highly popular movie          |

3. Genre Match Membership Functions
   Genre match indicates how well a movie’s genre aligns with user preference. Range: 0–1 (0 = no match, 1 = perfect match).
   
  | Fuzzy Label | Range     | MF Shape   | Example                                    |
  | ----------- | --------- | ---------- | ------------------------------------------ |
  | Poor        | 0 – 0.4   | Triangular | Little overlap with user’s favorite genres |
  | Average     | 0.3 – 0.7 | Triangular | Some alignment with user’s preference      |
  | Excellent   | 0.6 – 1   | Triangular | Perfect match with user’s favorite genre   |

4. Recommendation Score Membership Functions
   Recommendation Score (output) indicates how strongly a movie should be recommended. Range: 0–10.

  | Fuzzy Label | Range  | MF Shape   | Example                 |
  | ----------- | ------ | ---------- | ----------------------- |
  | Very Low    | 0 – 2  | Triangular | Do not recommend        |
  | Low         | 1 – 4  | Triangular | Recommend cautiously    |
  | Medium      | 3 – 7  | Triangular | Moderate recommendation |
  | High        | 6 – 9  | Triangular | Recommend confidently   |
  | Very High   | 8 – 10 | Triangular | Strongly recommend      |

5.  ANN Predicted Score Membership Functions
   ANN predicted score is similar to recommendation score. Range: 0–10.

  | Fuzzy Label | Range  | MF Shape   | Example                     |
  | ----------- | ------ | ---------- | --------------------------- |
  | Low         | 0 – 4  | Triangular | ANN predicts poor match     |
  | Medium      | 3 – 7  | Triangular | ANN predicts moderate match |
  | High        | 6 – 10 | Triangular | ANN predicts good match     |


## Sample Input and Output

### Sample Input

```json
{
  "User Preferences": {
    "Action": "High",
    "Comedy": "Medium",
    "Romance": "Low",
    "Thriller": "Medium"
  },
  "Previously Watched Movies": [
    "The Dark Knight",
    "Inception",
    "Titanic"
  ]
}
```

### Sample Output

```json
{
  "Recommended Movies": [
    {"Movie": "Interstellar", "Score": 0.87},
    {"Movie": "The Prestige", "Score": 0.83},
    {"Movie": "Shutter Island", "Score": 0.81}
  ]
}
```

## Features of the Project:
   Provides personalized movie recommendations based on fuzzy human-like reasoning.
   Uses ANN to capture hidden patterns in user ratings.
   Hybrid approach increases accuracy compared to single-method recommenders.
   Can handle imprecise or uncertain user inputs.
   Scalable to large datasets like MovieLens 1M.

## Enhancements for Future Development:
   Incorporate Additional Data: Use social media preferences, movie reviews, and tags for improved recommendations.
   Real-Time Recommendations: Update suggestions dynamically as users rate more movies.
   Explainable Recommendations: Provide textual explanations for why a movie is recommended.
   Deep Learning Models: Replace ANN with deep learning architectures like Autoencoders or Transformers for higher accuracy.
   Web Application: Deploy as a web app for interactive user recommendations.

## Use Cases:
   Streaming Platforms: Personalized movie suggestions for Netflix, Prime Video, or Disney+.
   Movie Enthusiasts: Discover new movies based on fuzzy preferences.
   Recommendation System Research: Serves as a practical example of hybrid soft computing approaches.

## Conclusion:
This Fuzzy Movie Recommendation System leverages Soft Computing techniques to model uncertain user preferences and provide accurate, personalized movie suggestions. By combining Fuzzy Logic with Artificial Neural Networks, the system bridges human-like reasoning with data-driven predictions, making it a robust and practical recommendation engine for modern applications.
