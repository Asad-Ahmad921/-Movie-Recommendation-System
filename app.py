from flask import Flask, render_template, request
import pickle
import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor # Fast fetching 
from functools import lru_cache # Memory caching e

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = "6b39685774b904c52ed79c2de10c1c0c"

# --- DATA LOADING SECTION (Modified for Debugging) ---

new_dataset = pd.DataFrame()
similarity = None


print("Loading data files...")
movies_dict = pickle.load(open(os.path.join(BASE_DIR, 'movie_dict.pkl'), 'rb'))
new_dataset = pd.DataFrame(movies_dict)
similarity = pickle.load(open(os.path.join(BASE_DIR, 'similarity.pkl'), 'rb'))
print("Data loaded successfully!")
# -----------------------------------------------------

@lru_cache(maxsize=1000)
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=2) 
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        return "https://via.placeholder.com/500x750?text=No+Poster"
    except:
        return "https://via.placeholder.com/500x750?text=Error"

def recommend(movie):
    # Global similarity check
    if similarity is None:
        return ["Error: Similarity matrix not loaded"], []

    movie_list_lower = new_dataset['title'].str.lower().values
    if movie.lower() not in movie_list_lower:
        return [], []

    movie_index = new_dataset[new_dataset['title'].str.lower() == movie.lower()].index[0]
    distances = similarity[movie_index]

    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:11]

    recommended_movies = []
    movie_ids = []
    
    for i in movie_list:
        recommended_movies.append(new_dataset.iloc[i[0]]['title'])
        try:
            movie_ids.append(new_dataset.iloc[i[0]]['id'])
        except:
            movie_ids.append(new_dataset.iloc[i[0]]['movie_id'])

    with ThreadPoolExecutor() as executor:
        recommended_posters = list(executor.map(fetch_poster, movie_ids))

    return recommended_movies, recommended_posters

@app.route('/', methods=['GET', 'POST'])
def index():
    recommendations = []
    posters = []
    selected_movie = None

    if request.method == 'POST':
        selected_movie = request.form.get('movie_name')
        if selected_movie:
            recommendations, posters = recommend(selected_movie)

    movie_titles = new_dataset['title'].values if not new_dataset.empty else []
    
    return render_template(
        'index.html',
        movies=movie_titles,
        recommendations=recommendations,
        posters=posters,
        selected_movie=selected_movie,
        zip=zip
    )

if __name__ == '__main__':
    app.run(debug=True)