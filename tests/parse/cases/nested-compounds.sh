for i in 1 2; do
  while false; do :; done
  until true; do :; done
  case $i in 1) if true; then echo one; fi ;; esac
done | sort
