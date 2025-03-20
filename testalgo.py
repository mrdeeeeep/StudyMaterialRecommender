import sqlite3
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
import nltk
from collections import Counter
from nltk.corpus import stopwords
from nltk.util import ngrams
import string
import requests

nltk.download("averaged_perceptron_tagger")
nltk.download("stopwords")

# Load stopwords
stop_words = set(stopwords.words("english")) | set(string.punctuation)

API_KEY = "AIzaSyArek7PgslU7vTIO52sYKgw-NcBQonbvFU"
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

def connect_db():
    """Connect to the SQLite database"""
    conn = sqlite3.connect('study_materials.db')
    print("Database connected successfully")
    return conn

def get_db_schema():
    """Print the database schema"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\nDatabase Schema:")
        print("-" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
                
    finally:
        conn.close()

def create_tables():
    """Create necessary tables if they do not exist"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                relevance_rating REAL,
                click_count INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_interactions (
                id INTEGER PRIMARY KEY,
                video_id TEXT NOT NULL,
                rating REAL,
                click_count INTEGER,
                FOREIGN KEY(video_id) REFERENCES videos(video_id)
            )
        """)
        
        conn.commit()
    finally:
        conn.close()

def calculate_video_score(relevance_rating, click_count, w1=0.7, w2=0.3):
    """
    Calculate a composite score for video ranking
    w1: weight for relevance rating (default 70%)
    w2: weight for click count (default 30%)
    """
    if relevance_rating is None:
        relevance_rating = 0
    if click_count is None:
        click_count = 0
    
    # Normalize relevance rating to 0-1 scale (assuming rating is 1-5)
    normalized_rating = relevance_rating / 5.0
    
    # Get score based on weighted sum
    return (w1 * normalized_rating) + (w2 * click_count)

def get_ranked_videos():
    """Get videos ranked by their composite score"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Check if the video table has data
        cursor.execute("SELECT COUNT(*) FROM video")
        count = cursor.fetchone()[0]
        print(f"Number of records in video table: {count}")
        
        # Get all videos with their relevance ratings and click counts
        cursor.execute("""
            SELECT 
                video_id,
                title,
                relevance_rating,
                click_count
            FROM video
        """)
        
        videos = cursor.fetchall()
        
        # Debug print to check fetched data
        print("\nFetched Videos:")
        for video in videos:
            print(video)
        
        # Calculate scores and store in list
        ranked_videos = []
        for video in videos:
            video_id, title, relevance_rating, click_count = video
            score = calculate_video_score(relevance_rating, click_count)
            ranked_videos.append({
                'video_id': video_id,
                'title': title,
                'relevance_rating': round(relevance_rating if relevance_rating else 0, 2),
                'click_count': click_count,
                'score': round(score, 3)
            })
        
        # Sort videos by score in descending order
        ranked_videos.sort(key=lambda x: x['score'], reverse=True)
        
        return ranked_videos
        
    finally:
        conn.close()

def get_top_ranked_videos():
    """Get top 3 ranked videos with relevance score > 5 or click count > 0"""
    ranked_videos = get_ranked_videos()
    filtered_videos = [video for video in ranked_videos if video['relevance_rating'] > 0 or video['click_count'] > 0]
    return filtered_videos[:3]

def search_youtube_videos(keyword, max_results=5):
    """Search for YouTube videos using a keyword"""
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": max_results,
        "key": API_KEY
    }
    response = requests.get(SEARCH_URL, params=params)
    return response.json()

def clean_text(text):
    """Lowercase, remove punctuation, and split into words"""
    words = text.lower().translate(str.maketrans("", "", string.punctuation)).split()
    return [w for w in words if w not in stop_words and len(w) > 2]  # Keep words with >2 chars

def extract_top_keywords(texts, n_keywords=5):
    """Extracts better keywords using POS tagging, bigrams, and TF-IDF"""
    # Convert text into TF-IDF matrix
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(texts)

    # Get feature names (words)
    feature_array = np.array(vectorizer.get_feature_names_out())
    
    # Get TF-IDF scores
    tfidf_sorting = np.argsort(X.toarray()).flatten()[::-1]
    
    # Extract top words
    top_words = feature_array[tfidf_sorting]

    # Keep only nouns, adjectives, verbs
    pos_filtered = [word for word, pos in nltk.pos_tag(top_words) if pos.startswith(("NN", "JJ", "VB"))]

    # Extract bigrams & trigrams
    all_words = [clean_text(text) for text in texts]
    flat_words = [word for sublist in all_words for word in sublist]
    bigrams = list(ngrams(flat_words, 2))
    trigrams = list(ngrams(flat_words, 3))

    # Count word occurrences
    word_freq = Counter(flat_words)
    bigram_freq = Counter(bigrams)
    trigram_freq = Counter(trigrams)

    # Combine words & phrases
    final_keywords = pos_filtered[:n_keywords]  # Start with best single words
    final_keywords += [" ".join(b) for b, _ in bigram_freq.most_common(2)]  # Add top bigrams
    final_keywords += [" ".join(t) for t, _ in trigram_freq.most_common(1)]  # Add top trigram

    return final_keywords[:n_keywords]  # Return refined top keywords

def cluster_videos(videos):
    """Cluster videos using TF-IDF and K-Means"""
    # Preprocess metadata (combine title + tags)
    corpus = [video["title"] for video in videos]

    # Convert text into TF-IDF feature vectors
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(corpus)

    # Apply K-Means Clustering
    num_clusters = 2  # Adjust based on your dataset size
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(X)

    # Assign cluster labels to videos
    for i, video in enumerate(videos):
        video["cluster"] = kmeans.labels_[i]

    # Group videos by cluster
    clusters = defaultdict(list)
    for video in videos:
        clusters[video["cluster"]].append(video)

    # Print grouped clusters and extract keywords
    for cluster_id, vids in clusters.items():
        print(f"\nCluster {cluster_id}:")
        for v in vids:
            print(f"  - {v['title']} (Relevance Rating: {v['relevance_rating']}, Clicks: {v['click_count']})")
        
        # Extract keywords for each cluster
        texts = [v["title"] for v in vids]
        keywords = extract_top_keywords(texts)
        combined_keyword = " ".join(keywords)
        print(f"Cluster {cluster_id} Combined Keyword: {combined_keyword}")
        
        # Search for new videos using combined keyword
        new_videos = []
        results = search_youtube_videos(combined_keyword)
        for item in results["items"]:
            new_videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "tags": combined_keyword  # Associate with the combined keyword
            })
        
        print(f"\nNewly Retrieved Videos for Cluster {cluster_id}:")
        for video in new_videos:
            print(f"  - {video['title']} (Tags: {video['tags']})")

def main():
    """Test the ranking and clustering system"""
    create_tables()  # Ensure tables exist
    top_videos = get_top_ranked_videos()
    
    print("\nTop Ranked Videos (by score):")
    print("-" * 80)
    print(f"{'Title':<50} | {'Relevance Rating':<17} | {'Clicks':<7} | {'Score':<6}")
    print("-" * 80)
    
    for video in top_videos:
        print(f"{video['title'][:50]:<50} | {video['relevance_rating']:<17} | {video['click_count']:<7} | {video['score']:<6}")
    
    # Cluster the top ranked videos and get cluster keywords
    cluster_videos(top_videos)

if __name__ == "__main__":
    main()