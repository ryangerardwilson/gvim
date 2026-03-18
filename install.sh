#!/usr/bin/env bash
set -euo pipefail

APP=gvim
REPO="ryangerardwilson/gvim"
APP_HOME="$HOME/.${APP}"
INSTALL_DIR="$APP_HOME/bin"
APP_DIR="$APP_HOME/app"
SOURCE_DIR="$APP_DIR/source"
VENV_DIR="$APP_HOME/venv"
FILENAME="gvim-linux-x64.tar.gz"

usage() {
  cat <<EOF
${APP} Installer

Usage: install.sh [options]

Options:
  -h                         Show this help and exit
  -v [<version>]             Print the latest release version, or install a specific one
  -u                         Upgrade to the latest release only when newer
  -b <path>                  Install from a local checkout or source bundle
  -n                         Do not modify shell config to add to PATH

      --help                 Compatibility alias for -h
      --version [<version>]  Compatibility alias for -v
      --upgrade              Compatibility alias for -u
      --binary <path>        Compatibility alias for -b
      --no-modify-path       Compatibility alias for -n
EOF
}

requested_version=${VERSION:-}
show_latest=false
upgrade=false
no_modify_path=false
binary_path=""
latest_version_cache=""

print_message() {
  local level=$1
  local message=$2
  printf '%b\n' "$message"
}

die() {
  print_message error "$1"
  exit 1
}

create_venv() {
  local venv_log="$tmp_dir/venv-create.log"

  ensure_gvim_system_deps

  rm -rf "$VENV_DIR"
  if command -v virtualenv >/dev/null 2>&1; then
    if TMPDIR="$tmp_root" virtualenv --python "$PYTHON_BIN" "$VENV_DIR" >"$venv_log" 2>&1; then
      [[ -x "$VENV_DIR/bin/pip" ]] || die "virtualenv created ${VENV_DIR} without pip"
      return 0
    fi
  fi

  rm -rf "$VENV_DIR"
  if TMPDIR="$tmp_root" "$PYTHON_BIN" -m venv "$VENV_DIR" >"$venv_log" 2>&1; then
    [[ -x "$VENV_DIR/bin/pip" ]] || die "python3 -m venv created ${VENV_DIR} without pip"
    return 0
  fi

  if [[ -s "$venv_log" ]]; then
    cat "$venv_log" >&2
  fi
  if command -v virtualenv >/dev/null 2>&1; then
    die "Unable to create virtual environment with virtualenv or python3 -m venv."
  fi
  die "Unable to create virtual environment with python3 -m venv. Install python3-venv or virtualenv."
}

extract_source() {
  local src_path="$1"
  local out_dir="$2"

  rm -rf "$out_dir"

  if [[ -d "$src_path" ]]; then
    mkdir -p "$out_dir"
    cp -R "$src_path"/. "$out_dir"/
  else
    command -v tar >/dev/null 2>&1 || die "'tar' is required but not installed."
    tar -xzf "$src_path" -C "$tmp_dir"
    local extracted
    extracted="$(find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    [[ -n "$extracted" ]] || die "Failed to extract source bundle"
    mv "$extracted" "$out_dir"
  fi

  rm -rf "$out_dir/.git" "$out_dir/.github" "$out_dir/dist" "$out_dir/.ruff_cache" "$out_dir/.pytest_cache"
  find "$out_dir" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
}

get_latest_version() {
  command -v curl >/dev/null 2>&1 || die "'curl' is required but not installed."
  if [[ -z "$latest_version_cache" ]]; then
    local release_url
    local tag
    release_url="$(curl -fsSL -o /dev/null -w "%{url_effective}" "https://github.com/${REPO}/releases/latest")" \
      || die "Unable to determine latest release"
    tag="${release_url##*/}"
    tag="${tag#v}"
    [[ -n "$tag" && "$tag" != "latest" ]] || die "Unable to determine latest release"
    latest_version_cache="$tag"
  fi
  printf '%s\n' "$latest_version_cache"
}

GVIM_SYSTEM_DEPS_READY=false

require_sudo() {
  if [[ $EUID -ne 0 ]]; then
    command -v sudo >/dev/null 2>&1 || die "sudo is required to install system packages"
  fi
}

system_deps_ok() {
  type -P python3 >/dev/null 2>&1 || return 1
  command python3 -c "import gi; gi.require_version('Gtk', '4.0')" >/dev/null 2>&1 || return 1
  return 0
}

install_system_deps() {
  [[ -f /etc/os-release ]] || die "Unsupported OS: missing /etc/os-release"
  # shellcheck disable=SC1091
  . /etc/os-release

  case "${ID}" in
    ubuntu|debian)
      require_sudo
      sudo apt-get update
      sudo apt-get install -y \
        python3 \
        python3-venv \
        python3-gi \
        gir1.2-gtk-4.0 \
        libgirepository1.0-dev \
        gcc \
        pkg-config \
        libcairo2-dev
      ;;
    fedora)
      require_sudo
      sudo dnf install -y \
        python3 \
        python3-gobject \
        gtk4 \
        gobject-introspection-devel \
        gcc \
        pkgconf-pkg-config \
        cairo-gobject-devel
      ;;
    arch)
      require_sudo
      sudo pacman -S --noconfirm \
        python \
        python-gobject \
        gtk4 \
        gobject-introspection \
        gcc \
        pkgconf \
        cairo
      ;;
    *)
      die "Unsupported distro for system deps: ${ID}"
      ;;
  esac
}

