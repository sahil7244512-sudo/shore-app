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

@app.route('/api/stream/<video_id>')
def get_stream_url(video_id):
    # A fallback list of community API servers to bypass YouTube's datacenter blocks
    instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.smnz.de",
        "https://de.piped.api.r4fo.com"
    ]
    
    for instance in instances:
        try:
            # Ask the community server to extract the stream
            res = requests.get(f"{instance}/streams/{video_id}", timeout=5).json()
            
            if 'audioStreams' in res and len(res['audioStreams']) > 0:
                # Grab the direct proxy URL and send it to the phone
                audio_url = res['audioStreams'][0]['url']
                return jsonify({"stream_url": audio_url})
        except Exception:
            # If one server is busy, it automatically loops and tries the next one
            continue
            
    return jsonify({"error": "Could not extract stream"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)