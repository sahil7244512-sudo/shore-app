from flask import Flask, jsonify, request, send_from_directory
from ytmusicapi import YTMusic
import requests

app = Flask(__name__, static_folder='.')

ytmusic = YTMusic()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/api/search')
def search():
    query = request.args.get('q')
    if not query:
        return jsonify([])
        
    try:
        search_results = ytmusic.search(query, filter="songs", limit=15)
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                "id": result.get("videoId"),
                "title": result.get("title"),
                "artist": ", ".join([a["name"] for a in result.get("artists", [])]),
                "thumbnail": result.get("thumbnails", [{}])[-1].get("url", "")
            })
        return jsonify(formatted_results)
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify({"error": "Search failed"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
@app.route('/api/stream/<video_id>')
def get_stream_url(video_id):
    # Expanded list of community servers
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.projectsegfau.lt",
        "https://pipedapi.smnz.de",
        "https://piped-api.lunar.icu"
    ]
    
    # Spoof a real Windows/Chrome web browser so servers don't block us
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for instance in instances:
        try:
            print(f"Trying Piped API: {instance}")
            res = requests.get(f"{instance}/streams/{video_id}", headers=headers, timeout=6)
            
            if res.status_code == 200:
                data = res.json()
                if 'audioStreams' in data and len(data['audioStreams']) > 0:
                    audio_url = data['audioStreams'][0]['url']
                    print(f"Success! Stream extracted via {instance}")
                    return jsonify({"stream_url": audio_url})
            else:
                print(f"Failed on {instance} - Status Code: {res.status_code}")
                
        except Exception as e:
            print(f"Error connecting to {instance}: {e}")
            continue
            
    return jsonify({"error": "Could not extract stream"}), 500