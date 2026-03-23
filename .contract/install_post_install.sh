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
  "$VENV_DIR/bin/python" -c "import numpy, matplotlib, pandas"
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

ensure_gvim_system_deps
enable_system_site_packages
verify_runtime_dependencies
rewrite_launcher
