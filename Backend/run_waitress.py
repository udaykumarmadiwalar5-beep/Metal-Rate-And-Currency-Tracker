import os
from waitress import serve
from app import app

port = int(os.environ.get('PORT', 5001))
print(f"Starting waitress on 127.0.0.1:{port}")
serve(app, host='127.0.0.1', port=port)
