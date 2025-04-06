# HTTP Server

This is a simple Python-based HTTP server that serves static files from the `website` directory. The server supports configurable host, port, and logging options.

## Features
- Serves static files from the `website` directory.
- Logs requests and server events to both the console and a log file.
- Configurable host, port, and maximum connections via command-line arguments.
- Handles common HTTP errors (e.g., 404 Not Found, 500 Internal Server Error).

## Requirements
- Python 3.6 or higher.

## Usage

### 1. Start the Server
Run the following command to start the server:

```bash
python server.py --host <host> --port <port> --log-dir <log_dir> --max-connections <max_connections>
```

The server supports the following command-line arguments:

| Argument            | Description                              | Default Value     |
|---------------------|------------------------------------------|-------------------|
| `--host`            | Host address to bind the server to.      | `localhost`       |
| `--port`            | Port number to bind the server to.       | `8080`            |
| `--log-dir`         | Directory to store log files.            | `logs`            |
| `--max-connections` | Maximum number of simultaneous clients.  | `5`               |



### 2. Start the Client
Run the following command to start the client:
```bash
python client.py -u http://localhost:8080 -k
```

| Argument           | Description                                              | Default Value               |
|--------------------|----------------------------------------------------------|-----------------------------|
| `-u`, `--url`       | Specifies the base URL of the server (default: `http://localhost:8080`) | `http://localhost:8080`     |
| `-p`, `--port`      | Specifies the port number (optional, overrides the port in the URL) | No default (must be specified) |
| `-k`, `--keep-alive`| Enables persistent connections (optional)                | Disabled by default         |


Once the client is started, you can input the request path and save path (optional) in the terminal.

#### Examples:

1. Request `/index.html` and save it as `index.html`:

```bash
Request: /index.html
Save as: index.html
```
2. Request /image.jpg and save it as image.jpg:

```bash
Request: /image.jpg
Save as: image.jpg
```
3. To exit the client, type exit or quit:

```bash
exit
```