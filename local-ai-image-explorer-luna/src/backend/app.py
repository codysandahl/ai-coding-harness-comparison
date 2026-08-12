import base64, json, os, random, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path

ROOT = Path(__file__).parent
GUIDANCE = json.loads((ROOT / 'config/creativity.json').read_text())
FAKE_MODELS = {'text': ['fake-text-1', 'fake-text-creative'], 'image': ['fake-image-1', 'fake-image-fast']}

def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_env()

def provider_configured():
    return bool(os.getenv('PROVIDER_API_KEY')) and not os.getenv('PROVIDER_BASE_URL', '').startswith('http://localhost')

def provider_request(path, payload=None):
    base = os.getenv('PROVIDER_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
    request = Request(base + path, data=json.dumps(payload).encode() if payload is not None else None,
                      headers={'Authorization': 'Bearer ' + os.environ['PROVIDER_API_KEY'], 'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=int(os.getenv('IMAGE_GEN_TIMEOUT_S' if path.startswith('/images') else 'TEXT_GEN_TIMEOUT_S', '60'))) as response:
            return json.loads(response.read())
    except HTTPError as error:
        try:
            detail = json.loads(error.read()).get('error', {}).get('message', str(error))
        except (ValueError, AttributeError):
            detail = str(error)
        raise ValueError(f'Provider rejected the request: {detail}') from error
    except URLError as error:
        raise ValueError(f'Provider connection failed: {error.reason}') from error

def provider_image_size(width, height):
    if width == height:
        return '1024x1024'
    return '1536x1024' if width > height else '1024x1536'

def provider_models():
    try:
        data = provider_request('/models')
        ids = [item['id'] for item in data.get('data', [])]
        image_hints = tuple(x.strip().lower() for x in os.getenv('IMAGE_MODEL_NAME_HINTS', '').split(',') if x.strip())
        images = [model for model in ids if any(hint in model.lower() for hint in image_hints)]
        return {'text': [model for model in ids if model not in images] or ids, 'image': images or ids}
    except (HTTPError, URLError, KeyError, ValueError):
        return FAKE_MODELS

def prompt_variation(base, remixes, creativity, seed):
    if creativity not in GUIDANCE: raise ValueError('Unknown creativity level')
    phrases = [p.strip() for p in remixes if p.strip()]
    guide = GUIDANCE[creativity]['guidance']
    extras = phrases or ['an unexpected visual study']
    choice = extras[seed % len(extras)]
    divergence = {'mild': 'subtle', 'normal': 'distinct', 'wild': '大胆 and surreal'}[creativity]
    local_prompt = f'{base.strip()} — {divergence} variation: {choice}. {guide}'
    if not provider_configured():
        return local_prompt
    response = provider_request('/chat/completions', {'model': os.getenv('TEXT_MODEL_NAME', 'gpt-4o-mini'), 'messages': [{'role': 'user', 'content': f'Create one distinct image prompt from: {local_prompt}'}], 'temperature': {'mild': 0.3, 'normal': 0.7, 'wild': 1.1}[creativity]})
    return response['choices'][0]['message']['content'].strip()

def resolve_seed(value):
    return random.SystemRandom().randint(1, 2**31 - 1) if value is None or str(value).strip() == '' else int(value)

def validate(req):
    prompt = str(req.get('prompt', '')).strip()
    if not prompt: raise ValueError('Prompt is required')
    width, height = int(req.get('width', 512)), int(req.get('height', 512))
    if not 64 <= width <= 2048 or not 64 <= height <= 2048: raise ValueError('Dimensions must be 64..2048')
    return prompt, width, height, resolve_seed(req.get('seed'))

def image_svg(prompt, width, height, seed):
    safe = prompt.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')[:180]
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="hsl({seed % 360} 45% 78%)"/><text x="50%" y="45%" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#1a1a1a">{safe}</text><text x="50%" y="55%" text-anchor="middle" font-family="sans-serif" font-size="16">seed {seed}</text></svg>'
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode()

class Handler(BaseHTTPRequestHandler):
    def cors_headers(self):
        origin = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173')
        self.send_header('Access-Control-Allow-Origin', origin); self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    def send_json(self, value, status=200):
        data=json.dumps(value).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.cors_headers(); self.end_headers(); self.wfile.write(data)
    def do_OPTIONS(self): self.send_response(204); self.cors_headers(); self.end_headers()
    def do_GET(self):
        if self.path == '/api/models': return self.send_json(provider_models() if provider_configured() else FAKE_MODELS)
        if self.path == '/api/health': return self.send_json({'ok': True})
        self.send_json({'error':'Not found'},404)
    def do_POST(self):
        try:
            length=int(self.headers.get('Content-Length',0)); req=json.loads(self.rfile.read(length))
            if self.path == '/api/prompts/variations':
                seed = resolve_seed(req.get('seed'))
                return self.send_json({'prompt':prompt_variation(req['basePrompt'], req.get('remixes',[]), req.get('creativity','normal'), seed), 'seed':seed})
            if self.path == '/api/images/generate':
                prompt,w,h,seed=validate(req)
                if provider_configured():
                    response = provider_request('/images/generations', {'model': req.get('imageModel'), 'prompt': prompt, 'size': provider_image_size(w, h), 'n': 1})
                    item = response['data'][0]
                    encoded = item.get('b64_json')
                    image_data = 'data:image/png;base64,' + encoded if encoded else item['url']
                else:
                    image_data = image_svg(prompt,w,h,seed)
                image={'id':str(uuid.uuid4()),'image':image_data,'prompt':prompt,'textModel':req.get('textModel','fake-text-1'),'imageModel':req.get('imageModel','fake-image-1'),'width':w,'height':h,'seed':seed,'creativity':req.get('creativity','normal')}
                return self.send_json(image)
            self.send_json({'error':'Not found'},404)
        except (ValueError, KeyError, TypeError) as e: self.send_json({'error':str(e)},400)
    def log_message(self, *_): pass

if __name__ == '__main__': HTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
