/*  cv8-ops.h - GENERATED from opcodes.tab by tools/gen-opcodes.sh.
 *  Do not edit: change opcodes.tab and run make. The engine's
 *  dispatch tables - the direct primitives in order, the escaped
 *  ones in order, every other opcode at its number (CV8.md 2.2).  */
#define NDIRECT 26
#define NESC    76
#define CV8_OPS_DIRECT \
    &&L_noop, &&L_exit, &&L_lit, &&L_branch, &&L_0branch, &&L_drop, \
    &&L_dup, &&L_swap, &&L_rot, &&L_over, &&L_cfetch, &&L_fetch, \
    &&L_cstore, &&L_store, &&L_and, &&L_or, &&L_xor, &&L_fromr, &&L_tor, \
    &&L_rfetch, &&L_eq, &&L_ult, &&L_lt, &&L_plus, &&L_ummult, &&L_spfetch
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
    &&L_tcplisten, &&L_tcpaccept, &&L_tcpconnect, &&L_negate, &&L_lshift, \
    &&L_rshift, &&L_umdiv, &&L_dplus, &&L_type, &&L_spstore, &&L_rpfetch, \
    &&L_rpstore, &&L_dictlimit, &&L_chmod
#define CV8_OPS_OTHER \
    [0x1A] = &&L_lit32, [0x1B] = &&L_dovar, [0x1C] = &&L_dodoes, \
    [0x1D] = &&L_lit8, [0x3F] = &&L_branch8, [0x40] = &&L_0branch8, \
    [0x41] = &&L_plusstore, [0x42] = &&L_qdup, [0x43] = &&L_i, \
    [0x44] = &&L_loop, [0x45] = &&L_qdo, [0x46] = &&L_execute, \
    [0x47] = &&L_atxt, [0x61] = &&L_lit0, [0x62] = &&L_lit1, \
    [0x63] = &&L_litm1, [0x64] = &&L_vf, [0x65] = &&L_vs, \
    [0x66] = &&L_lsave, [0x67] = &&L_lrest, [0x68] = &&L_lstore, \
    [0x69] = &&L_lzero, [0x6A] = &&L_zeq, [0x6B] = &&L_sub, \
    [0x6C] = &&L_ne, [0x6D] = &&L_zlt, [0x6E] = &&L_sgt, [0x6F] = &&L_2dup, \
    [0x70] = &&L_2drop, [0x72] = &&L_onep, [0x73] = &&L_cellp, \
    [0x74] = &&L_cells, [0x75] = &&L_onem, [0x77] = &&L_count, \
    [0x79] = &&L_addi, [0x7B] = &&L_eqi, [0x7D] = &&L_lit64, \
    [0x7E] = &&L_esc
#define OPC_BRANCH8 0x3F   /* the loop opcodes step over it */
