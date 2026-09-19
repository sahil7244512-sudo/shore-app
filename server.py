from flask import Flask, jsonify, request, send_from_directory
from ytmusicapi import YTMusic

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
        # The reliable backend search is back!
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