ensure_gvim_system_deps() {
  if [[ "$GVIM_SYSTEM_DEPS_READY" == "true" ]]; then
    return
  fi
  if system_deps_ok; then
    GVIM_SYSTEM_DEPS_READY=true
    return
  fi
  install_system_deps
  system_deps_ok || die "GTK system dependencies are still unavailable after install"
  GVIM_SYSTEM_DEPS_READY=true
}

python3() {
  ensure_gvim_system_deps
  command python3 "$@"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -v|--version)
      if [[ -n "${2:-}" && "${2:0:1}" != "-" ]]; then
        requested_version="${2#v}"
        shift 2
      else
        show_latest=true
        shift
      fi
      ;;
    -u|--upgrade)
      upgrade=true
      shift
      ;;
    -b|--binary)
      [[ -n "${2:-}" ]] || { echo "Error: -b requires a path"; exit 1; }
      binary_path="$2"
      shift 2
      ;;
    -n|--no-modify-path)
      no_modify_path=true
      shift
      ;;

    *)
      echo "Warning: Unknown option '$1'" >&2
      shift
      ;;
  esac
done

if $show_latest; then
  [[ "$upgrade" == false && -z "$binary_path" && -z "$requested_version" ]] || \
    die "-v (no arg) cannot be combined with other options"
  get_latest_version
  exit 0
fi

if $upgrade; then
  [[ -z "$binary_path" ]] || die "-u cannot be used with -b"
  [[ -z "$requested_version" ]] || die "-u cannot be combined with -v <version>"
  requested_version="$(get_latest_version)"
  if command -v "${APP}" >/dev/null 2>&1; then
    installed_version="$(${APP} -v 2>/dev/null || true)"
    installed_version="${installed_version#v}"
    if [[ -n "$installed_version" && "$installed_version" == "$requested_version" ]]; then
      print_message info "${APP} version ${requested_version} already installed"
      exit 0
    fi
  fi
fi

command -v python3 >/dev/null 2>&1 || { print_message error "'python3' is required but not installed."; exit 1; }
PYTHON_BIN="python3"
mkdir -p "$INSTALL_DIR" "$APP_DIR"
tmp_root="${TMPDIR:-${XDG_CACHE_HOME:-$HOME/.cache}/${APP}/tmp}"
mkdir -p "$tmp_root"
tmp_dir="${tmp_root}/${APP}_install_$$"
rm -rf "$tmp_dir"
mkdir -p "$tmp_dir"
trap 'rm -rf "$tmp_dir"' EXIT

if [[ -n "$binary_path" ]]; then
  [[ -e "$binary_path" ]] || { print_message error "Source bundle not found: $binary_path"; exit 1; }
  print_message info "\nInstalling ${APP} from local source: ${binary_path}"
  extract_source "$binary_path" "$SOURCE_DIR"
  specific_version="local"
else
  command -v curl >/dev/null 2>&1 || { print_message error "'curl' is required but not installed."; exit 1; }

  if [[ -z "$requested_version" ]]; then
    specific_version="$(get_latest_version)"
  else
    requested_version="${requested_version#v}"
    specific_version="${requested_version}"
    http_status=$(curl -sI -o /dev/null -w "%{http_code}" "https://github.com/${REPO}/releases/tag/v${requested_version}")
    if [[ "$http_status" == "404" ]]; then
      print_message error "Release v${requested_version} not found"
      print_message info "See available releases: https://github.com/${REPO}/releases"
      exit 1
    fi
  fi

  if command -v "${APP}" >/dev/null 2>&1; then
    installed_version="$(${APP} -v 2>/dev/null || true)"
    installed_version="${installed_version#v}"
    if [[ -n "$installed_version" && "$installed_version" == "$specific_version" ]]; then
      print_message info "${APP} version ${specific_version} already installed"
      exit 0
    fi
  fi

  url="https://github.com/${REPO}/releases/download/v${specific_version}/${FILENAME}"
  print_message info "\nInstalling ${APP} version: ${specific_version}"
  curl -# -L -o "$tmp_dir/$FILENAME" "$url"
  extract_source "$tmp_dir/$FILENAME" "$SOURCE_DIR"
fi

[[ -f "${SOURCE_DIR}/main.py" ]] || die "Source bundle missing main.py"
[[ -f "${SOURCE_DIR}/_version.py" ]] || die "Source bundle missing _version.py"

create_venv
if [[ -f "${SOURCE_DIR}/requirements.txt" ]]; then
  "$VENV_DIR/bin/python" -m pip install --disable-pip-version-check --no-cache-dir --only-binary=:all: -r "${SOURCE_DIR}/requirements.txt" >/dev/null
