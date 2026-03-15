_gvim_complete() {
  local cur
  cur="${COMP_WORDS[COMP_CWORD]}"
  local prev
  prev="${COMP_WORDS[COMP_CWORD-1]}"

  if (( COMP_CWORD == 1 )); then
    COMPREPLY=( $(compgen -W "-h --help -v --version -u --upgrade conf init e q" -- "${cur}") )
    COMPREPLY+=( $(compgen -f -X '!*.gvim' -- "${cur}") )
  elif [[ "${prev}" == "q" ]]; then
    COMPREPLY=( $(compgen -f -X '!*.gvim' -- "${cur}") )
  elif [[ "${cur}" == -* ]]; then
    COMPREPLY=( $(compgen -W "-h --help -v --version -u --upgrade" -- "${cur}") )
  else
    COMPREPLY=( $(compgen -f -X '!*.gvim' -- "${cur}") )
  fi

  compopt -o filenames 2>/dev/null || true
}

complete -F _gvim_complete gvim
