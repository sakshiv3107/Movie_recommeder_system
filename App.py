import streamlit as st
from PIL import Image
import json
from Classifier import KNearestNeighbours
from bs4 import BeautifulSoup
import requests, io
import PIL.Image
from urllib.request import urlopen

# Load data
with open('./Data/movie_data.json', 'r+', encoding='utf-8') as f:
    data = json.load(f)
with open('./Data/movie_titles.json', 'r+', encoding='utf-8') as f:
    movie_titles = json.load(f)
hdr = {'User-Agent': 'Mozilla/5.0'}

# Function to fetch movie poster
def movie_poster_fetcher(imdb_link):
    url_data = requests.get(imdb_link, headers=hdr).text
    s_data = BeautifulSoup(url_data, 'html.parser')
    imdb_dp = s_data.find("meta", property="og:image")
    movie_poster_link = imdb_dp.attrs['content']
    u = urlopen(movie_poster_link)
    raw_data = u.read()
    image = PIL.Image.open(io.BytesIO(raw_data))
    image = image.resize((158, 301), )
    st.image(image, use_container_width=False)

# Function to get movie info
def get_movie_info(imdb_link):
    try:
        url_data = requests.get(imdb_link, headers=hdr).text
        s_data = BeautifulSoup(url_data, 'html.parser')
        
        # Check if "og:description" meta tag exists
        imdb_content = s_data.find("meta", property="twitter:image:alt")
        if not imdb_content:
            print("Meta tag with 'description' not found!")
            return "Error: Metadata not found.", None, None, None
        
        # Debugging output
        print("Meta tag content:", imdb_content.attrs.get('content', ''))
        
        # Process description
        movie_descr = imdb_content.attrs.get('content', '').split('.')
        print("movie_descr:", movie_descr)  # Debugging step
        if len(movie_descr) < 3:
            return "Description incomplete", None, None, None
        
        movie_director = movie_descr[0]
        movie_cast = str(movie_descr[1]).replace('With', 'Cast: ').strip()
        movie_story = 'Story: ' + str(movie_descr[2]).strip() + '.'
        
        # Check for rating span
        rating_span = s_data.find("span", class_="sc-d541859f-3 dwhNqC")
        if not rating_span:
            return movie_director, movie_cast, movie_story, "Rating not found."
        
        rating = rating_span.text
        movie_rating = 'Total Rating count: ' + str(rating)
        
        return movie_director, movie_cast, movie_story, movie_rating

    except Exception as e:
        return f"Error: {e}", None, None, None

# KNN recommendation function
def KNN_Movie_Recommender(test_point, k):
    target = [0 for _ in movie_titles]
    model = KNearestNeighbours(data, target, test_point, k=k)
    model.fit()
    table = []
    for i in model.indices:
        table.append([movie_titles[i][0], movie_titles[i][2], data[i][-1]])
    return table

# Streamlit app configuration
st.set_page_config(page_title="Movie Recommender System", layout="wide")

# Run app
def run():
    # Add a sidebar for settings
    with st.sidebar:
        st.image('./meta/image.jpg', use_container_width=True)
        st.title("Movie Recommender System")
        st.markdown(
            '''
            **Features**:
            - Recommend movies based on selection or genres.
            - Fetch movie posters and details from IMDb.
            '''
        )
        st.markdown("### Made with ❤️ by Sakshi ")

    st.title("🎬 Welcome to the Movie Recommender System")
    st.markdown("Your personal movie discovery assistant!")

    # UI layout using columns
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Select Recommendation Type:")
        category = st.selectbox(
            '',
            ['--Select--', 'Movie-based Recommendation', 'Genre-based Recommendation']
        )

    if category == '--Select--':
        st.warning("Please select a recommendation type to proceed!")

    elif category == 'Movie-based Recommendation':
        # Movie-based Recommendations
        movies = [title[0] for title in movie_titles]
        selected_movie = st.selectbox('Choose a movie:', ['--Select--'] + movies)

        if selected_movie != '--Select--':
            no_of_reco = st.slider('Number of recommendations:', 5, 20, 10)

            # Fetch recommendations
            st.info(f"Generating {no_of_reco} recommendations for **{selected_movie}**...")
            genres = data[movies.index(selected_movie)]
            test_point = genres
            recommendations = KNN_Movie_Recommender(test_point, no_of_reco + 1)
            recommendations.pop(0)
            c = 0
            # Display recommendations
            st.subheader(f"Recommended Movies for '{selected_movie}':")
            # for idx, (movie, link, ratings) in enumerate(recommendations, start=1):
            #     with st.expander(f"Recommendation {idx}: {movie}"):
            #         poster = movie_poster_fetcher(link)
            #         colA, colB = st.columns([1, 2])
            #         with colA:
            #             st.image(poster)
            #         with colB:
            #             director, cast, story = get_movie_info(link)
            #             st.markdown(f"**Director:** {director}")
            #             st.markdown(f"**Cast:** {cast}")
            #             st.markdown(f"**Story:** {story}")
            #             st.markdown(f"**IMDb Rating:** {ratings} ⭐")
            for movie, link, ratings in recommendations:
                    c += 1
                    st.markdown(f"({c})[ {movie}]({link})")
                    movie_poster_fetcher(link)
                    director, cast, story, total_rat = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')

    elif category == 'Genre-based Recommendation':
        # Genre-based Recommendations
        genres = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama',
                  'Family', 'Fantasy', 'Film-Noir', 'Game-Show', 'History', 'Horror', 'Music', 'Musical',
                  'Mystery', 'News', 'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Thriller', 'War', 'Western']
        selected_genres = st.multiselect('Select genres:', genres)

        if selected_genres:
            imdb_score = st.slider('Choose minimum IMDb score:', 1, 10, 8)
            no_of_reco = st.number_input('Number of movies:', 5, 20, 5)

            test_point = [1 if genre in selected_genres else 0 for genre in genres]
            test_point.append(imdb_score)

            st.info(f"Fetching {no_of_reco} recommendations based on genres: {', '.join(selected_genres)}")
            recommendations = KNN_Movie_Recommender(test_point, no_of_reco)
            c = 0
            # Display recommendations
            st.subheader(f"Movies matching genres: {', '.join(selected_genres)}")
            for movie, link, ratings in recommendations:
                    c += 1
                    st.markdown(f"({c})[ {movie}]({link})")
                    movie_poster_fetcher(link)
                    director, cast, story, total_rat = get_movie_info(link)
                    st.markdown(director)
                    st.markdown(cast)
                    st.markdown(story)
                    st.markdown('IMDB Rating: ' + str(ratings) + '⭐')
    

run()
