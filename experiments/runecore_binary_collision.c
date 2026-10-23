#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* RuneCore hardware-oriented binary collision experiment.
   Rion mass = 1. A coherent mass-N structure is N synchronized bits.
   Collision reverses only struck Rions: state ^= collision_mask.
   Relationship test below measures disagreement only; it does NOT invent
   repair, fracture, attraction, or any other post-collision behavior. */

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
            if ((out ^ mask) != state) return 0;
            if (((state ^ out) & all) != mask) return 0;
            if (popcount64(state ^ out) != popcount64(mask)) return 0;
        }
    }
    return 1;
}

static int test_mass_conservation(void) {
    for (unsigned n = 1; n <= 63; ++n) {
        const uint64_t membership = (UINT64_C(1) << n) - 1;
        for (unsigned k = 0; k <= n; ++k) {
            const uint64_t state = 0;
            const uint64_t mask = k == 0 ? 0 : ((UINT64_C(1) << k) - 1);
            const uint64_t out = state ^ mask;
            const uint64_t membership_after = membership;
            if (popcount64(membership_after) != n) return 0;
            if ((out & ~membership_after) != 0) return 0;
            if (popcount64(mask) != k) return 0;
        }
    }
    return 1;
}

/* Ring topology: each Rion is related to its next neighbor, including N-1 -> 0.
   An edge is synchronized when endpoint flow bits match; disagreement is merely
   observed as a broken synchronization edge. No consequence is assigned. */
static unsigned ring_disagreements(uint64_t state, unsigned n) {
    unsigned broken = 0;
    for (unsigned i = 0; i < n; ++i) {
        unsigned j = (i + 1) % n;
        unsigned a = (unsigned)((state >> i) & 1u);
        unsigned b = (unsigned)((state >> j) & 1u);
        broken += (a != b);
    }
    return broken;
}

static int test_relationship_observation(void) {
    for (unsigned n = 2; n <= 16; ++n) {
        const uint64_t all = (UINT64_C(1) << n) - 1;
        if (ring_disagreements(0, n) != 0) return 0;
        if (ring_disagreements(all, n) != 0) return 0;

        for (uint64_t mask = 0; mask <= all; ++mask) {
            uint64_t out = mask; /* coherent zero state XOR collision mask */
            unsigned broken = ring_disagreements(out, n);
            if (broken > n) return 0;
            if (broken & 1u) return 0; /* binary transitions around a closed ring are even */
        }
    }
    return 1;
}

static void print_case(unsigned n, unsigned k) {
    uint64_t mask = k ? ((UINT64_C(1) << k) - 1) : 0;
    uint64_t out = mask;
    long net = (long)n - 2L * (long)popcount64(out);
    printf("M=%u collisions=%u reversed=%u net=%ld/%u coherent=%s ring_disagreements=%u\n",
           n, k, popcount64(out), net, n,
           (out == 0 || out == ((UINT64_C(1) << n) - 1)) ? "yes" : "no",
           ring_disagreements(out, n));
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
    if (!test_relationship_observation()) {
        fprintf(stderr, "FAIL relationship disagreement observation test\n");
        return EXIT_FAILURE;
    }

    puts("PASS exhaustive 8-Rion state/mask space: 65,536 transitions");
    puts("PASS collision operation is exactly XOR / bit reversal");
    puts("PASS applying identical collision twice restores original state");
    puts("PASS constituent mass/count is conserved through collisions");
    puts("PASS closed-ring relationship disagreement observation for N=2..16");
    puts("NOTE no post-collision repair/fracture rule was assumed");
    print_case(2, 1);
    print_case(10, 1);
    print_case(10, 5);
    print_case(10, 10);
    return EXIT_SUCCESS;
}
