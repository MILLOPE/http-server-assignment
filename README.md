# HTTP Server

This is a simple Python-based HTTP server that serves static files from the `website` directory. The server supports configurable host, port, and logging options.

## Features
- Serves static files from the `website` directory.
- Logs requests and server events to both the console and a log file.
- Configurable host, port, and maximum connections via command-line arguments.
- Handles common HTTP errors (e.g., 404 Not Found, 500 Internal Server Error).

## Requirements
- Python 3.6 or higher.

## Directory Structure

project/ 
├── server/ 
    ├── server.py # Main server script │ 
    ├── config.py # Configuration file │ 
    └── logs/ # Directory for log files 
├── website/ # Directory containing static files (e.g., index.html)
    ├── index.html # index webpage │
├── client # 
├── logs # log file

## Usage

### 1. Start the Server
Run the following command to start the server:

```bash
python [server.py](http://_vscodecontentref_/2) --host <host> --port <port> --log-dir <log_dir> --max-connections <max_connections>
```

### 2. Command-Line Arguments

The server supports the following command-line arguments:

| Argument            | Description                              | Default Value     |
|---------------------|------------------------------------------|-------------------|
| `--host`            | Host address to bind the server to.      | `localhost`       |
| `--port`            | Port number to bind the server to.       | `8080`            |
| `--log-dir`         | Directory to store log files.            | `logs`            |
| `--max-connections` | Maximum number of simultaneous clients.  | `5`               |
```