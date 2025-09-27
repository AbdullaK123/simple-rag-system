#!/bin/bash

# Ruthlessly kill any processes using port 5432
echo "Ruthlessly killing any process using port 5432..."

# Method 1: Use lsof to find processes
PIDS=$(lsof -ti:5432 2>/dev/null)
if [ ! -z "$PIDS" ]; then
    for pid in $PIDS; do
        echo "Killing process $pid on port 5432 (via lsof)"
        kill -9 $pid 2>/dev/null || true
    done
fi

# Method 2: Use netstat to find processes
PIDS=$(netstat -tlnp 2>/dev/null | grep :5432 | awk '{print $7}' | cut -d'/' -f1 | grep -E '^[0-9]+$' 2>/dev/null)
if [ ! -z "$PIDS" ]; then
    for pid in $PIDS; do
        echo "Killing process $pid on port 5432 (via netstat)"
        kill -9 $pid 2>/dev/null || true
    done
fi

# Method 3: Use ss to find processes
PIDS=$(ss -tlnp 2>/dev/null | grep :5432 | sed -n 's/.*pid=\([0-9]*\).*/\1/p' 2>/dev/null)
if [ ! -z "$PIDS" ]; then
    for pid in $PIDS; do
        echo "Killing process $pid on port 5432 (via ss)"
        kill -9 $pid 2>/dev/null || true
    done
fi

# Method 4: Use fuser to kill processes on the port
echo "Using fuser to kill any remaining processes on port 5432..."
fuser -k 5432/tcp 2>/dev/null || true

sleep 3

# Stop and remove existing postgres container if it exists
echo "Cleaning up existing postgres container..."
docker stop rag-service-db 2>/dev/null || true
docker rm rag-service-db 2>/dev/null || true

# Also clean up any containers that might be using port 5432
echo "Cleaning up any Docker containers using port 5432..."
docker ps -q --filter "publish=5432" | xargs -r docker stop 2>/dev/null || true
docker ps -aq --filter "publish=5432" | xargs -r docker rm 2>/dev/null || true

# Wait a moment to ensure port is fully released
echo "Waiting for port 5432 to be fully released..."
sleep 2

# Start PostgreSQL 17 with pgvector
echo "Starting PostgreSQL 17 container..."
if ! docker run -d \
    --name rag-service-db \
    -p 5432:5432 \
    -e POSTGRES_DB=rag_service_db \
    -e POSTGRES_USER=rag_user \
    -e POSTGRES_PASSWORD=password \
    -v rag_service_data:/var/lib/postgresql/data \
    --restart unless-stopped \
    postgres:17; then
    echo "Failed to start container. Checking what's still using port 5432..."
    lsof -i:5432 2>/dev/null || true
    netstat -tlnp | grep :5432 2>/dev/null || true
    ss -tlnp | grep :5432 2>/dev/null || true
    docker ps -a --filter "name=rag-service-db"
    exit 1
fi

# Wait for postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Test connection
echo "Testing connection..."
until docker exec rag-service-db pg_isready -U rag_user -d rag_service_db; do
    echo "Waiting for database to be ready..."
    sleep 2
done

echo "PostgreSQL 17 is ready!"
echo "Running migrations..."
alembic upgrade head
echo "Connection string: postgresql+asyncpg://rag_user:password@localhost:5432/rag_service_db"