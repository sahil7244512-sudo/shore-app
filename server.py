from flask import Flask, jsonify, request, send_from_directory
from ytmusicapi import YTMusic
import yt_dlp
import os

app = Flask(__name__, static_folder='.')

# Initialize the YouTube Music API scraper
ytmusic = YTMusic()

# Configure the video scraper to only extract the best audio stream
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,
}

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
        # Default screen when nothing is searched
        return jsonify([])
        
    try:
        # Search YouTube Music for songs
        search_results = ytmusic.search(query, filter="songs", limit=15)
        
        # Format the data cleanly for our frontend
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                "id": result.get("videoId"),
                "title": result.get("title"),
                "artist": ", ".join([a["name"] for a in result.get("artists", [])]),
                # Grab the highest resolution album art available
                "thumbnail": result.get("thumbnails", [{}])[-1].get("url", "")
            })
            
        return jsonify(formatted_results)
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify({"error": "Search failed"}), 500

@app.route('/api/stream/<video_id>')
def get_stream_url(video_id):
    try:
        # Give yt-dlp the YouTube video ID
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract the hidden Google audio server URL without downloading the file
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            
        return jsonify({"stream_url": audio_url})
    except Exception as e:
        print(f"Extraction Error: {e}")
        return jsonify({"error": "Could not extract stream"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)