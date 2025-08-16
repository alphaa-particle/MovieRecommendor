import streamlit as st
import pickle
import pandas as pd
import requests
import time
import base64

# --- API KEYS ---
TMDB_API_KEY = "5e9d6560e9345bbd9516f919d2a3e75c"
OMDB_API_KEY = "73808edc"

# --- DATA LOADING ---
movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))


# --- DYNAMIC BACKGROUND ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def get_background_posters():
    """Fetches posters for the dynamic background."""
    try:
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page=1"
        data = requests.get(url).json()
        poster_urls = [f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" for movie in data.get('results', []) if movie.get('poster_path')]
        return poster_urls[:10] # Get top 10 for the collage
    except Exception:
        return []

# --- API FETCH FUNCTIONS ---

def fetch_movie_details(movie_id, movie_title):
    """Fetches extensive movie details."""
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=reviews"
        data = requests.get(url).json()
        if 'id' in data:
            poster = "https://image.tmdb.org/t/p/w500" + data.get('poster_path', '') if data.get('poster_path') else ""
            overview = data.get('overview', 'No overview available.')
            release_date = data.get('release_date', 'N/A')
            rating = data.get('vote_average', 0)
            genres = [genre['name'] for genre in data.get('genres', [])]
            tagline = data.get('tagline', '')
            runtime = data.get('runtime', 0)
            revenue = data.get('revenue', 0)
            reviews = data.get('reviews', {}).get('results', [])
            top_review = reviews[0] if reviews else None
            return poster, overview, release_date, rating, genres, tagline, runtime, revenue, top_review
    except Exception: pass
    try:
        url = f"http://www.omdbapi.com/?t={movie_title}&apikey={OMDB_API_KEY}"
        data = requests.get(url).json()
        if data.get("Response") == "True":
            poster = data.get("Poster") if data.get("Poster") != "N/A" else ""
            overview = data.get("Plot", "No overview available.")
            release_date = data.get("Released", "N/A")
            rating = float(data.get("imdbRating", "0")) if data.get("imdbRating") != "N/A" else 0
            genres = [genre.strip() for genre in data.get("Genre", "").split(',')]
            runtime_str = data.get("Runtime", "0 min").replace(" min", "")
            runtime = int(runtime_str) if runtime_str.isdigit() else 0
            return poster, overview, release_date, rating, genres, "", runtime, 0, None
    except Exception: pass
    return "https://via.placeholder.com/500x750.png?text=Info+Not+Found", "Could not fetch details.", "N/A", 0, [], "", 0, 0, None


# --- RECOMMENDATION LOGIC ---

def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        recommended_movies_data = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            movie_title = movies.iloc[i[0]].title
            details = fetch_movie_details(movie_id, movie_title)
            recommended_movies_data.append({
                "title": movie_title, "poster": details[0], "overview": details[1],
                "release_date": details[2], "rating": details[3], "genres": details[4],
                "tagline": details[5], "runtime": details[6], "revenue": details[7], "review": details[8]
            })
        return recommended_movies_data
    except IndexError:
        st.error("Movie not found in the dataset. Please select another one.")
        return []


# --- UI & STYLING (CSS) ---

st.set_page_config(layout="wide", page_title="CineRecs - Movie Recommender")

# --- Dynamic Background CSS ---
background_posters = get_background_posters()
background_style = ""
if background_posters:
    style_blocks = ""
    for i, url in enumerate(background_posters):
        # Use double curly braces to escape them in the f-string for CSS
        style_blocks += f"""
            .stApp::before:nth-of-type({i + 1}) {{
                background-image: url('{url}');
                animation-delay: {i * 5}s;
            }}
        """
    # CORRECTED: Separated the main CSS from the f-string to avoid parsing errors
    main_css = """
        @keyframes drift {
            0% { transform: translate(0, 0) scale(1.1); opacity: 0; }
            10% { opacity: 0.1; }
            90% { opacity: 0.1; }
            100% { transform: translate(calc(var(--x-end) * 1px), calc(var(--y-end) * 1px)) scale(1.3); opacity: 0; }
        }
        .stApp::before {
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background-size: cover;
            background-position: center;
            opacity: 0;
            z-index: -2;
            animation: drift 50s infinite linear;
            --x-end: 100;
            --y-end: -100;
        }
    """
    background_style = main_css + style_blocks

st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;700&display=swap" rel="stylesheet">

<style>
    {background_style}
    
    /* --- Keyframes for Animations --- */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes vault-unlock {{
        0% {{ stroke-dashoffset: 283; }}
        50% {{ stroke-dashoffset: 0; }}
        100% {{ stroke-dashoffset: -283; }}
    }}
    @keyframes inner-spin {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}

    /* --- General Styling --- */
    .stApp {{
        background-color: rgba(43, 43, 43, 0.85); /* Semi-transparent charcoal */
        backdrop-filter: blur(10px);
        color: #F5F5DC;
        font-family: 'Raleway', sans-serif;
    }}
    .stApp::after {{ /* Dark overlay for readability */
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: radial-gradient(circle, rgba(43,43,43,0.6) 0%, rgba(43,43,43,0.9) 100%);
        z-index: -1;
    }}

    /* --- Header Styling --- */
    .title {{ font-weight: 700; font-size: 3.5rem; color: #FFFFFF; text-align: center; padding: 1rem 0; animation: fadeIn 1s ease-out; }}
    .title .highlight {{ color: #D4AF37; }}
    .subtitle {{ text-align: center; color: #BEBEBE; font-size: 1.2rem; margin-bottom: 2.5rem; animation: fadeIn 1.5s ease-out; }}

    /* --- Interactive Search/Input Block --- */
    .stTextInput > div > div > input {{
        background-color: rgba(54, 54, 54, 0.8);
        color: #F5F5DC; border: 1px solid #555555; border-radius: 10px; padding: 1rem; transition: all 0.3s ease;
    }}
    .stTextInput > div > div > input:focus {{ border-color: #D4AF37; box-shadow: 0 0 10px rgba(212, 175, 55, 0.5); }}
    .stButton>button {{
        background: #D4AF37; color: #2B2B2B; border: none; border-radius: 10px; padding: 12px 30px;
        font-size: 16px; font-weight: 700; transition: all 0.3s ease; display: block; margin: 1rem auto 0 auto;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
    }}
    .stButton>button:hover {{ transform: scale(1.05); background: #EACD69; }}
    
    /* --- Custom SVG Loader Animation --- */
    .loader-container {{ text-align: center; padding: 2rem; }}
    .loader-svg {{ width: 80px; height: 80px; }}
    .vault-circle {{
        stroke: #D4AF37; stroke-width: 5; fill: transparent;
        stroke-dasharray: 283; animation: vault-unlock 2s infinite linear;
    }}
    .inner-circle {{
        stroke: #555555; stroke-width: 15; fill: transparent;
        animation: inner-spin 4s infinite linear;
    }}
    .loader-text {{ color: #BEBEBE; margin-top: 1rem; font-size: 1.1rem; }}

    /* --- Recommendation Card --- */
    .movie-container {{
        background-color: rgba(54, 54, 54, 0.8); backdrop-filter: blur(5px);
        border-radius: 15px; padding: 20px; margin-bottom: 20px; border: 1px solid #555555;
        animation: fadeIn 0.5s ease-out forwards; opacity: 0;
    }}
    .poster-img {{ border-radius: 10px; }}
    .movie-title {{ font-family: 'Raleway', sans-serif; color: #FFFFFF; font-size: 28px; font-weight: bold; }}
    .movie-tagline {{ color: #BEBEBE; font-style: italic; margin-bottom: 1rem; }}
    .movie-meta, .movie-stats {{ color: #BEBEBE; font-size: 14px; margin-bottom: 15px; }}
    .movie-overview {{ color: #F5F5DC; line-height: 1.6; }}
    .genre-tag {{ background-color: #555555; color: #F5F5DC; padding: 5px 12px; border-radius: 15px; font-size: 12px; margin-right: 5px; display: inline-block; margin-top: 5px; }}
    .review-box {{ background-color: rgba(43, 43, 43, 0.8); border-left: 3px solid #D4AF37; padding: 15px; border-radius: 8px; margin-top: 1rem; }}
    .review-author {{ font-weight: bold; color: #FFFFFF; }}
    .review-content {{ color: #BEBEBE; font-size: 14px; max-height: 100px; overflow-y: auto; }}
</style>
""", unsafe_allow_html=True)


# --- STREAMLIT APP LAYOUT ---

st.markdown("<h1 class='title'>Cine<span class='highlight'>Recs</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Discover films you'll love, based on your favorites.</p>", unsafe_allow_html=True)

search_term = st.text_input("Search for a movie...", "", key="search_bar")

if search_term:
    filtered_movies = movies[movies['title'].str.contains(search_term, case=False)]['title'].tolist()
    selected_movie = st.selectbox("Select your movie from the list:", filtered_movies) if filtered_movies else None
    if not filtered_movies: st.warning("No movies found with that name. Try another search.")
else:
    selected_movie = st.selectbox("Or select a movie from the full list:", movies['title'].values, index=None, placeholder="Select a movie...")

if st.button("Get Recommendations", key="rec_button") and selected_movie:
    loader_placeholder = st.empty()
    loading_messages = [
        "Analyzing cinematic DNA...",
        "Cross-referencing genres and themes...",
        "Unlocking the vault of recommendations...",
        "Curating your personalized film selection..."
    ]
    for message in loading_messages:
        loader_placeholder.markdown(f"""
            <div class="loader-container">
                <svg class="loader-svg" viewBox="0 0 100 100">
                    <circle class="inner-circle" cx="50" cy="50" r="35" />
                    <circle class="vault-circle" cx="50" cy="50" r="45" />
                </svg>
                <p class="loader-text">{message}</p>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(0.9)
    
    recommendations = recommend(selected_movie)
    loader_placeholder.empty()

    if recommendations:
        st.write("---")
        st.subheader(f"Because you watched '{selected_movie}', you might also like...")
        for i, movie in enumerate(recommendations):
            with st.container():
                st.markdown(f'<div class="movie-container" style="animation-delay: {i * 0.1}s;">', unsafe_allow_html=True)
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f'<img src="{movie["poster"]}" class="poster-img" style="width:100%">', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<p class="movie-title">{movie["title"]}</p>', unsafe_allow_html=True)
                    if movie['tagline']: st.markdown(f'<p class="movie-tagline">"{movie["tagline"]}"</p>', unsafe_allow_html=True)
                    st.markdown(f"""<p class="movie-meta"><strong>⭐ Rating:</strong> {movie['rating']:.1f}/10 &nbsp;&nbsp;|&nbsp;&nbsp; <strong>🗓️ Released:</strong> {movie['release_date']}</p>""", unsafe_allow_html=True)
                    genres_html = "".join([f'<span class="genre-tag">{genre}</span>' for genre in movie['genres']])
                    st.markdown(f'<div>{genres_html}</div>', unsafe_allow_html=True)
                    st.markdown(f"""<p class="movie-stats" style="margin-top: 1rem;"><strong>⏳ Runtime:</strong> {movie['runtime']} min &nbsp;&nbsp;|&nbsp;&nbsp; <strong>💰 Box Office:</strong> ${movie['revenue']:,}</p>""", unsafe_allow_html=True)
                    st.markdown(f'<p class="movie-overview">{movie["overview"]}</p>', unsafe_allow_html=True)
                    if movie['review']:
                        review = movie['review']
                        author = review['author']
                        content = review['content'][:400] + '...' if len(review['content']) > 400 else review['content']
                        st.markdown(f"""<div class="review-box"><p class="review-author">Top Review by {author}:</p><p class="review-content">"{content}"</p></div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
elif st.session_state.get('rec_button'):
    st.warning("Please select a movie to get recommendations.")
