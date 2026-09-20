# test-filetypes-378.sh - the file-type and mode predicates of `test`.
# FILE-KIND, the engine primitive since Iteration 307, answers only
# none, regular, directory or other, which cannot tell a block device
# from a socket or see the set-user bit; -b -c -p -S -h -L -u -g -k were
# all missing until the FILE-MODE primitive of Iteration 378.
d=/tmp/relf-378.$$
rm -rf $d; mkdir -p $d; cd $d
: > plain
mkdir adir
ln -s plain goodlink
ln -s nowhere brokenlink
mkfifo afifo 2>/dev/null
chmod u+s,g+s plain 2>/dev/null
chmod +t adir 2>/dev/null
for f in plain adir goodlink brokenlink afifo /dev/null; do
  printf '%s:' "$f"
  test -f "$f" && printf ' -f'
  test -d "$f" && printf ' -d'
  test -h "$f" && printf ' -h'
  test -L "$f" && printf ' -L'
  test -c "$f" && printf ' -c'
  test -b "$f" && printf ' -b'
  test -p "$f" && printf ' -p'
  test -S "$f" && printf ' -S'
  test -e "$f" && printf ' -e'
  echo
done
test -u plain && echo "plain is setuid"
test -g plain && echo "plain is setgid"
test -k adir && echo "adir is sticky"
test -u adir || echo "adir is not setuid"
test -h nosuchfile || echo "missing file is not a link"
cd /tmp; rm -rf $d
