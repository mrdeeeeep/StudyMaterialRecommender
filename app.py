from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
import logging
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_materials.db'
db = SQLAlchemy(app)

# API configurations
YOUTUBE_API_KEY = 'AIzaSyArek7PgslU7vTIO52sYKgw-NcBQonbvFU'
CORE_API_KEY = 'oIJb9cduRHMOYiVxFv2aQE8rXeTh1AjZ'
GOOGLE_API_KEY = 'AIzaSyArek7PgslU7vTIO52sYKgw-NcBQonbvFU'  # Same key for YouTube and Books

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
books_service = build('books', 'v1', developerKey=GOOGLE_API_KEY)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    videos = db.relationship('Video', backref='project', lazy=True, cascade='all, delete-orphan')
    papers = db.relationship('Paper', backref='project', lazy=True, cascade='all, delete-orphan')
    books = db.relationship('Book', backref='project', lazy=True, cascade='all, delete-orphan')

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    video_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    thumbnail_url = db.Column(db.String(200))
    channel_title = db.Column(db.String(100))
    published_at = db.Column(db.DateTime)
    view_count = db.Column(db.Integer)
    like_count = db.Column(db.Integer)
    category_id = db.Column(db.String(50))
    tags = db.Column(db.Text)
    duration = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    relevance_rating = db.Column(db.Integer, default=5)  # Rating out of 10
    click_count = db.Column(db.Integer, default=0)  # Track clicks
    is_visible = db.Column(db.Boolean, default=True)  # Track if content is hidden

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    core_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    abstract = db.Column(db.Text)
    authors = db.Column(db.Text)
    download_url = db.Column(db.String(500))
    pdf_url = db.Column(db.String(500))
    publisher = db.Column(db.String(200))
    year = db.Column(db.Integer)
    language = db.Column(db.String(10))
    doi = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    relevance_rating = db.Column(db.Integer, default=5)  # Rating out of 10
    click_count = db.Column(db.Integer, default=0)  # Track clicks
    is_visible = db.Column(db.Boolean, default=True)  # Track if content is hidden

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    google_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    subtitle = db.Column(db.String(500))
    authors = db.Column(db.Text)
    publisher = db.Column(db.String(200))
    published_date = db.Column(db.String(20))
    description = db.Column(db.Text)
    page_count = db.Column(db.Integer)
    categories = db.Column(db.Text)
    average_rating = db.Column(db.Float)
    ratings_count = db.Column(db.Integer)
    thumbnail = db.Column(db.String(500))
    preview_link = db.Column(db.String(500))
    info_link = db.Column(db.String(500))
    buy_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    relevance_rating = db.Column(db.Integer, default=5)  # Rating out of 10
    click_count = db.Column(db.Integer, default=0)  # Track clicks
    is_visible = db.Column(db.Boolean, default=True)  # Track if content is hidden

# Delete the existing database file if it exists
db_file = 'study_materials.db'
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Deleted existing database: {db_file}")

# Create all tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully")

