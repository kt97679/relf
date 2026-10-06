#include <stdint.h>
/* shell.4's NAME-HASH in C: FNV-1a over a NUL-terminated name, then the final mix */
uint64_t name_hash(const unsigned char *s) {
    uint64_t h = 2166136261u;
    for (; *s; s++) h = (h ^ *s) * 16777619u;
    h ^= h >> 16; h *= 73244475u; h ^= h >> 16;
    return h;
}
