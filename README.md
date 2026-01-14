# Zipline Proxy

A lightweight HTTP API proxy for Zipline that exposes file upload statistics in a format compatible with Homepage dashboard widgets.

## Features

- Health check endpoint
- Statistics endpoint returning file count and storage size in GB
- Session-based authentication with cookie caching
- Configurable cache timeout (default: 5 minutes)
- Lightweight Flask-based API
- Docker container ready

## Environment Variables

- `ZIPLINE_URL` - Base URL for Zipline API (default: `http://zipline:3000`)
- `ZIPLINE_USERNAME` - Zipline username for authentication (required)
- `ZIPLINE_PASSWORD` - Zipline password for authentication (required)
- `CACHE_TIMEOUT` - Cache duration in seconds (default: `300` / 5 minutes)

## Authentication

Zipline uses session-based authentication with cookies:
1. Proxy logs in to Zipline with username/password
2. Receives session cookies
3. Caches cookies and reuses for subsequent requests
4. Automatically re-authenticates when session expires (hourly check)

## Endpoints

### GET /health
Returns `OK` with status 200 if the service is running.

### GET /stats
Returns Zipline statistics in JSON format:

```json
{
    "files": 219,
    "storage_gb": 0.2,
    "storage_mb": 200.98,
    "storage": 200.98,
    "storage_unit": "MB"
}
```

The API intelligently returns:
- `storage` and `storage_unit`: Smart unit selection (MB when < 1GB, GB when >= 1GB)
- `storage_mb`: Always in megabytes
- `storage_gb`: Always in gigabytes
- `files`: Total number of files uploaded

## Docker Usage

```bash
docker run -d \
  --name zipline-proxy \
  -p 8427:5000 \
  -e ZIPLINE_URL=http://zipline:3000 \
  -e ZIPLINE_USERNAME=your_username \
  -e ZIPLINE_PASSWORD=your_password \
  -e CACHE_TIMEOUT=300 \
  ghcr.io/lioncitygaming/zipline-proxy:latest
```

## Docker Compose

```yaml
services:
  zipline-proxy:
    image: ghcr.io/lioncitygaming/zipline-proxy:latest
    container_name: zipline-proxy
    ports:
      - "8427:5000"
    environment:
      - ZIPLINE_URL=http://zipline:3000
      - ZIPLINE_USERNAME=your_username
      - ZIPLINE_PASSWORD=your_password
      - CACHE_TIMEOUT=300
    restart: unless-stopped
```

## Homepage Widget Configuration

Add this to your Homepage `services.yaml`:

### Option 1: Smart Unit Display (Recommended)
Shows MB when less than 1GB, automatically switches to GB when over 1GB:

```yaml
- Zipline:
    icon: zipline.png
    href: http://your-server:3000
    description: File Upload & Sharing
    widget:
        type: customapi
        url: http://your-server:8427/stats
        refreshInterval: 300000  # 5 minutes
        mappings:
            - field: files
              label: Files
              format: number
            - field: storage
              label: Storage
              format: number
              suffix: " {{storage_unit}}"
```

### Option 2: Always Show MB
```yaml
- Zipline:
    icon: zipline.png
    href: http://your-server:3000
    description: File Upload & Sharing
    widget:
        type: customapi
        url: http://your-server:8427/stats
        refreshInterval: 300000  # 5 minutes
        mappings:
            - field: files
              label: Files
              format: number
            - field: storage_mb
              label: Storage
              format: number
              suffix: " MB"
```

### Option 3: Always Show GB
```yaml
- Zipline:
    icon: zipline.png
    href: http://your-server:3000
    description: File Upload & Sharing
    widget:
        type: customapi
        url: http://your-server:8427/stats
        refreshInterval: 300000  # 5 minutes
        mappings:
            - field: files
              label: Files
              format: number
            - field: storage_gb
              label: Storage
              format: number
              suffix: " GB"
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
export ZIPLINE_URL=http://localhost:3000
export ZIPLINE_USERNAME=your_username
export ZIPLINE_PASSWORD=your_password
python app.py
```

## License

MIT
