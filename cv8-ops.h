/*  cv8-ops.h - GENERATED from opcodes.tab by tools/gen-opcodes.sh.
 *  Do not edit: change opcodes.tab and run make. The engine's
 *  dispatch tables - the direct primitives in order, the escaped
 *  ones in order, every other opcode at its number (CV8.md 2.2).  */
#define NDIRECT 35
#define NESC    65
#define CV8_OPS_DIRECT \
    &&L_noop, &&L_exit, &&L_lit, &&L_branch, &&L_0branch, &&L_drop, \
    &&L_dup, &&L_swap, &&L_rot, &&L_over, &&L_cfetch, &&L_fetch, \
    &&L_cstore, &&L_store, &&L_and, &&L_or, &&L_xor, &&L_fromr, &&L_tor, \
    &&L_rfetch, &&L_eq, &&L_ult, &&L_lt, &&L_plus, &&L_negate, &&L_lshift, \
    &&L_rshift, &&L_ummult, &&L_umdiv, &&L_dplus, &&L_type, &&L_spfetch, \
    &&L_spstore, &&L_rpfetch, &&L_rpstore
#define CV8_OPS_ESCAPED \
    &&L_bye, &&L_openfile, &&L_closefile, &&L_system, &&L_reposfile, \
    &&L_filepos, &&L_delfile, &&L_filesize, &&L_fork, &&L_execve, \
    &&L_waitpid, &&L_pipe, &&L_dup2, &&L_getenv, &&L_setenv, &&L_sysexit, \
    &&L_chdir, &&L_getcwd, &&L_sysargc, &&L_sysarg, &&L_getpid, \
    &&L_unsetenv, &&L_allocate, &&L_free, &&L_resize, &&L_getpwhome, \
    &&L_getfsize, &&L_setfsize, &&L_read, &&L_write, &&L_poll, &&L_rawmode, \
    &&L_move, &&L_fill, &&L_compare, &&L_scan, &&L_cstrlen, &&L_isatty, \
    &&L_opendir, &&L_readdir, &&L_closedir, &&L_access, &&L_kill, \
    &&L_umask, &&L_cputimes, &&L_sigaction, &&L_sigpending, &&L_termraw, \
    &&L_termrestore, &&L_filekind, &&L_getrlimit, &&L_setrlimit, \
    &&L_waitnohang, &&L_getppid, &&L_envat, &&L_setpgid, &&L_tcsetpgrp, \
    &&L_tcgetpgrp, &&L_waitjob, &&L_filemode, &&L_localtime, &&L_dupfrom, \
    &&L_tcplisten, &&L_tcpaccept, &&L_tcpconnect
#define CV8_OPS_OTHER \
    [0x23] = &&L_lit32, [0x24] = &&L_dovar, [0x25] = &&L_dodoes, \
    [0x26] = &&L_lit8, [0x27] = &&L_lit8x, [0x28] = &&LX_plus, \
    [0x29] = &&LX_eq, [0x2A] = &&LX_store, [0x2B] = &&LX_fetch, \
    [0x2C] = &&LX_lshift, [0x2D] = &&LX_rshift, [0x2E] = &&LX_cfetch, \
    [0x2F] = &&LX_cstore, [0x30] = &&LX_and, [0x31] = &&LX_or, \
    [0x32] = &&LX_xor, [0x33] = &&LX_lit, [0x34] = &&LX_lt, \
    [0x35] = &&LX_ult, [0x36] = &&LX_over, [0x37] = &&LX_drop, \
    [0x38] = &&LX_dup, [0x39] = &&LX_swap, [0x3A] = &&LX_rot, \
    [0x3B] = &&LX_tor, [0x3C] = &&LX_fromr, [0x3D] = &&LX_rfetch, \
    [0x3E] = &&LX_negate, [0x3F] = &&L_branch8, [0x40] = &&L_0branch8, \
    [0x61] = &&L_lit0, [0x62] = &&L_lit1, [0x63] = &&L_litm1, \
    [0x64] = &&L_vf, [0x65] = &&L_vs, [0x66] = &&L_lsave, \
    [0x67] = &&L_lrest, [0x68] = &&L_lstore, [0x69] = &&L_lzero, \
    [0x6A] = &&L_zeq, [0x6B] = &&L_sub, [0x6C] = &&L_ne, [0x6D] = &&L_zlt, \
    [0x6E] = &&L_sgt, [0x6F] = &&L_2dup, [0x70] = &&L_2drop, \
    [0x71] = &&L_charp, [0x72] = &&L_onep, [0x73] = &&L_cellp, \
    [0x74] = &&L_cells, [0x75] = &&L_onem, [0x76] = &&L_invert, \
    [0x77] = &&L_count, [0x78] = &&L_aligned, [0x79] = &&L_addi, \
    [0x7A] = &&L_addix, [0x7B] = &&L_eqi, [0x7C] = &&L_eqix, \
    [0x7D] = &&L_lit64, [0x7E] = &&L_esc
