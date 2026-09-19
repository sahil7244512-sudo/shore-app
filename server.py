from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('.', 'manifest.json')

# Notice there are no more API routes! 
# Your phone does 100% of the work directly now, bypassing the cloud server IP blocks.

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)