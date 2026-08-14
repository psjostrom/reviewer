#!/bin/sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_SOURCE="$SCRIPT_DIR/opencode"
GLOBAL_TARGET="${HOME}/.config/opencode"
PROJECT_TARGET="$(pwd)/.opencode"

usage() {
  cat <<'EOF'
Usage:
  ./install-opencode.sh install [--project]
  ./install-opencode.sh uninstall [--project]
  ./install-opencode.sh list [--project]
EOF
}

is_owned_link() {
  link="$1"
  [ -L "$link" ] || return 1
  case "$(readlink "$link")" in
    "$PLUGIN_SOURCE"/*) return 0 ;;
  esac
  return 1
}

prune_stale_links() {
  target="$1"
  for source_dir in "$PLUGIN_SOURCE"/*; do
    [ -d "$source_dir" ] || continue
    category="$(basename "$source_dir")"
    [ -d "$target/$category" ] || continue
    for link in "$target/$category"/*; do
      [ -L "$link" ] || continue
      if is_owned_link "$link" && [ ! -e "$link" ]; then
        rm "$link"
        echo "  pruned stale $link"
      fi
    done
  done
}

link_plugin() {
  target="$1"
  prune_stale_links "$target"
  for source_dir in "$PLUGIN_SOURCE"/*; do
    [ -d "$source_dir" ] || continue
    category="$(basename "$source_dir")"
    mkdir -p "$target/$category"
    for source in "$source_dir"/*; do
      [ -e "$source" ] || continue
      dest="$target/$category/$(basename "$source")"
      if [ -e "$dest" ] || [ -L "$dest" ]; then
        if ! is_owned_link "$dest"; then
          echo "  skip $dest — exists and is not Reviewer-owned"
          continue
        fi
      fi
      ln -sfn "$source" "$dest"
      echo "  linked $dest"
    done
  done
  echo "Installed Reviewer -> $target"
}

unlink_plugin() {
  target="$1"
  prune_stale_links "$target"
  for source_dir in "$PLUGIN_SOURCE"/*; do
    [ -d "$source_dir" ] || continue
    category="$(basename "$source_dir")"
    for source in "$source_dir"/*; do
      [ -e "$source" ] || continue
      link="$target/$category/$(basename "$source")"
      if is_owned_link "$link"; then
        rm "$link"
        echo "  removed $link"
      fi
    done
  done
  echo "Uninstalled Reviewer from $target"
}

list_plugin() {
  target="$1"
  if is_owned_link "$target/agents/reviewer.md"; then
    echo "Reviewer installed: $target"
  else
    echo "Reviewer not installed: $target"
  fi
}

command="${1:-}"
project=false
case "$#" in
  1) ;;
  2) [ "$2" = "--project" ] && project=true || { usage >&2; exit 1; } ;;
  *) usage >&2; exit 1 ;;
esac

case "$command" in
  install|uninstall|list) ;;
  *) usage >&2; exit 1 ;;
esac

target="$GLOBAL_TARGET"
[ "$project" = true ] && target="$PROJECT_TARGET"

case "$command" in
  install) link_plugin "$target" ;;
  uninstall) unlink_plugin "$target" ;;
  list) list_plugin "$target" ;;
esac
