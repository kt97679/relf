# Positional parameters inside ${...}, not just the bare $N spelling.
set -- aa bb cc
echo "[${1}] [${2}] [${3}]"
echo "[${#1}] [${9:-none}] [${2#a}] [${3:+yes}]"
set -- x
echo "[${2:-fallback}] [${1:+set}]"
