import socket
import argparse
from urllib.parse import urlparse, urljoin
import os
import urllib.parse
from config import HOST, PORT

class HTTPClient:
    def __init__(self, host=HOST, port=PORT, timeout=5, keep_alive=True):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.keep_alive = keep_alive
        self.active_connection = False  # 跟踪当前连接状态

    def connect(self):
        """建立或复用TCP连接"""
        if not self.active_connection or self.socket is None:
            self._create_new_connection()

    def _create_new_connection(self):
        """创建新TCP连接"""
        if self.socket:
            self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        try:
            self.socket.connect((self.host, self.port))
            self.active_connection = True
            print(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            raise

    def _construct_request(self, method, path):
        """构造HTTP请求报文"""
        # 规范化路径
        parsed_path = urllib.parse.urlparse(path)
        clean_path = urllib.parse.quote(parsed_path.path)
        if not clean_path.startswith('/'):
            clean_path = '/' + clean_path
            
        connection_header = "keep-alive" if self.keep_alive else "close"
        return (
            f"{method} {clean_path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Connection: {connection_header}\r\n"
            "\r\n"
        )

    def _parse_response(self, response):
        """解析HTTP响应"""
        header_end = response.find(b'\r\n\r\n')
        if header_end == -1:
            raise ValueError("Invalid HTTP response format")
        
        raw_headers = response[:header_end].decode(errors='ignore')
        body = response[header_end+4:]
        
        # 解析状态行
        status_line = raw_headers.split('\r\n', 1)[0]
        _, status_code, status_text = status_line.split(' ', 2)
        
        # 解析响应头
        headers = {}
        for line in raw_headers.split('\r\n')[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key.strip().lower()] = value.strip()
        
        # 更新连接状态
        if headers.get('connection') == 'close':
            self.active_connection = False

        return {
            'status_code': int(status_code),
            'status_text': status_text,
            'headers': headers,
            'body': body
        }

    def get(self, path='/', save_path=None):
        try:
            self.connect()
            
            request = self._construct_request('GET', path)
            self.socket.sendall(request.encode())
            print(f"\nSent request to {path}")
            
            response = self._receive_full_response()
            parsed = self._parse_response(response)
            
            self._print_response_summary(parsed)
            self._handle_response_body(parsed, save_path)
            
        except Exception as e:
            print(f"\nRequest failed: {str(e)}")
            self.active_connection = False
        finally:
            if not self.keep_alive or not self.active_connection:
                self._close_connection()

    def _receive_full_response(self):
        """接收完整响应数据"""
        response = b''
        while True:
            try:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                response += chunk
                # 检查是否接收完所有数据
                if self._is_response_complete(response):
                    break
            except socket.timeout:
                break
        return response

    def _is_response_complete(self, response):
        """检查响应完整性"""
        headers_end = response.find(b'\r\n\r\n')
        if headers_end == -1:
            return False
            
        headers = response[:headers_end].decode(errors='ignore').lower()
        if 'content-length' in headers:
            cl_start = headers.index('content-length:') + 14
            cl_end = headers.find('\r\n', cl_start)
            content_length = int(headers[cl_start:cl_end].strip())
            return len(response) >= headers_end + 4 + content_length
        return True  # 如果没有Content-Length，假设短连接数据

    def _print_response_summary(self, parsed_response):
        """打印响应摘要"""
        print(f"Status: {parsed_response['status_code']} {parsed_response['status_text']}")
        print("Headers:")
        for k, v in parsed_response['headers'].items():
            print(f"  {k}: {v}")

    def _handle_response_body(self, parsed_response, save_path):
        """处理响应体"""
        content_type = parsed_response['headers'].get('content-type', '')
        body = parsed_response['body']
        
        if save_path:
            self._save_file(save_path, body)
            print(f"File saved to: {os.path.abspath(save_path)}")
        elif 'text' in content_type:
            try:
                print("\nResponse Body:")
                print(body.decode('utf-8'))
            except UnicodeDecodeError:
                print(f"Text content decoding failed ({len(body)} bytes)")
        else:
            print(f"Received {len(body)} bytes binary data")

    def _save_file(self, path, data):
        """保存文件到指定路径"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)

    def _close_connection(self):
        """关闭当前连接"""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.active_connection = False
            print("Connection closed")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Interactive HTTP Client')
    parser.add_argument('-u', '--url', help='Base URL', default=f'http://{HOST}:{PORT}')
    parser.add_argument('-p', '--port', type=int, help='Port number (overrides port in URL)')
    parser.add_argument('-k', '--keep-alive', action='store_true', help='Enable persistent connections')
    args = parser.parse_args()

    parsed_url = urlparse(args.url)
    hostname = parsed_url.hostname or HOST
    port = args.port if args.port is not None else (parsed_url.port or PORT)

    client = HTTPClient(
        host=hostname,
        port=port,
        keep_alive=args.keep_alive
    )
    print("Interactive HTTP Client (Enter 'exit' to quit)")
    try:
        while True:
            user_input = input("\nEnter request path and save path (optional): ").strip()
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input:
                continue

            parts = user_input.split(maxsplit=1)
            path = parts[0]
            save_path = parts[1] if len(parts) > 1 else None
            
            # 自动生成保存路径
            if save_path is None and not path.endswith('/'):
                save_path = os.path.basename(urllib.parse.unquote(path)) or 'output'
            
            try:
                path = urljoin("http://localhost:8080", path)
                client.get(path=path, save_path=save_path)
            except Exception as e:
                print(f"Error: {str(e)}")
                
            # 如果连接不可用则自动重置
            print(keep_alive)
            if not client.active_connection and client.keep_alive:
                print("Server closed connection, resetting...")
                client._close_connection()

    except KeyboardInterrupt:
        print("\nClient terminated by user")
    finally:
        client._close_connection()