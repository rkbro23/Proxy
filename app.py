from flask import Flask, request, Response
import requests
from urllib.parse import urljoin
import mimetypes

app = Flask(__name__)

EXCLUDED_HEADERS = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']

SUPPORTED_EXTENSIONS = ['.m3u8', '.mpd', '.ts', '.mp4', '.webm', '.json', '.jpg', '.jpeg', '.png', '.gif', '.svg']

def is_playlist(content_type, url):
    return (
        'application/vnd.apple.mpegurl' in content_type or
        'application/dash+xml' in content_type or
        any(url.lower().endswith(ext) for ext in ['.m3u8', '.mpd'])
    )

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/')
def home():
    return "✅ Ultra CORS Bypass Proxy is Running!"

@app.route('/proxy')
def proxy():
    target_url = request.args.get('url')
    if not target_url:
        return "❌ Missing 'url' parameter", 400

    try:
        headers = {
            'User-Agent': request.headers.get('User-Agent', 'Mozilla/5.0'),
            'Referer': target_url
        }

        remote = requests.get(target_url, headers=headers, stream=True, timeout=10)
        content_type = remote.headers.get('Content-Type', mimetypes.guess_type(target_url)[0] or 'application/octet-stream')

        # Playlist handling
        if is_playlist(content_type, target_url):
            base_url = target_url.rsplit('/', 1)[0] + '/'
            lines = remote.text.splitlines()
            modified = []
            for line in lines:
                if line.strip() and not line.startswith("#"):
                    full = urljoin(base_url, line.strip())
                    modified.append(full)
                else:
                    modified.append(line)
            content = '\n'.join(modified)
            return Response(content, mimetype=content_type)

        # All other formats
        content = remote.content
        resp_headers = [(k, v) for k, v in remote.raw.headers.items() if k.lower() not in EXCLUDED_HEADERS]
        return Response(content, status=remote.status_code, headers=resp_headers, mimetype=content_type)

    except Exception as e:
        return f"🔥 Proxy Error: {str(e)}", 500

if __name__ == '__main__':
    print("🚀 Running on...")
    app.run(host='0.0.0.0', port=8080)
