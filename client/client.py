import socket
import argparse
from urllib.parse import urlparse
import os
from config import HOST, PORT  # Import HOST and PORT from config.py

class HTTPClient:
    def __init__(self, host=HOST, port=PORT, timeout=5):
        """
        初始化HTTP客户端
        :param host: 服务器主机地址
        :param port: 服务器端口号
        :param timeout: 连接超时时间（秒）
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        
    def connect(self):
        """建立到服务器的连接"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        try:
            self.socket.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            raise
    
    def _construct_request(self, method, path):
        """手动构造HTTP请求报文"""
        return (
            f"{method} {path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
    
    def _parse_response(self, response):
        """手动解析HTTP响应"""
        # 分割响应头和正文
        header_end = response.find(b'\r\n\r\n')
        if header_end == -1:
            raise ValueError("Invalid HTTP response format")
        
        raw_headers = response[:header_end].decode()
        body = response[header_end+4:]
        
        # 解析状态行
        status_line = raw_headers.split('\r\n')[0]
        _, status_code, status_text = status_line.split(' ', 2)
        
        # 解析响应头
        headers = {}
        for line in raw_headers.split('\r\n')[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key.strip()] = value.strip()
        
        return {
            'status_code': int(status_code),
            'status_text': status_text,
            'headers': headers,
            'body': body
        }
    
    def get(self, path='/', save_path=None):
        try:
            # 建立连接
            self.connect()
            
            # 构造并发送请求
            request = self._construct_request('GET', path)
            self.socket.sendall(request.encode())
            print(f"Sent request:\n{request}")
            
            # 接收响应数据
            response = b''
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            # 解析响应
            parsed = self._parse_response(response)
            print(f"\nResponse Status: {parsed['status_code']} {parsed['status_text']}")
            print("Headers:")
            for k, v in parsed['headers'].items():
                print(f"  {k}: {v}")
            
            # 处理响应体
            if save_path:
                self._save_file(save_path, parsed['body'])
                print(f"\nFile saved to: {os.path.abspath(save_path)}")
            else:
                self._display_content(parsed['body'], parsed['headers'].get('Content-Type'))
        
        except Exception as e:
            print(f"\nRequest failed: {str(e)}")
        finally:
            if self.socket:
                self.socket.close()
    
    def _save_file(self, path, data):
        """save response body to file"""
        with open(path, 'wb') as f:
            f.write(data)
    
    def _display_content(self, data, content_type):
        """display response body"""
        if content_type and 'text' in content_type:
            try:
                print("\nResponse Body:")
                print(data.decode('utf-8'))
            except UnicodeDecodeError:
                print(f"\nReceived text with invalid encoding ({len(data)} bytes)")
        else:
            print(f"\nReceived binary data ({len(data)} bytes)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP Client')
    parser.add_argument('-url', help='Request URL', default='http://localhost:8080')
    parser.add_argument('-output', help='Output file path', default='/output')
    args = parser.parse_args()
    
    # 解析URL
    parsed_url = urlparse(args.url)
    host = parsed_url.hostname or HOST  # Use HOST from config.py as default
    port = parsed_url.port or PORT      # Use PORT from config.py as default
    path = parsed_url.path or '/'
    
    # build client
    client = HTTPClient(host=host, port=port)
    client.get(path=path, save_path=args.output)