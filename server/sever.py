import os
import logging
from datetime import datetime
from threading import Thread
import socket

class HTTPServer:
    def __init__(self, host='localhost', port=8080, log_dir='logs'):
        self.host = host
        self.port = port
        self.static_dir = os.path.join(os.path.dirname(__file__), 'website')
        self.log_dir = log_dir
        
        # setup logging system
        self._setup_logging()
        
        # create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def _setup_logging(self):
        """logging setup"""
        os.makedirs(self.log_dir, exist_ok=True)
        
        # logging configuration
        log_format = r'%(asctime)s - %(levelname)s - %(message)s'
        date_format = r'%Y-%m-%d %H:%M:%S'
        
        # 文件处理器（每天一个日志文件）
        log_file = os.path.join(self.log_dir, 'server.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # 配置根日志记录器
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger('HTTP Server')

    def _log_request(self, client_addr, method, path, status_code, content_length):
        """记录请求日志"""
        log_message = (
            f'{client_addr[0]} - - [{datetime.now().strftime(r"%d/%b/%Y:%H:%M:%S %z")}] '
            f'"{method} {path} HTTP/1.1" {status_code} {content_length}'
        )
        self.logger.info(log_message)

    def _generate_headers(self, status_code, content_type=None):
        """ Generate HTTP headers """

        status_codes = {
            200: 'OK',
            404: 'Not Found',
            500: 'Internal Server Error'
        }
        
        headers = [
            f'HTTP/1.1 {status_code} {status_codes.get(status_code, "")}',
            r'Server: Msm\'s PythonServer',
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
        """ based on file extension to get content type """
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
            
            # file path 
            safe_path = path.lstrip('/').replace('..', '') 
            file_path = os.path.join(self.static_dir, safe_path)
            
            if os.path.isdir(file_path):
                file_path = os.path.join(file_path, 'index.html')

            # file request
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
            self.logger.error(f"Error handling request: {str(e)}", exc_info=True)
            headers = self._generate_headers(500)
            client_socket.sendall(headers.encode() + b'Internal Server Error')
        
        finally:
            client_socket.close()

    def start(self):
        """启动服务器"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.logger.info(f"Server started on http://{self.host}:{self.port}")
        
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                self.logger.debug(f"New connection from {addr}")
                Thread(target=self._handle_request, args=(client_socket, addr)).start()
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested")
        except Exception as e:
            self.logger.critical(f"Server crashed: {str(e)}", exc_info=True)
        finally:
            self.server_socket.close()
            self.logger.info("Server stopped")

if __name__ == '__main__':
    server = HTTPServer()
    server.start()