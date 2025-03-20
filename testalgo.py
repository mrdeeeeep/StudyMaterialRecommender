import sqlite3
from collections import defaultdict

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

def main():
    """Test the ranking system"""
    create_tables()  # Ensure tables exist
    ranked_videos = get_ranked_videos()
    
    print("\nRanked Videos (by score):")
    print("-" * 80)
    print(f"{'Title':<50} | {'Relevance Rating':<17} | {'Clicks':<7} | {'Score':<6}")
    print("-" * 80)
    
    for video in ranked_videos:
        print(f"{video['title'][:50]:<50} | {video['relevance_rating']:<17} | {video['click_count']:<7} | {video['score']:<6}")

if __name__ == "__main__":
    main()