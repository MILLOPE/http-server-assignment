import socket
import os
from threading import Thread

class HTTPServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.static_dir = os.path.join(os.path.dirname(__file__), 'website')
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def _generate_headers(self, status_code, content_type=None):
        """ Generate HTTP headers """

        status_codes = {
            200: 'OK',
            404: 'Not Found',
            500: 'Internal Server Error'
        }
        
        headers = [
            f'HTTP/1.1 {status_code} {status_codes.get(status_code, "")}',
            'Server: Msm\'s PythonServer',
            'Connection: close'
        ]
        
        if content_type:
            headers.append(f'Content-Type: {content_type}')
        
        return '\r\n'.join(headers) + '\r\n\r\n'

    def _parse_request(self, request):
        """ Parse HTTP request """
        lines = request.split('\r\n')
        method, path, _ = lines[0].split()
        return method, path

    def _get_content_type(self, file_path):
        """手动判断内容类型"""
        ext = os.path.splitext(file_path)[1]
        return {
            '.html': 'text/html',
            '.css': 'text/css',
            '.jpg': 'image/jpeg',
            '.ico': 'image/x-icon'
        }.get(ext, 'application/octet-stream')

    def _handle_request(self, client_socket):
        """处理单个请求"""
        try:
            request = client_socket.recv(1024).decode()
            print(f"[Request]\n{request}\n")
            
            if not request:
                return

            method, path = self._parse_request(request)
            
            # 构建文件路径
            safe_path = path.lstrip('/').replace('..', '')  # 简单安全处理
            file_path = os.path.join(self.static_dir, safe_path)
            
            if os.path.isdir(file_path):
                file_path = os.path.join(file_path, 'index.html')

            # 处理文件请求
            if os.path.exists(file_path) and not os.path.isdir(file_path):
                content_type = self._get_content_type(file_path)
                headers = self._generate_headers(200, content_type)
                
                with open(file_path, 'rb') as f:
                    response = headers.encode() + f.read()
            else:
                headers = self._generate_headers(404)
                response = headers.encode() + b'404 Not Found'
            
            client_socket.sendall(response)
        
        except Exception as e:
            print(f"Error: {str(e)}")
            headers = self._generate_headers(500)
            client_socket.sendall(headers.encode() + b'Internal Server Error')
        
        finally:
            client_socket.close()

    def start(self):
        """Start Server"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server running at http://{self.host}:{self.port}")
        
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Accepted connection from {addr}")
                Thread(target=self._handle_request, args=(client_socket,)).start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.server_socket.close()

if __name__ == '__main__':
    server = HTTPServer()
    server.start()