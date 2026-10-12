i=0
while IFS= read -r line; do
  i=$((i+1))
  if [ "$line" = HEREDOC ]; then printf 'cat << EOF\né ü 日本 $(echo ä)\nEOF\n' > c$i.sh
  else printf '%s\n' "$line" > c$i.sh; fi
done < cases.txt
n=0; d=0
for f in $(ls c*.sh | sort -V); do
  n=$((n+1))
  ref=$(LC_ALL=C timeout 10 dash $f 2>&1 < /dev/null | od -An -tx1 | tr -s ' \n' ' ')
  bsh=$(LC_ALL=C timeout 10 bash $f 2>&1 < /dev/null | od -An -tx1 | tr -s ' \n' ' ')
  for sh in relfshasm64 relfsh64 relfsh-native; do
    got=$(LC_ALL=C timeout 10 /home/claude/relf/$sh $f 2>&1 < /dev/null | od -An -tx1 | tr -s ' \n' ' ')
    if [ "$got" != "$ref" ]; then
      d=$((d+1))
      echo "DIFF $f $sh: $(head -c 70 $f | tr '\n' '~')"
      echo "   dash: $(LC_ALL=C dash $f 2>&1 < /dev/null | head -3 | tr '\n' '~' | cut -c1-100)"
      echo "   relf: $(LC_ALL=C /home/claude/relf/$sh $f 2>&1 < /dev/null | head -3 | tr '\n' '~' | cut -c1-100)"
      [ "$got" = "$bsh" ] && echo "   (relf agrees with bash)"
    fi
  done
done
echo "cases: $n, differences from dash: $d"
