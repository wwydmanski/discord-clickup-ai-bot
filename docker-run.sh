#!/bin/bash

# Discord ClickUp Bot Docker Management Script
# Usage: ./docker-run.sh [command]

set -e

BOT_NAME="discord-clickup-bot"
IMAGE_NAME="discord-clickup-bot:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_error ".env file not found!"
        print_status "Please create .env file based on env.example"
        print_status "cp env.example .env"
        exit 1
    fi
}

# Build the Docker image
build() {
    print_status "Building Docker image..."
    docker build -t $IMAGE_NAME .
    print_success "Docker image built successfully!"
}

# Run the bot
run() {
    check_env
    print_status "Starting Discord bot..."
    docker-compose up -d
    print_success "Bot started! Check logs with: $0 logs"
}

# Stop the bot
stop() {
    print_status "Stopping Discord bot..."
    docker-compose down
    print_success "Bot stopped!"
}

# Restart the bot
restart() {
    print_status "Restarting Discord bot..."
    stop
    sleep 2
    run
}

# Show logs
logs() {
    print_status "Showing bot logs (Ctrl+C to exit)..."
    docker-compose logs -f discord-bot
}

# Show status
status() {
    print_status "Bot status:"
    docker-compose ps
    
    if docker-compose ps | grep -q "Up"; then
        print_success "Bot is running!"
        
        # Show health status
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $BOT_NAME 2>/dev/null || echo "no-healthcheck")
        if [ "$HEALTH" = "healthy" ]; then
            print_success "Health check: Healthy"
        elif [ "$HEALTH" = "unhealthy" ]; then
            print_error "Health check: Unhealthy"
        else
            print_warning "Health check: $HEALTH"
        fi
    else
        print_warning "Bot is not running"
    fi
}

# Clean up
clean() {
    print_status "Cleaning up Docker resources..."
    docker-compose down --rmi local --volumes --remove-orphans
    print_success "Cleanup completed!"
}

# Update and rebuild
update() {
    print_status "Updating bot..."
    stop
    build
    run
    print_success "Bot updated and restarted!"
}

# Show help
help() {
    echo "Discord ClickUp Bot Docker Management"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build      - Build Docker image"
    echo "  run        - Start the bot"
    echo "  stop       - Stop the bot"
    echo "  restart    - Restart the bot"
    echo "  logs       - Show bot logs"
    echo "  status     - Show bot status"
    echo "  clean      - Clean up Docker resources"
    echo "  update     - Update and restart bot"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 run           # Start the bot"
    echo "  $0 logs          # Show logs"
    echo "  $0 status        # Check if bot is running"
    echo "  $0 restart       # Restart the bot"
}

# Main script logic
case "${1:-help}" in
    "build")
        build
        ;;
    "run")
        run
        ;;
    "stop")
        stop
        ;;
    "restart")
        restart
        ;;
    "logs")
        logs
        ;;
    "status")
        status
        ;;
    "clean")
        clean
        ;;
    "update")
        update
        ;;
    "help"|"--help"|"-h")
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac 