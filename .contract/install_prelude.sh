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
