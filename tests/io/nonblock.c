/*
 *  tests/io/nonblock.c - run a command with O_NONBLOCK set on its
 *  standard input: the condition under which read(2) returns EAGAIN
 *  and KEY has to wait rather than give up. There is no portable shell
 *  command that sets the flag, hence this.
 *
 *      nonblock /path/to/program args...
 */
#include <fcntl.h>
#include <unistd.h>

int main(int argc, char **argv) {
    int fl = fcntl(0, F_GETFL);
    if (argc < 2 || fl < 0 || fcntl(0, F_SETFL, fl | O_NONBLOCK) < 0)
        return 125;
    execv(argv[1], argv + 1);
    return 126;
}
