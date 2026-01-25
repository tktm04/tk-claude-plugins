#!/bin/bash
#
# upload_to_notion.sh - Upload images directly to Notion using File Uploads API
# Simple approach: No external storage needed (no R2, S3, etc.)
#

set -e

# Configuration file path
CONFIG_DIR="${HOME}/.config/notion-image"
CONFIG_FILE="${CONFIG_DIR}/.env"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handling
error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${GREEN}$1${NC}"
}

warn() {
    echo -e "${YELLOW}$1${NC}"
}

# Load configuration
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        error "Config file not found: $CONFIG_FILE
Please create it with the following variables:
  NOTION_TOKEN=ntn_xxxxxxxxxxxxx

Optionally:
  DEFAULT_PAGE_ID=your_default_page_id"
    fi

    # Source the config file
    set -a
    source "$CONFIG_FILE"
    set +a

    # Validate required variables
    [[ -z "$NOTION_TOKEN" ]] && error "NOTION_TOKEN not set"
}

# Detect MIME type from file extension
get_mime_type() {
    local file="$1"
    local ext="${file##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

    case "$ext" in
        png)  echo "image/png" ;;
        jpg|jpeg) echo "image/jpeg" ;;
        gif)  echo "image/gif" ;;
        webp) echo "image/webp" ;;
        svg)  echo "image/svg+xml" ;;
        *)    error "Unsupported file type: .$ext (supported: png, jpg, jpeg, gif, webp, svg)" ;;
    esac
}

# Step 1: Create file upload object
create_file_upload() {
    local response
    response=$(curl -s -X POST "https://api.notion.com/v1/file_uploads" \
        -H "Authorization: Bearer $NOTION_TOKEN" \
        -H "Notion-Version: 2022-06-28" \
        -H "Content-Type: application/json")

    # Extract ID from response
    local upload_id
    upload_id=$(echo "$response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [[ -z "$upload_id" ]]; then
        echo "API Response: $response" >&2
        error "Failed to create file upload object"
    fi

    echo "$upload_id"
}

# Step 2: Send file to upload object
send_file() {
    local upload_id="$1"
    local file_path="$2"

    local response
    response=$(curl -s -X POST "https://api.notion.com/v1/file_uploads/$upload_id/send" \
        -H "Authorization: Bearer $NOTION_TOKEN" \
        -H "Notion-Version: 2022-06-28" \
        -F "file=@$file_path")

    # Check for error
    if echo "$response" | grep -q '"status":"uploaded"'; then
        return 0
    else
        echo "API Response: $response" >&2
        error "Failed to send file"
    fi
}

# Step 3: Attach image to page
attach_to_page() {
    local page_id="$1"
    local upload_id="$2"

    local response
    response=$(curl -s -X PATCH "https://api.notion.com/v1/blocks/$page_id/children" \
        -H "Authorization: Bearer $NOTION_TOKEN" \
        -H "Notion-Version: 2022-06-28" \
        -H "Content-Type: application/json" \
        -d "{\"children\": [{\"type\": \"image\", \"image\": {\"type\": \"file_upload\", \"file_upload\": {\"id\": \"$upload_id\"}}}]}")

    # Check for error
    if echo "$response" | grep -q '"results"'; then
        return 0
    else
        echo "API Response: $response" >&2
        error "Failed to attach image to page"
    fi
}

# Main upload function
upload_to_notion() {
    local local_file="$1"
    local page_id="$2"

    # Validate file exists
    [[ ! -f "$local_file" ]] && error "File not found: $local_file"

    # Get MIME type (validates file type)
    local content_type
    content_type=$(get_mime_type "$local_file")

    info "Uploading: $local_file"
    info "  -> Content-Type: $content_type"

    # Step 1: Create upload object
    info "Step 1/3: Creating upload object..."
    local upload_id
    upload_id=$(create_file_upload)
    info "  -> Upload ID: $upload_id"

    # Step 2: Send file
    info "Step 2/3: Sending file..."
    send_file "$upload_id" "$local_file"
    info "  -> File sent successfully"

    # Step 3: Attach to page (if page_id provided)
    if [[ -n "$page_id" ]]; then
        info "Step 3/3: Attaching to page..."
        attach_to_page "$page_id" "$upload_id"
        info "  -> Attached to page: $page_id"
    else
        warn "Step 3/3: Skipped (no page_id provided)"
        echo ""
        info "To attach later, use:"
        echo "  Upload ID: $upload_id"
        echo ""
        warn "Note: Upload expires in 1 hour if not attached!"
    fi

    echo ""
    info "Upload successful!"
}

# Show usage
usage() {
    echo "Usage: $0 <image_file_path> [page_id]"
    echo ""
    echo "Uploads an image directly to Notion using the File Uploads API."
    echo ""
    echo "Arguments:"
    echo "  <image_file_path>  Path to the image file (required)"
    echo "  [page_id]          Notion page ID to attach the image (optional)"
    echo "                     If not provided, uses DEFAULT_PAGE_ID from config"
    echo ""
    echo "Supported formats: png, jpg, jpeg, gif, webp, svg"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/image.png"
    echo "  $0 /path/to/image.png abc123def456..."
}

# Main entry point
main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    load_config

    local file_path="$1"
    local page_id="${2:-$DEFAULT_PAGE_ID}"

    upload_to_notion "$file_path" "$page_id"
}

main "$@"
