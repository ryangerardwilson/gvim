_gtkv_complete() {
  local cur
  cur="${COMP_WORDS[COMP_CWORD]}"
  local prev
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  case "${cur}" in
    --image=*)
      COMPREPLY=( $(compgen -f -- "${cur#--image=}") )
      ;;
    --export=*)
      COMPREPLY=( $(compgen -f -- "${cur#--export=}") )
      ;;
    -*)
      COMPREPLY=( $(compgen -W "-h --help -v --version -u --upgrade -e --export -q" -- "${cur}") )
      ;;
    *)
      if [[ "${prev}" == "-e" || "${prev}" == "--export" ]]; then
        COMPREPLY=( $(compgen -f -- "${cur}") )
      else
        local opts
        opts=( $(compgen -W "init" -- "${cur}") )
        local files
        files=( $(compgen -f -X '!*.docv' -- "${cur}") )
        COMPREPLY=( "${opts[@]}" "${files[@]}" )
      fi
      ;;
  esac
  compopt -o filenames 2>/dev/null || true
}

complete -F _gtkv_complete gtkv
