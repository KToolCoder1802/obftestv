from http.server import BaseHTTPRequestHandler
import base64
import zlib
import json
import sys
import os

# Thêm thư mục gốc vào path để import pymeo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PYMEO
try:
    from pymeo import obfuscate
    PYMEO_LOADED = True
    print("[OK] PYMEO loaded successfully", flush=True)
except ImportError as e:
    PYMEO_LOADED = False
    print(f"[WARN] PYMEO not loaded: {e}", flush=True)
    # Fallback obfuscate function
    def obfuscate(code, mode=2, more_obf=False, antidebug=True, anticrack=True, username="API_USER"):
        compressed = zlib.compress(code.encode())
        encoded = base64.b64encode(compressed).decode()
        return f"import base64,zlib\nexec(zlib.decompress(base64.b64decode('{encoded}')))"

class handler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        try:
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Lấy tham số từ form
            mode = 2
            more_obf = True
            antidebug = True
            anticrack = True
            username = "API_USER"
            
            if 'multipart/form-data' in content_type:
                boundary = content_type.split('boundary=')[1].encode()
                parts = post_data.split(boundary)
                
                file_content = None
                filename = "obfuscated.py"
                
                for part in parts:
                    if b'filename=' in part:
                        lines = part.split(b'\r\n')
                        for line in lines:
                            if b'filename=' in line:
                                filename = line.decode().split('filename="')[1].split('"')[0]
                                break
                        
                        start = part.find(b'\r\n\r\n')
                        if start != -1:
                            file_content = part[start + 4:].rstrip(b'\r\n--')
                            break
                    
                    # Lấy các tham số khác (mode, more_obf, etc.)
                    if b'name="mode"' in part:
                        start = part.find(b'\r\n\r\n')
                        if start != -1:
                            mode = int(part[start + 4:].strip())
                    if b'name="username"' in part:
                        start = part.find(b'\r\n\r\n')
                        if start != -1:
                            username = part[start + 4:].strip().decode()
                
                if not file_content:
                    self._send_error(400, "No file found")
                    return
                
                code = file_content.decode('utf-8', errors='ignore')
                
                # Gọi PYMEO obfuscate
                result = obfuscate(
                    code=code,
                    mode=mode,
                    more_obf=more_obf,
                    antidebug=antidebug,
                    anticrack=anticrack,
                    username=username
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/x-python')
                self.send_header('Content-Disposition', f'attachment; filename=obfuscated_{filename}')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(result.encode('utf-8'))
                
            else:
                self._send_error(400, "Unsupported content type")
                
        except Exception as e:
            self._send_error(500, f"Internal error: {str(e)}")
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        info = {
            "status": "ok",
            "message": "PYMEO Obfuscator API is running",
            "pymeo_loaded": PYMEO_LOADED,
            "usage": "POST /api/obfuscate with file"
        }
        self.wfile.write(json.dumps(info).encode())
    
    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error = {"error": message}
        self.wfile.write(json.dumps(error).encode())