#!/bin/bash
#
# setup.sh - Plugin setup script for tk-claude-plugins
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory (repository root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

info() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1" >&2; }
step() { echo -e "${BLUE}→${NC} $1"; }

# Enable plugin in ~/.claude/settings.json
# Usage: enable_plugin <plugin_name>
enable_plugin() {
    local plugin_name="$1"
    local plugin_key="${plugin_name}@tk-plugins"
    local settings_file="$HOME/.claude/settings.json"

    step "プラグインを有効化: $plugin_key"

    mkdir -p "$HOME/.claude"

    # Create settings.json if it doesn't exist
    if [[ ! -f "$settings_file" ]]; then
        echo '{"enabledPlugins":{}}' > "$settings_file"
    fi

    # Check if jq is available
    if command -v jq &> /dev/null; then
        # Use jq for JSON manipulation
        local tmp_file=$(mktemp)
        jq --arg key "$plugin_key" '.enabledPlugins[$key] = true' "$settings_file" > "$tmp_file"
        mv "$tmp_file" "$settings_file"
        info "有効化完了: $plugin_key"
    else
        # Fallback: simple text manipulation (less robust but works for simple cases)
        if grep -q "\"$plugin_key\"" "$settings_file" 2>/dev/null; then
            info "既に有効: $plugin_key"
        else
            # Add plugin to enabledPlugins
            if grep -q '"enabledPlugins": {}' "$settings_file" 2>/dev/null; then
                # Empty enabledPlugins
                sed -i.bak "s/\"enabledPlugins\": {}/\"enabledPlugins\": {\"$plugin_key\": true}/" "$settings_file"
            elif grep -q '"enabledPlugins": {' "$settings_file" 2>/dev/null; then
                # Non-empty enabledPlugins - add before closing brace
                sed -i.bak "s/\"enabledPlugins\": {/\"enabledPlugins\": {\"$plugin_key\": true, /" "$settings_file"
            else
                warn "settings.json の形式が不明です。手動で追加してください:"
                echo "  \"$plugin_key\": true"
                return
            fi
            rm -f "${settings_file}.bak"
            info "有効化完了: $plugin_key"
        fi
    fi
}

# Install plugin to ~/.claude/plugins/cache/ and register in installed_plugins.json
# Usage: install_plugin <plugin_name>
install_plugin() {
    local plugin_name="$1"
    local plugin_key="${plugin_name}@tk-plugins"
    local plugin_src="$REPO_DIR/plugins/$plugin_name"
    local plugin_json="$plugin_src/.claude-plugin/plugin.json"
    local installed_plugins_file="$HOME/.claude/plugins/installed_plugins.json"

    # Read version from plugin.json
    if [[ ! -f "$plugin_json" ]]; then
        error "plugin.json が見つかりません: $plugin_json"
        return 1
    fi

    local version
    if command -v jq &> /dev/null; then
        version=$(jq -r '.version' "$plugin_json")
    else
        version=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$plugin_json" | sed 's/.*"\([^"]*\)"$/\1/')
    fi

    if [[ -z "$version" ]]; then
        error "バージョンを取得できません"
        return 1
    fi

    step "プラグインをインストール: $plugin_key (v$version)"

    # Create cache directory and copy plugin
    local cache_dir="$HOME/.claude/plugins/cache/tk-plugins/$plugin_name/$version"
    mkdir -p "$cache_dir"

    # Copy plugin contents (excluding .git, scripts, etc.)
    rsync -a --delete \
        --exclude='.git' \
        --exclude='scripts/' \
        "$plugin_src/" "$cache_dir/"

    info "コピー完了: $cache_dir"

    # Update installed_plugins.json
    mkdir -p "$HOME/.claude/plugins"

    if [[ ! -f "$installed_plugins_file" ]]; then
        echo '{"version":2,"plugins":{}}' > "$installed_plugins_file"
    fi

    local current_time=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
    local git_sha=""
    if [[ -d "$REPO_DIR/.git" ]]; then
        git_sha=$(cd "$REPO_DIR" && git rev-parse HEAD 2>/dev/null || echo "")
    fi

    if command -v jq &> /dev/null; then
        local tmp_file=$(mktemp)
        jq --arg key "$plugin_key" \
           --arg path "$cache_dir" \
           --arg ver "$version" \
           --arg time "$current_time" \
           --arg sha "$git_sha" \
           '.plugins[$key] = [{
               "scope": "user",
               "installPath": $path,
               "version": $ver,
               "installedAt": $time,
               "lastUpdated": $time,
               "gitCommitSha": $sha
           }]' "$installed_plugins_file" > "$tmp_file"
        mv "$tmp_file" "$installed_plugins_file"
        info "installed_plugins.json 更新完了"
    else
        warn "jq がインストールされていないため、installed_plugins.json を手動で更新してください"
        echo "  $plugin_key を追加してください"
    fi
}

# Register skill to ~/.claude/skills/
# Usage: register_skill <skill_name> <skill_path>
register_skill() {
    local skill_name="$1"
    local skill_path="$2"

    step "スキルを登録: $skill_name"

    SKILLS_DIR="$HOME/.claude/skills"
    mkdir -p "$SKILLS_DIR"

    LINK_PATH="$SKILLS_DIR/$skill_name"

    # Remove existing symlink if exists
    if [[ -L "$LINK_PATH" ]]; then
        rm "$LINK_PATH"
    fi

    # Create symlink
    ln -sf "$skill_path" "$LINK_PATH"
    info "スキル登録完了: $LINK_PATH -> $skill_path"
}

# Add ~/bin to PATH in shell config
add_bin_to_path() {
    step "~/bin をPATHに追加..."

    # Determine shell config file
    SHELL_CONFIG="$HOME/.zshrc"
    if [[ "$SHELL" == *"bash"* ]]; then
        SHELL_CONFIG="$HOME/.bashrc"
    fi

    # Check if already in config file
    if grep -q 'export PATH="\$HOME/bin:\$PATH"' "$SHELL_CONFIG" 2>/dev/null; then
        info "既に $SHELL_CONFIG に記載済み（次回ログイン時に有効）"
    else
        echo '' >> "$SHELL_CONFIG"
        echo '# Added by tk-claude-plugins setup' >> "$SHELL_CONFIG"
        echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_CONFIG"
        info "$SHELL_CONFIG に追加完了"
        warn "反映するには: source $SHELL_CONFIG"
    fi
}

# Setup notion-image plugin
setup_notion_image() {
    echo ""
    echo "================================"
    echo " notion-image セットアップ"
    echo "================================"
    echo ""

    install_plugin "notion-image"
    register_skill "notion-image" "$REPO_DIR/plugins/notion-image/skills/notion-image"
    enable_plugin "notion-image"

    CONFIG_DIR="$HOME/.config/notion-image"
    CONFIG_FILE="$CONFIG_DIR/.env"
    BIN_DIR="$HOME/bin"
    SCRIPT_PATH="$REPO_DIR/plugins/notion-image/scripts/upload_to_notion.sh"

    # Step 1: Create config directory
    step "設定ディレクトリを作成..."
    if [[ -d "$CONFIG_DIR" ]]; then
        info "既に存在: $CONFIG_DIR"
    else
        mkdir -p "$CONFIG_DIR"
        chmod 700 "$CONFIG_DIR"
        info "作成完了: $CONFIG_DIR"
    fi

    # Step 2: Create config file template
    step "設定ファイルを作成..."
    if [[ -f "$CONFIG_FILE" ]]; then
        warn "既に存在: $CONFIG_FILE (スキップ)"
    else
        cat > "$CONFIG_FILE" << 'EOF'
# Notion Integration Token
# 取得方法: https://www.notion.so/my-integrations
NOTION_TOKEN=ntn_xxxxxxxxxxxxx

# デフォルトのアップロード先ページID（オプション）
# NotionページURLの末尾32文字（ハイフンなし）
DEFAULT_PAGE_ID=
EOF
        chmod 600 "$CONFIG_FILE"
        info "作成完了: $CONFIG_FILE"
    fi

    # Step 3: Create bin directory and symlinks
    step "コマンドをPATHに追加..."
    mkdir -p "$BIN_DIR"

    # notion-upload
    local UPLOAD_SCRIPT="$REPO_DIR/plugins/notion-image/scripts/upload_to_notion.sh"
    if [[ -L "$BIN_DIR/notion-upload" ]]; then
        rm "$BIN_DIR/notion-upload"
    fi
    ln -s "$UPLOAD_SCRIPT" "$BIN_DIR/notion-upload"
    chmod +x "$UPLOAD_SCRIPT"
    info "シンボリックリンク作成: $BIN_DIR/notion-upload"

    # notion-get-blocks
    local BLOCKS_SCRIPT="$REPO_DIR/plugins/notion-image/scripts/notion_get_blocks.sh"
    if [[ -L "$BIN_DIR/notion-get-blocks" ]]; then
        rm "$BIN_DIR/notion-get-blocks"
    fi
    ln -s "$BLOCKS_SCRIPT" "$BIN_DIR/notion-get-blocks"
    chmod +x "$BLOCKS_SCRIPT"
    info "シンボリックリンク作成: $BIN_DIR/notion-get-blocks"

    # notion-upload-batch
    local BATCH_SCRIPT="$REPO_DIR/plugins/notion-image/scripts/upload_to_notion_batch.sh"
    if [[ -L "$BIN_DIR/notion-upload-batch" ]]; then
        rm "$BIN_DIR/notion-upload-batch"
    fi
    ln -s "$BATCH_SCRIPT" "$BIN_DIR/notion-upload-batch"
    chmod +x "$BATCH_SCRIPT"
    info "シンボリックリンク作成: $BIN_DIR/notion-upload-batch"

    # Check if ~/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
        add_bin_to_path
    else
        info "~/bin は既にPATHに含まれています"
    fi

    # Manual steps
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo " 残りの手動ステップ"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Notion Integrationを作成:"
    echo "   → https://www.notion.so/my-integrations"
    echo "   → New integration → 名前入力 → Submit"
    echo "   → Capabilities: Read content ✓, Insert content ✓"
    echo ""
    echo "2. トークンを設定ファイルに記入:"
    echo "   # ntn_xxx... をコピーしたトークンに置き換えて実行"
    echo "   echo \"NOTION_TOKEN=ntn_xxxxxxxxxxxxx\" > $CONFIG_FILE"
    echo ""
    echo "3. Notionでページに接続:"
    echo "   → アップロード先ページを開く"
    echo "   → 右上「...」→「接続」→ Integration選択"
    echo ""
    echo "4. テスト:"
    echo "   → notion-upload /path/to/image.png PAGE_ID"
    echo ""
}

# Setup codex plugin
setup_codex() {
    echo ""
    echo "================================"
    echo " codex セットアップ"
    echo "================================"
    echo ""

    install_plugin "codex"
    register_skill "codex" "$REPO_DIR/plugins/codex/skills/codex"
    enable_plugin "codex"

    CONFIG_DIR="$HOME/.config/codex"
    CONFIG_FILE="$CONFIG_DIR/.env"
    BIN_DIR="$HOME/bin"
    SCRIPT_PATH="$REPO_DIR/plugins/codex/scripts/codex-review.sh"

    # Step 1: Create config directory
    step "設定ディレクトリを作成..."
    if [[ -d "$CONFIG_DIR" ]]; then
        info "既に存在: $CONFIG_DIR"
    else
        mkdir -p "$CONFIG_DIR"
        chmod 700 "$CONFIG_DIR"
        info "作成完了: $CONFIG_DIR"
    fi

    # Step 2: Create config file template
    step "設定ファイルを作成..."
    if [[ -f "$CONFIG_FILE" ]]; then
        warn "既に存在: $CONFIG_FILE (スキップ)"
    else
        cat > "$CONFIG_FILE" << 'EOF'
# サンドボックスモード: read-only | workspace-write | full-write
CODEX_SANDBOX=read-only
EOF
        chmod 600 "$CONFIG_FILE"
        info "作成完了: $CONFIG_FILE"
    fi

    # Step 3: Create bin directory and symlink
    step "コマンドをPATHに追加..."
    mkdir -p "$BIN_DIR"

    if [[ -L "$BIN_DIR/codex-review" ]]; then
        rm "$BIN_DIR/codex-review"
    fi

    ln -s "$SCRIPT_PATH" "$BIN_DIR/codex-review"
    chmod +x "$SCRIPT_PATH"
    info "シンボリックリンク作成: $BIN_DIR/codex-review"

    # Check if ~/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
        add_bin_to_path
    else
        info "~/bin は既にPATHに含まれています"
    fi

    # Check if codex is installed
    step "Codex CLIを確認..."
    if command -v codex &> /dev/null; then
        info "インストール済み: $(which codex)"
    else
        warn "Codex CLIがインストールされていません"
        echo ""
        echo "  以下のコマンドでインストール:"
        echo ""
        echo "    npm install -g @openai/codex"
        echo ""
    fi

    # Check OPENAI_API_KEY
    step "OPENAI_API_KEYを確認..."
    if [[ -n "$OPENAI_API_KEY" ]]; then
        info "設定済み"
    else
        warn "OPENAI_API_KEYが設定されていません"
        echo ""
        echo "  以下を ~/.zshrc または ~/.bashrc に追加:"
        echo ""
        echo "    export OPENAI_API_KEY=sk-..."
        echo ""
    fi
}

# Setup gemini plugin
setup_gemini() {
    echo ""
    echo "================================"
    echo " gemini セットアップ"
    echo "================================"
    echo ""

    install_plugin "gemini"
    register_skill "gemini" "$REPO_DIR/plugins/gemini/skills/gemini"
    enable_plugin "gemini"

    CONFIG_DIR="$HOME/.config/gemini"
    CONFIG_FILE="$CONFIG_DIR/.env"
    BIN_DIR="$HOME/bin"
    SCRIPT_PATH="$REPO_DIR/plugins/gemini/scripts/gemini-review.sh"

    # Step 1: Create config directory
    step "設定ディレクトリを作成..."
    if [[ -d "$CONFIG_DIR" ]]; then
        info "既に存在: $CONFIG_DIR"
    else
        mkdir -p "$CONFIG_DIR"
        chmod 700 "$CONFIG_DIR"
        info "作成完了: $CONFIG_DIR"
    fi

    # Step 2: Create config file template
    step "設定ファイルを作成..."
    if [[ -f "$CONFIG_FILE" ]]; then
        warn "既に存在: $CONFIG_FILE (スキップ)"
    else
        cat > "$CONFIG_FILE" << 'EOF'
# モデル指定（空欄でデフォルト）
GEMINI_MODEL=
EOF
        chmod 600 "$CONFIG_FILE"
        info "作成完了: $CONFIG_FILE"
    fi

    # Step 3: Create bin directory and symlink
    step "コマンドをPATHに追加..."
    mkdir -p "$BIN_DIR"

    if [[ -L "$BIN_DIR/gemini-review" ]]; then
        rm "$BIN_DIR/gemini-review"
    fi

    ln -s "$SCRIPT_PATH" "$BIN_DIR/gemini-review"
    chmod +x "$SCRIPT_PATH"
    info "シンボリックリンク作成: $BIN_DIR/gemini-review"

    # Check if ~/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
        add_bin_to_path
    else
        info "~/bin は既にPATHに含まれています"
    fi

    # Check if gemini is installed
    step "Gemini CLIを確認..."
    if command -v gemini &> /dev/null; then
        info "インストール済み: $(which gemini)"
    else
        warn "Gemini CLIがインストールされていません"
        echo ""
        echo "  以下のコマンドでインストール:"
        echo ""
        echo "    npm install -g @google/gemini-cli"
        echo ""
    fi
}

# Setup peer-review plugin
setup_peer_review() {
    echo ""
    echo "================================"
    echo " peer-review セットアップ"
    echo "================================"
    echo ""

    install_plugin "peer-review"
    register_skill "peer-review" "$REPO_DIR/plugins/peer-review/skills/peer-review"
    register_skill "check-reference" "$REPO_DIR/plugins/peer-review/skills/check-reference"
    enable_plugin "peer-review"

    info "peer-review はスクリプト不要のオーケストレーションスキルです"
}

# Setup all plugins
setup_all() {
    setup_codex
    setup_gemini
    setup_notion_image
    setup_peer_review
}

# Show usage
usage() {
    echo "Usage: $0 [plugin|all]"
    echo ""
    echo "Plugins:"
    echo "  codex         - Codex CLIレビュープラグイン"
    echo "  gemini        - Gemini CLIレビュープラグイン"
    echo "  notion-image  - Notion画像アップロードプラグイン"
    echo "  peer-review   - Professor/Student文書レビュープラグイン"
    echo "  all           - すべてのプラグイン"
    echo ""
    echo "Examples:"
    echo "  $0 codex"
    echo "  $0 gemini"
    echo "  $0 notion-image"
    echo "  $0 all"
}

# Main
main() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    case "$1" in
        codex)
            setup_codex
            ;;
        gemini)
            setup_gemini
            ;;
        notion-image)
            setup_notion_image
            ;;
        peer-review)
            setup_peer_review
            ;;
        all)
            setup_all
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "Unknown plugin: $1"
            usage
            exit 1
            ;;
    esac

    echo ""
    info "セットアップ完了!"
    echo ""
}

main "$@"
