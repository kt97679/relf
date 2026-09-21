# tests/crashers - reproducers of crashes found by the fuzzer

Each file is a script `tools/crashfuzz.py` found crashing this shell,
shrunk to the smallest input that still does. The name says which
build it was found on (`crash-4-byte-...`, `crash-8-byte-...`); the
bug may well reproduce on both.

These are OPEN until they are fixed, and GOALS.md's "Open now" lists
them. When one is fixed, its case moves into a real suite - usually a
differential case or a `tests/shell` assertion - and the file here is
deleted in the same commit. A file here is a to-do, not a test.

    for f in tests/crashers/*.sh; do ./relfsh "$f"; done
