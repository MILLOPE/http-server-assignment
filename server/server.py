import os
import logging
from datetime import datetime
from threading import Thread
import socket
import argparse 
import sys

from config import HOST, PORT, LOG_DIR, MAX_CONNECTIONS

class HTTPServer:
    def __init__(self, host=HOST, port=PORT, log_dir=LOG_DIR):
        self.host = host
        self.port = port
        # Update static_dir to point to the parent directory's website folder
        self.static_dir = os.path.join(os.path.dirname(__file__), '..', 'website')
        self.log_dir = log_dir
        
        # setup logging system
        self._setup_logging()
        
        # create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def _setup_logging(self):
        """logging setup"""
        os.makedirs(self.log_dir, exist_ok=True)
        
        # logging format
        log_format = r'%(asctime)s - %(levelname)s - %(message)s'
        date_format = r'%Y-%m-%d %H:%M:%S'
        
        # 文件处理器（每天一个日志文件）
        log_file = os.path.join(self.log_dir, 'server.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # coonsole handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # logging baseic config
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger('HTTP Server')

    def _log_request(self, client_addr, method, path, status_code, content_length):
        """response log"""
        log_message = (
            f'{client_addr[0]} - - [{datetime.now().strftime(r"%d/%b/%Y:%H:%M:%S %z")}] '
            f'"{method} {path} HTTP/1.1" {status_code} Content_length : {content_length}'
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


    def _handle_request(self, client_socket, addr):
        """Handle a single HTTP request."""
        try:
            request = client_socket.recv(1024).decode()
            
            if not request:
                return

            method, path = self._parse_request(request)
            
            self.logger.info(f"Request: {method} {path} from {addr}")
            
            # Resolve the file path
            default_path = path.lstrip('/').replace('..', '')  # Prevent directory traversal
            
            # Handle favicon.ico request
            if path == '/favicon.ico':
                headers = self._generate_headers(200, 'image/x-icon')
                client_socket.send(headers.encode())
                self._log_request(addr, method, path, 200, 0)
                return

            # Default to index.html if the root path is requested
            if path == '/' or default_path == '':
                default_path = 'index.html'

            file_path = os.path.join(self.static_dir, default_path)
            # Check if the file exists and is not a directory
            if os.path.exists(file_path) and not os.path.isdir(file_path):
                content_type = self._get_content_type(file_path)
                headers = self._generate_headers(200, content_type)
                
                with open(file_path, 'rb') as f:
                    response = headers.encode() + f.read()
            else:
                headers = self._generate_headers(404)
                response = headers.encode() + b'404 Not Found'
            
            client_socket.sendall(response)
            
            # Write log
            content_length = len(response) - len(headers.encode())
            self._log_request(
                addr, 
                method, 
                path, 
                200 if os.path.exists(file_path) else 404, 
                content_length
            )
        
        except ConnectionResetError:
            self.logger.warning(f"Connection reset by client: {addr}")
        except Exception as e:
            self.logger.error(f"Error handling request: {str(e)}", exc_info=True)
            headers = self._generate_headers(500)
            client_socket.sendall(headers.encode() + b'Internal Server Error')
        
        finally:
            self.logger.info(f"Connection closed: {addr}")
            client_socket.close()

    def start(self, max_connections=MAX_CONNECTIONS):
        """Start the server."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(max_connections)  # Max connections
        self.logger.info(f"Server started on http://{self.host}:{self.port}")
        
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                self.logger.info(f"New connection from {addr}")
                Thread(target=self._handle_request, args=(client_socket, addr)).start()
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested by user (KeyboardInterrupt)")
        except Exception as e:
            self.logger.critical(f"Server crashed: {str(e)}", exc_info=True)
        finally:
            self.logger.info("Server stopped")
            print("Server stopped")
            # 强制刷新日志和标准输出
            for handler in self.logger.handlers:
                handler.flush()
            sys.stdout.flush()
            self.server_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Start the HTTP server.")
    parser.add_argument('--host', type=str, default=HOST, help='Host address (default: localhost)')
    parser.add_argument('--port', type=int, default=PORT, help='Port number (default: 8080)')
    parser.add_argument('--log-dir', type=str, default=LOG_DIR, help='Log directory (default: logs)')
    parser.add_argument('--max-connections', type=int, default=MAX_CONNECTIONS, help='Max connections (default: 5)')
    args = parser.parse_args()

    server = HTTPServer(host=args.host, port=args.port, log_dir=args.log_dir)
    server.start(max_connections=args.max_connections)

    