fi

cat > "${INSTALL_DIR}/${APP}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${VENV_DIR}/bin/python" "${SOURCE_DIR}/main.py" "\$@"
EOF
chmod 755 "${INSTALL_DIR}/${APP}"

enable_system_site_packages() {
  local pyvenv_cfg="$VENV_DIR/pyvenv.cfg"
  [[ -f "$pyvenv_cfg" ]] || die "Missing venv config: $pyvenv_cfg"

  if grep -q '^include-system-site-packages = true$' "$pyvenv_cfg"; then
    return
  fi

  if grep -q '^include-system-site-packages = false$' "$pyvenv_cfg"; then
    sed -i 's/^include-system-site-packages = false$/include-system-site-packages = true/' "$pyvenv_cfg"
  else
    printf '\ninclude-system-site-packages = true\n' >> "$pyvenv_cfg"
  fi
}

verify_runtime_dependencies() {
  "$VENV_DIR/bin/python" -c "import gi; gi.require_version('Gtk', '4.0')"
  "$VENV_DIR/bin/python" -c "import numpy, matplotlib, pandas, rgw_cli_contract"
}

rewrite_launcher() {
  cat > "${INSTALL_DIR}/${APP}" <<EOF
#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${VENV_DIR}/bin/python"
APP_MAIN="${SOURCE_DIR}/main.py"

if [[ ! -x "\$PYTHON_BIN" ]]; then
  echo "gvim venv missing. Reinstall with install.sh." >&2
  exit 1
fi

case "\${1:-}" in
  conf|init|e|-h|--help|-v|--version|-u|--upgrade)
    exec "\$PYTHON_BIN" "\$APP_MAIN" "\$@"
    ;;
  q)
    ;;
  -*)
    exec "\$PYTHON_BIN" "\$APP_MAIN" "\$@"
    ;;
esac

nohup "\$PYTHON_BIN" "\$APP_MAIN" "\$@" >/dev/null 2>&1 &
disown
EOF
  chmod 755 "${INSTALL_DIR}/${APP}"
}

install_bash_completion() {
  local source_completion="${SOURCE_DIR}/completions_gvim.bash"
  local completion_dir="${XDG_CONFIG_HOME:-$HOME/.config}/bash_completion.d"
  local bashrc="$HOME/.bashrc"

  [[ -f "$source_completion" ]] || return

  mkdir -p "$completion_dir"
  cp "$source_completion" "$completion_dir/gvim"

  if [[ ! -e "$bashrc" ]]; then
    touch "$bashrc"
  fi

  if [[ -w "$bashrc" ]] && ! grep -Fq "bash_completion.d/gvim" "$bashrc" 2>/dev/null; then
    printf '\n# GVIM bash completion\nif [ -r "%s/gvim" ]; then\n  . "%s/gvim"\nfi\n' \
      "$completion_dir" "$completion_dir" >> "$bashrc"
  fi
}

ensure_gvim_system_deps
enable_system_site_packages
verify_runtime_dependencies
rewrite_launcher
install_bash_completion

add_to_path() {
  local config_file=$1
  local command=$2

  if grep -Fxq "$command" "$config_file" 2>/dev/null; then
    print_message info "PATH entry already present in $config_file"
  elif [[ -w "$config_file" ]]; then
    {
      echo ""
      echo "# ${APP}"
      echo "$command"
    } >> "$config_file"
    print_message info "Added ${APP} to PATH in $config_file"
  else
    print_message info "Add this to your shell config:"
    print_message info "  $command"
  fi
}

if [[ "$no_modify_path" != "true" ]]; then
  if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-$HOME/.config}
    current_shell=$(basename "${SHELL:-bash}")

    case "$current_shell" in
      zsh)  config_candidates=("$HOME/.zshrc" "$HOME/.zshenv" "$XDG_CONFIG_HOME/zsh/.zshrc" "$XDG_CONFIG_HOME/zsh/.zshenv") ;;
      bash) config_candidates=("$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile" "$XDG_CONFIG_HOME/bash/.bashrc" "$XDG_CONFIG_HOME/bash/.bash_profile") ;;
      fish) config_candidates=("$HOME/.config/fish/config.fish") ;;
      *)    config_candidates=("$HOME/.profile" "$HOME/.bashrc") ;;
    esac

    config_file=""
    for f in "${config_candidates[@]}"; do
      if [[ -f "$f" ]]; then
        config_file="$f"
        break
      fi
    done

    if [[ -z "$config_file" ]]; then
      print_message info "No shell config file found. Manually add:"
      print_message info "  export PATH=$INSTALL_DIR:\$PATH"
    else
      if [[ "$current_shell" == "fish" ]]; then
        add_to_path "$config_file" "fish_add_path $INSTALL_DIR"
      else
        add_to_path "$config_file" "export PATH=$INSTALL_DIR:\$PATH"
      fi
    fi
  fi
fi

print_message info "Run: ${APP} -h"
