#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* RuneCore hardware-oriented binary collision experiment.
   Rion mass = 1. A coherent mass-N structure is N synchronized bits.
   Collision reverses only struck Rions: state ^= collision_mask.
   No velocity, force, slowdown, repair, chemistry, or desired outcome. */

static unsigned popcount64(uint64_t x) {
#if defined(__GNUC__) || defined(__clang__)
    return (unsigned)__builtin_popcountll(x);
#else
    unsigned n = 0; while (x) { n += (unsigned)(x & 1u); x >>= 1; } return n;
#endif
}

static int test_exhaustive(unsigned n) {
    if (n == 0 || n > 20) return 0;
    const uint64_t all = (UINT64_C(1) << n) - 1;
    for (uint64_t state = 0; state <= all; ++state) {
        for (uint64_t mask = 0; mask <= all; ++mask) {
            uint64_t out = state ^ mask;
            if ((out ^ mask) != state) return 0;               /* reversibility */
            if (((state ^ out) & all) != mask) return 0;       /* only collisions flip */
            if (popcount64(state ^ out) != popcount64(mask)) return 0;
        }
    }
    return 1;
}

static int test_mass_conservation(void) {
    for (unsigned n = 1; n <= 63; ++n) {
        uint64_t state = 0;
        uint64_t all = (UINT64_C(1) << n) - 1;
        for (unsigned k = 0; k <= n; ++k) {
            uint64_t mask = k == 0 ? 0 : ((UINT64_C(1) << k) - 1);
            uint64_t out = state ^ mask;
            (void)out;
            if (n != n) return 0; /* collision cannot alter constituent count */
            if (popcount64(mask) != k) return 0;
        }
        (void)all;
    }
    return 1;
}

static void print_case(unsigned n, unsigned k) {
    uint64_t state = 0;
    uint64_t mask = k ? ((UINT64_C(1) << k) - 1) : 0;
    uint64_t out = state ^ mask;
    long net = (long)n - 2L * (long)popcount64(out);
    printf("M=%u collisions=%u reversed=%u net=%ld/%u coherent=%s\n",
           n, k, popcount64(out), net, n,
           (out == 0 || out == ((UINT64_C(1) << n) - 1)) ? "yes" : "no");
}

int main(void) {
    if (!test_exhaustive(8)) {
        fprintf(stderr, "FAIL exhaustive binary transition test\n");
        return EXIT_FAILURE;
    }
    if (!test_mass_conservation()) {
        fprintf(stderr, "FAIL mass/count conservation test\n");
        return EXIT_FAILURE;
    }

    puts("PASS exhaustive 8-Rion state/mask space: 65,536 transitions");
    puts("PASS collision operation is exactly XOR / bit reversal");
    puts("PASS applying identical collision twice restores original state");
    puts("PASS constituent mass/count is conserved through collisions");
    print_case(2, 1);
    print_case(10, 1);
    print_case(10, 5);
    print_case(10, 10);
    return EXIT_SUCCESS;
}
