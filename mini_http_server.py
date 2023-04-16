import http.server
import socketserver
import os
import cgi

# DIRECTORY = os.path.join(os.path.dirname(__file__), 'public')
DIRECTORY = "publicfiles"
PORT = 40080
SAFE_FILE_EXT = '.mp3'
os.chdir(DIRECTORY)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        # 文件上传处理
        if self.path.startswith('/upload'):
            self.handle_upload()
        else:
            self.send_error(404, "Invalid path for POST request")
    
    def do_GET(self):
        # 文件访问处理
        if self.path.startswith('/read'):
            try:
                super().do_GET()
            except ConnectionResetError:
                print("Connection reset by peer")
        else:
            self.send_error(404, "Invalid path for GET request")

    def translate_path(self, path):
        # Get file name from URL path
        file_name, file_ext = os.path.splitext(os.path.basename(path))
        if "voice" not in file_name.lower() or file_ext.lower() != SAFE_FILE_EXT:
            return ''

        # Get file path
        # path = os.path.join(DIRECTORY, file_name + file_ext)
        return file_name + file_ext
    
    def handle_upload(self):
        content_type = self.headers['Content-Type']

        # 判断内容类型是否为multipart/form-data
        if content_type.startswith('multipart/form-data'):
            ctype, pdict = cgi.parse_header(content_type)
            pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
            fields = cgi.parse_multipart(self.rfile, pdict)

            # 获取文件名
            filename = self.headers.get('filename', '').lower() + SAFE_FILE_EXT

            # 检查文件名中是否包含'required_string'
            if 'voice' not in filename:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'File name does not contain required string')
                return

            # 获取文件内容
            file_content = fields.get('file', [None])[0]

            if file_content:
                # 保存上传的文件
                # file_path = os.path.join(DIRECTORY, filename)
                file_path = filename
                with open(file_path, 'wb') as f:
                    f.write(file_content)

                # 响应成功
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'File uploaded successfully')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'No file content found in the request')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid content type')


httpd = socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler)
print(f"Starting server on port {PORT}")
httpd.serve_forever()