def fetch_youtube_videos(search_query):
    try:
        # First, search for videos
        search_response = youtube.search().list(
            q=search_query,
            part='id,snippet',
            maxResults=10,
            type='video',
            relevanceLanguage='en',
            order='relevance'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response['items']]
        
        # Then get detailed information for each video
        videos_response = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=','.join(video_ids)
        ).execute()

        videos_data = []
        for video in videos_response['items']:
            snippet = video['snippet']
            statistics = video.get('statistics', {})
            content_details = video.get('contentDetails', {})

            video_data = {
                'video_id': video['id'],
                'title': snippet['title'],
                'description': snippet['description'],
                'thumbnail_url': snippet['thumbnails']['high']['url'],
                'channel_title': snippet['channelTitle'],
                'published_at': snippet['publishedAt'],
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'category_id': snippet.get('categoryId', ''),
                'tags': ','.join(snippet.get('tags', [])),
                'duration': content_details.get('duration', ''),
                'url': f"https://www.youtube.com/watch?v={video['id']}"
            }
            videos_data.append(video_data)
            
        return videos_data
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def fetch_core_papers(search_query):
    try:
        # CORE API endpoint for search
        url = 'https://api.core.ac.uk/v3/search/works'
        headers = {
            'Authorization': f'Bearer {CORE_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Prepare the search payload
        payload = {
            'q': search_query,
            'limit': 5,
            'offset': 0,
            'scroll': True
        }

        logging.info(f"Fetching papers for query: {search_query}")
        response = requests.post(url, json=payload, headers=headers)
        logging.info(f"API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            logging.error(f"API Error Response: {response.text}")
            return []

        data = response.json()
        logging.info(f"Found {len(data.get('results', []))} papers")

        papers_data = []
        for item in data.get('results', []):
            try:
                # Extract authors
                authors = []
                for author in item.get('authors', []):
                    if isinstance(author, dict):
                        authors.append(author.get('name', ''))
                    else:
                        authors.append(str(author))

                paper_data = {
                    'core_id': str(item.get('id', '')),
                    'title': item.get('title', 'Untitled'),
                    'abstract': item.get('abstract', ''),
                    'authors': ','.join(authors) if authors else 'Unknown',
                    'download_url': item.get('downloadUrl', ''),
                    'pdf_url': item.get('pdfUrl', ''),
                    'publisher': item.get('publisher', ''),
                    'year': item.get('yearPublished'),
                    'language': item.get('languageCode', 'en'),
                    'doi': item.get('doi', '')
                }
                papers_data.append(paper_data)
                logging.info(f"Processed paper: {paper_data['title']}")
            except Exception as e:
                logging.error(f"Error processing paper: {str(e)}")
                continue

        return papers_data

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error while fetching papers: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error while fetching papers: {str(e)}")
        return []

def fetch_google_books(search_query):
    try:
        logging.info(f"Fetching books for query: {search_query}")
        
        # Call the Google Books API
        request = books_service.volumes().list(
            q=search_query,
            maxResults=10,
            orderBy='relevance',
            printType='BOOKS',
            langRestrict='en'
        )
        response = request.execute()
        
        logging.info(f"Found {len(response.get('items', []))} books")
        
        books_data = []
        for item in response.get('items', []):
            try:
                volume_info = item.get('volumeInfo', {})
                sale_info = item.get('saleInfo', {})
                
                # Extract authors
                authors = volume_info.get('authors', [])
                authors_str = ','.join(authors) if authors else 'Unknown'
                
                # Extract categories
                categories = volume_info.get('categories', [])
                categories_str = ','.join(categories) if categories else ''
                
                # Extract links
                preview_link = volume_info.get('previewLink', '')
                info_link = volume_info.get('infoLink', '')
                
                # Extract buy link if available
                buy_link = ''
                if sale_info.get('buyLink'):
                    buy_link = sale_info.get('buyLink')
                
                # Extract thumbnail
                thumbnail = ''
                if 'imageLinks' in volume_info:
                    thumbnail = volume_info['imageLinks'].get('thumbnail', '')
                
                book_data = {
                    'google_id': item.get('id', ''),
                    'title': volume_info.get('title', 'Untitled'),
                    'subtitle': volume_info.get('subtitle', ''),
                    'authors': authors_str,
                    'publisher': volume_info.get('publisher', ''),
                    'published_date': volume_info.get('publishedDate', ''),
                    'description': volume_info.get('description', ''),
                    'page_count': volume_info.get('pageCount', 0),
                    'categories': categories_str,
                    'average_rating': volume_info.get('averageRating', 0.0),
                    'ratings_count': volume_info.get('ratingsCount', 0),
                    'thumbnail': thumbnail,
                    'preview_link': preview_link,
                    'info_link': info_link,
                    'buy_link': buy_link
                }
                
                books_data.append(book_data)
                logging.info(f"Processed book: {book_data['title']}")
                
            except Exception as e:
                logging.error(f"Error processing book: {str(e)}")
                continue
                
        return books_data
        
    except HttpError as e:
        logging.error(f"HTTP error while fetching books: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error while fetching books: {str(e)}")
        return []

@app.route('/')
def index():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projects=projects)

@app.route('/project/<int:project_id>')
def project_details(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_details.html', project=project)

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    new_project = Project(
        title=data['title'],
        prompt=data['prompt']
    )
    db.session.add(new_project)
    db.session.commit()

    # Fetch and store YouTube videos
    search_query = f"{new_project.title} {new_project.prompt}"
    
    # Fetch videos
    videos_data = fetch_youtube_videos(search_query)
    for video_data in videos_data:
        new_video = Video(
            project_id=new_project.id,
            video_id=video_data['video_id'],
            title=video_data['title'],
            description=video_data['description'],
            thumbnail_url=video_data['thumbnail_url'],
            channel_title=video_data['channel_title'],
            published_at=datetime.strptime(video_data['published_at'], '%Y-%m-%dT%H:%M:%SZ'),
            view_count=video_data['view_count'],
            like_count=video_data['like_count'],
            category_id=video_data['category_id'],
            tags=video_data['tags'],
            duration=video_data['duration']
        )
        db.session.add(new_video)
    
    # Fetch papers
    papers_data = fetch_core_papers(search_query)
    for paper_data in papers_data:
        new_paper = Paper(
            project_id=new_project.id,
            core_id=paper_data['core_id'],
            title=paper_data['title'],
            abstract=paper_data['abstract'],
            authors=paper_data['authors'],
            download_url=paper_data['download_url'],
            pdf_url=paper_data['pdf_url'],
            publisher=paper_data['publisher'],
            year=paper_data['year'],
            language=paper_data['language'],
            doi=paper_data['doi']
        )
        db.session.add(new_paper)

    # Fetch books
    books_data = fetch_google_books(search_query)
    for book_data in books_data:
        new_book = Book(
            project_id=new_project.id,
            google_id=book_data['google_id'],
            title=book_data['title'],
            subtitle=book_data.get('subtitle', ''),
            authors=book_data.get('authors', ''),
            publisher=book_data.get('publisher', ''),
            published_date=book_data.get('published_date', ''),
            description=book_data.get('description', ''),
            page_count=book_data.get('page_count', 0),
            categories=book_data.get('categories', ''),
            average_rating=book_data.get('average_rating', 0.0),
            ratings_count=book_data.get('ratings_count', 0),
            thumbnail=book_data.get('thumbnail', ''),
            preview_link=book_data.get('preview_link', ''),
            info_link=book_data.get('info_link', ''),
            buy_link=book_data.get('buy_link', '')
        )
        db.session.add(new_book)

    db.session.commit()

    return jsonify({
        'id': new_project.id,
        'title': new_project.title,
        'prompt': new_project.prompt,
        'created_at': new_project.created_at.isoformat()
    })

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'})

@app.route('/api/projects/<int:project_id>/videos', methods=['GET'])
def get_videos(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get videos from database
        videos = Video.query.filter_by(project_id=project_id).all()
        
        if not videos:
            # If no videos in database, fetch from YouTube API
            videos_data = fetch_youtube_videos(project.prompt)
            
            # Save to database
            for video_data in videos_data:
                # Parse the published_at date string
                published_at = None
                if 'published_at' in video_data:
                    try:
                        published_at = datetime.strptime(video_data['published_at'], '%Y-%m-%dT%H:%M:%SZ')
                    except ValueError:
                        pass
                
                video = Video(
                    project_id=project.id,
                    video_id=video_data['video_id'],
                    title=video_data['title'],
                    description=video_data['description'],
                    thumbnail_url=video_data['thumbnail_url'],
                    channel_title=video_data['channel_title'],
                    published_at=published_at,
                    view_count=video_data['view_count'],
                    like_count=video_data['like_count'],
                    category_id=video_data['category_id'],
                    tags=video_data['tags'],
                    duration=video_data['duration']
                )
                db.session.add(video)
            
            db.session.commit()
            
            # Get videos again after saving
            videos = Video.query.filter_by(project_id=project_id).all()
        
        # Convert to JSON
        videos_json = []
        for video in videos:
            video_data = {
                'id': video.id,
                'video_id': video.video_id,
                'title': video.title,
                'description': video.description,
                'thumbnail_url': video.thumbnail_url,
                'channel_title': video.channel_title,
                'published_at': video.published_at.isoformat() if video.published_at else None,
                'view_count': video.view_count,
                'like_count': video.like_count,
                'url': f"https://www.youtube.com/watch?v={video.video_id}",
                'relevance_rating': video.relevance_rating,
                'click_count': video.click_count
            }
            videos_json.append(video_data)
        
        return jsonify(videos_json)
    
    except Exception as e:
        logging.error(f"Error fetching videos from database: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/papers', methods=['GET'])
def get_papers(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get papers from database
        papers = Paper.query.filter_by(project_id=project_id).all()
        
        if not papers:
            # If no papers in database, fetch from CORE API
            papers_data = fetch_core_papers(project.prompt)
            
            # Save to database
            for paper_data in papers_data:
                paper = Paper(
                    project_id=project.id,
                    core_id=paper_data['core_id'],
                    title=paper_data['title'],
                    abstract=paper_data['abstract'],
                    authors=paper_data['authors'],
                    download_url=paper_data['download_url'],
                    pdf_url=paper_data['pdf_url'],
                    publisher=paper_data['publisher'],
                    year=paper_data['year'],
                    language=paper_data['language'],
                    doi=paper_data['doi']
                )
                db.session.add(paper)
            
            db.session.commit()
            
            # Get papers again after saving
            papers = Paper.query.filter_by(project_id=project_id).all()
        
        # Convert to JSON
        papers_json = []
        for paper in papers:
            paper_data = {
                'id': paper.id,
                'core_id': paper.core_id,
                'title': paper.title,
                'abstract': paper.abstract,
                'authors': paper.authors,
                'download_url': paper.download_url,
                'pdf_url': paper.pdf_url,
                'publisher': paper.publisher,
                'year': paper.year,
                'doi': paper.doi,
                'relevance_rating': paper.relevance_rating,
                'click_count': paper.click_count
            }
            papers_json.append(paper_data)
        
        return jsonify(papers_json)
    
    except Exception as e:
        logging.error(f"Error fetching papers from database: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/books', methods=['GET'])
def get_books(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        # Get books from database
        books = Book.query.filter_by(project_id=project_id).all()
        
        if not books:
            # If no books in database, fetch from Google Books API
            books_data = fetch_google_books(project.prompt)
            
            # Save to database
            for book_data in books_data:
                book = Book(
                    project_id=project.id,
                    google_id=book_data['google_id'],
                    title=book_data['title'],
                    subtitle=book_data.get('subtitle', ''),
                    authors=book_data.get('authors', ''),
                    publisher=book_data.get('publisher', ''),
                    published_date=book_data.get('published_date', ''),
                    description=book_data.get('description', ''),
                    page_count=book_data.get('page_count', 0),
                    categories=book_data.get('categories', ''),
                    average_rating=book_data.get('average_rating', 0.0),
                    ratings_count=book_data.get('ratings_count', 0),
                    thumbnail=book_data.get('thumbnail', ''),
                    preview_link=book_data.get('preview_link', ''),
                    info_link=book_data.get('info_link', ''),
                    buy_link=book_data.get('buy_link', '')
                )
                db.session.add(book)
            
            db.session.commit()
            
            # Get books again after saving
            books = Book.query.filter_by(project_id=project_id).all()
        
        # Convert to JSON
        books_json = []
        for book in books:
            book_data = {
                'id': book.id,
                'google_id': book.google_id,
                'title': book.title,
                'subtitle': book.subtitle,
                'authors': book.authors,
                'publisher': book.publisher,
                'published_date': book.published_date,
                'description': book.description,
                'page_count': book.page_count,
                'categories': book.categories,
                'average_rating': book.average_rating,
                'ratings_count': book.ratings_count,
                'thumbnail': book.thumbnail,
                'preview_link': book.preview_link,
                'info_link': book.info_link,
                'buy_link': book.buy_link,
                'relevance_rating': book.relevance_rating,
                'click_count': book.click_count
            }
            books_json.append(book_data)
        
        return jsonify(books_json)
    
    except Exception as e:
        logging.error(f"Error fetching books from database: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/<int:video_id>/click', methods=['POST'])
def track_video_click(video_id):
    video = Video.query.get_or_404(video_id)
    video.click_count += 1
    db.session.commit()
    return jsonify({'success': True, 'click_count': video.click_count})

@app.route('/api/videos/<int:video_id>/rate', methods=['POST'])
def rate_video(video_id):
    video = Video.query.get_or_404(video_id)
    data = request.get_json()
    video.relevance_rating = data.get('rating', 5)
    db.session.commit()
    return jsonify({'success': True, 'rating': video.relevance_rating})

@app.route('/api/videos/<int:video_id>/hide', methods=['POST'])
def hide_video(video_id):
    video = Video.query.get_or_404(video_id)
    db.session.delete(video)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/papers/<int:paper_id>/click', methods=['POST'])
def track_paper_click(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    paper.click_count += 1
    db.session.commit()
    return jsonify({'success': True, 'click_count': paper.click_count})

@app.route('/api/papers/<int:paper_id>/rate', methods=['POST'])
def rate_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    data = request.get_json()
    paper.relevance_rating = data.get('rating', 5)
    db.session.commit()
    return jsonify({'success': True, 'rating': paper.relevance_rating})

@app.route('/api/papers/<int:paper_id>/hide', methods=['POST'])
def hide_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    db.session.delete(paper)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/books/<int:book_id>/click', methods=['POST'])
def track_book_click(book_id):
    book = Book.query.get_or_404(book_id)
    book.click_count += 1
    db.session.commit()
    return jsonify({'success': True, 'click_count': book.click_count})

@app.route('/api/books/<int:book_id>/rate', methods=['POST'])
def rate_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json()
    book.relevance_rating = data.get('rating', 5)
    db.session.commit()
    return jsonify({'success': True, 'rating': book.relevance_rating})

@app.route('/api/books/<int:book_id>/hide', methods=['POST'])
def hide_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
