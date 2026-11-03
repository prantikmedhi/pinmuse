#!/usr/bin/env bash
# pinmuse installer: the CLI, plus the skill for every AI agent found on this machine.
#
#   curl -fsSL https://raw.githubusercontent.com/prantikmedhi/pinmuse/main/install.sh | bash
#   ./install.sh --all        # install the skill for every supported agent, even if not detected
#   ./install.sh --mcp        # also register the MCP server with claude / codex / gemini CLIs
set -euo pipefail

REPO="https://github.com/prantikmedhi/pinmuse"
ALL=0; MCP=0
for a in "$@"; do case "$a" in --all) ALL=1 ;; --mcp) MCP=1 ;; esac; done

say() { printf "\033[1;35m▸\033[0m %s\n" "$*"; }

# 1) Get the source (works from a clone or via curl | bash)
if [ -f "$(dirname "${BASH_SOURCE[0]:-$0}")/skills/pinmuse/SKILL.md" ]; then
  SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
else
  SRC="${PINMUSE_HOME:-$HOME/.pinmuse}"
  if [ -d "$SRC/.git" ]; then git -C "$SRC" pull -q; else git clone -q --depth 1 "$REPO" "$SRC"; fi
fi
say "source: $SRC"

# 2) Install the CLI
if command -v uv >/dev/null; then uv tool install --force "$SRC[mcp]" >/dev/null
elif command -v pipx >/dev/null; then pipx install --force "$SRC[mcp]" >/dev/null
else python3 -m pip install --user -q "$SRC[mcp]"; fi
say "cli: $(command -v pinmuse || echo 'pinmuse (add ~/.local/bin to PATH)')"

# 3) Link the skill into each agent's skills folder
# agent-name : home-dir-that-means-it's-installed : skills-dir
TARGETS=(
  "Claude Code:$HOME/.claude:$HOME/.claude/skills"
  "Codex:$HOME/.codex:$HOME/.codex/skills"
  "Agents (shared):$HOME/.agents:$HOME/.agents/skills"
  "Gemini CLI:$HOME/.gemini:$HOME/.gemini/skills"
  "Antigravity (agy):$HOME/.gemini/antigravity:$HOME/.gemini/antigravity/skills"
  "opencode:$HOME/.config/opencode:$HOME/.config/opencode/skills"
  "OpenClaw:$HOME/.openclaw:$HOME/.openclaw/skills"
  "Hermes Agent:$HOME/.hermes:$HOME/.hermes/skills"
  "Cursor:$HOME/.cursor:$HOME/.cursor/skills"
)
for t in "${TARGETS[@]}"; do
  IFS=":" read -r name home dir <<<"$t"
  if [ "$ALL" = 1 ] || [ -d "$home" ]; then
    mkdir -p "$dir"
    ln -sfn "$SRC/skills/pinmuse" "$dir/pinmuse"
    say "skill → $name ($dir/pinmuse)"
  fi
done

# 4) Optionally register the MCP server
if [ "$MCP" = 1 ]; then
  command -v claude >/dev/null && claude mcp add --scope user pinmuse -- pinmuse mcp >/dev/null 2>&1 && say "mcp → Claude Code"
  command -v codex  >/dev/null && codex mcp add pinmuse -- pinmuse mcp >/dev/null 2>&1 && say "mcp → Codex"
  command -v gemini >/dev/null && gemini mcp add pinmuse pinmuse mcp >/dev/null 2>&1 && say "mcp → Gemini CLI"
fi

echo
say "done. Try:  pinmuse create \"ceramic vase\" --inspo \"minimal ceramics\" -t story -f ig-story --title \"Slow Living\""
say "image models: pinmuse list providers   (set OPENAI_API_KEY / GEMINI_API_KEY / FAL_KEY … or run ComfyUI)"
