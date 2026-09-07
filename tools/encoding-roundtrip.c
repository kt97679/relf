#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>

/* ---- the proposed encoding, i386 shape (4-byte cell) ---- */
typedef uint32_t UNS; typedef int32_t INT;
#define IDX_BITS   10                 /* 1024 primitive slots  */
#define PAY_SHIFT  (2 + IDX_BITS)     /* payload starts at bit 12 */
#define IDX_MASK   ((1u << IDX_BITS) - 1)

#define I_LIT   200u                  /* reserved primitive indices */
#define I_BR    201u
#define I_0BR   202u

#define ENC_PRIM(i)     (((UNS)(i) << 2) | 1u)
#define ENC_PAY(i,v)    ((((UNS)(INT)(v)) << PAY_SHIFT) | ((UNS)(i) << 2) | 1u)
#define ENC_CALL(off)   ((UNS)(INT)(off))            /* 0 mod 4 already */

#define TOK_IDX(t)      (((t) >> 2) & IDX_MASK)
#define TOK_PAY(t)      ((INT)(t) >> PAY_SHIFT)

int main(void) {
    INT vals[] = {0,1,-1,2,3,-2216,2196,127404,-524288,524287};
    int bad=0;
    for (unsigned k=0;k<sizeof vals/sizeof*vals;k++) {
        INT v=vals[k];
        UNS t=ENC_PAY(I_LIT,v);
        if (!(t&1)) { printf("FAIL not-a-primitive tag for %d\n",v); bad=1; }
        if (TOK_IDX(t)!=I_LIT) { printf("FAIL idx %u for %d\n",TOK_IDX(t),v); bad=1; }
        if (TOK_PAY(t)!=v)     { printf("FAIL payload %d != %d\n",TOK_PAY(t),v); bad=1; }
    }
    for (unsigned i=0;i<1024;i++) {
        UNS t=ENC_PRIM(i);
        if (!(t&1)||TOK_IDX(t)!=i) { printf("FAIL prim %u\n",i); bad=1; }
    }
    for (INT off=-4096; off<=4096; off+=4) {
        UNS t=ENC_CALL(off);
        if (off && (t&1)) { printf("FAIL call %d looks like a primitive\n",off); bad=1; }
    }
    printf("payload range: %d .. %d\n", -(1<<(31-PAY_SHIFT)), (1<<(31-PAY_SHIFT))-1);
    printf(bad?"BAD\n":"all round-trips OK\n");
    return bad;
}
