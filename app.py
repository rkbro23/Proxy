from flask import Flask, request, Response, stream_with_context
import requests
from urllib.parse import urljoin, urlparse, quote
import mimetypes
import re

app = Flask(__name__)

# Headers we won't forward from origin to client
EXCLUDED_HEADERS = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']

# Allowed media extensions to proxy
SUPPORTED_EXTENSIONS = ['.m3u8', '.mpd', '.ts', '.mp4', '.webm', '.json', '.jpg', '.jpeg', '.png', '.gif', '.svg']

def is_playlist(content_type, url):
    # Identify if response is a playlist (HLS or DASH)
    return (
        'application/vnd.apple.mpegurl' in content_type or
        'application/dash+xml' in content_type or
        any(url.lower().endswith(ext) for ext in ['.m3u8', '.mpd'])
    )

def rewrite_m3u8(base_url, content, proxy_base):
    # Rewrite all relative or absolute TS or playlist links inside .m3u8 to route through proxy
    lines = content.splitlines()
    new_lines = []

    for line in lines:
        line_strip = line.strip()
        if not line_strip or line_strip.startswith('#'):
            # Comment or empty line, keep as is
            new_lines.append(line)
        else:
            # Must be a segment URL or nested playlist URL
            # Convert relative links to absolute first
            abs_url = urljoin(base_url, line_strip)

            # Encode the URL for passing as a GET param
            proxied_url = f"{proxy_base}?url={quote(abs_url, safe=':/?&=')}"
            new_lines.append(proxied_url)

    return '\n'.join(new_lines)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
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
        # Use a realistic desktop UA to avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Referer': target_url
        }

        # Stream to avoid memory load for big files
        remote = requests.get(target_url, headers=headers, stream=True, timeout=15)
        content_type = remote.headers.get('Content-Type', mimetypes.guess_type(target_url)[0] or 'application/octet-stream')

        # If the response is a playlist (.m3u8, .mpd) rewrite links
        if is_playlist(content_type, target_url):
            base_url = target_url.rsplit('/', 1)[0] + '/'
            raw_text = remote.text

            # Proxy base url for rewriting links (detect current host and scheme)
            proxy_base = request.url_root.rstrip('/') + '/proxy'

            rewritten = rewrite_m3u8(base_url, raw_text, proxy_base)

            # Return rewritten playlist with correct mimetype
            return Response(rewritten, mimetype=content_type, headers={
                'Cache-Control': 'no-store, no-cache, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
            })

        # For media segment files (.ts, .mp4, etc) and images, stream directly
        def generate():
            for chunk in remote.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        # Filter out headers that can cause issues
        resp_headers = [(k, v) for k, v in remote.raw.headers.items() if k.lower() not in EXCLUDED_HEADERS]

        return Response(stream_with_context(generate()), status=remote.status_code, headers=resp_headers, mimetype=content_type)

    except requests.exceptions.Timeout:
        return "🔥 Proxy Error: Timeout fetching remote URL", 504
    except requests.exceptions.ConnectionError:
        return "🔥 Proxy Error: Connection error", 502
    except Exception as e:
        return f"🔥 Proxy Error: {str(e)}", 500

if __name__ == '__main__':
    print("🚀 Ultra Proxy running on http://0.0.0.0:8080/proxy?url=...")
    app.run(host='0.0.0.0', port=8080)
