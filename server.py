from flask import Flask, jsonify, request, send_from_directory, Response
from ytmusicapi import YTMusic
import yt_dlp
import os
import urllib.parse
import requests

app = Flask(__name__, static_folder='.')

ytmusic = YTMusic()

# Configure the video scraper to extract the best audio stream
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': False,
    'no_warnings': True,
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
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
    ydl_opts['pot_provider'] = 'bgutil'
    
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            
        # Give the phone our proxy URL instead of the Google URL
        encoded_url = urllib.parse.quote(audio_url)
        return jsonify({"stream_url": f"/api/proxy?url={encoded_url}"})
    except Exception as e:
        print(f"Extraction Error: {e}")
        return jsonify({"error": "Could not extract stream"}), 500

# --- NEW: PROXY ROUTE ---
@app.route('/api/proxy')
def proxy_audio():
    target_url = request.args.get('url')
    if not target_url:
        return "No URL provided", 400
        
    headers = {}
    # Forward the phone's Range headers to Google so scrubbing works
    if 'Range' in request.headers:
        headers['Range'] = request.headers['Range']
        
    # Stream the data from Google through Render
    r = requests.get(target_url, headers=headers, stream=True)
    
    def generate():
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                yield chunk
                
    resp = Response(generate(), status=r.status_code)
    resp.headers['Content-Type'] = r.headers.get('Content-Type', 'audio/webm')
    resp.headers['Accept-Ranges'] = 'bytes'
    
    # Forward content length and range details if they exist
    if 'Content-Length' in r.headers:
        resp.headers['Content-Length'] = r.headers['Content-Length']
    if 'Content-Range' in r.headers:
        resp.headers['Content-Range'] = r.headers['Content-Range']
        
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)