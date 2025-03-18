import requests
import json

CORE_API_KEY = 'oIJb9cduRHMOYiVxFv2aQE8rXeTh1AjZ'


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

        print(f"Fetching papers for query: {search_query}")
        response = requests.post(url, json=payload, headers=headers)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API Error Response: {response.text}")
            return []

        data = response.json()
        print(f"Found {len(data.get('results', []))} papers")

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
                print(f"Processed paper: {paper_data['title']}")
            except Exception as e:
                print(f"Error processing paper: {str(e)}")
                continue

        return papers_data

    except requests.exceptions.RequestException as e:
        print(f"Request error while fetching papers: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error while fetching papers: {str(e)}")
        return []


def main():
    search_query = input("Enter search keywords for papers: ")
    papers = fetch_core_papers(search_query)
    
    if not papers:
        print("No papers found.")
    else:
        print(json.dumps(papers, indent=2))


if __name__ == "__main__":
    main()
