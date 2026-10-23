#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/*
 * Successor audit for the unresolved S118 x 3 relationship.
 *
 * We do NOT invent a transition selector. Instead, for each one-of-three
 * promoted state, exhaust every possible next three-bit state and retain
 * only transitions compatible with the currently earned constraints:
 *   1) promoted units remain binary;
 *   2) constituent mass remains 354;
 *   3) the shared one-of-three relationship total remains one active unit;
 *   4) no rule is added that privileges a member or direction.
 *
 * Existing local collision rule is XOR. For any current/next pair the
 * required collision mask is current XOR next. This tells us which masks
 * could realize a candidate transition; it does not choose a mask.
 */

enum { N = 3, MASS_PER_UNIT = 118, TOTAL_MASS = 354 };

static int pop3(unsigned x) {
    return (int)(x & 1u) + (int)((x >> 1) & 1u) + (int)((x >> 2) & 1u);
}

static void bits(unsigned x, char out[4]) {
    out[0] = (x & 4u) ? '1' : '0';
    out[1] = (x & 2u) ? '1' : '0';
    out[2] = (x & 1u) ? '1' : '0';
    out[3] = '\0';
}

int main(void) {
    if (N * MASS_PER_UNIT != TOTAL_MASS) return EXIT_FAILURE;

    int current_states = 0;
    int total_legal_successors = 0;
    int self_successors = 0;
    int changed_successors = 0;
    int masks_by_pop[4] = {0,0,0,0};

    for (unsigned cur = 0; cur < 8; ++cur) {
        if (pop3(cur) != 1) continue;
        ++current_states;
        int local_legal = 0;
        char cb[4]; bits(cur, cb);
        printf("CURRENT %s\n", cb);

        for (unsigned next = 0; next < 8; ++next) {
            if (pop3(next) != 1) continue;
            unsigned mask = cur ^ next; /* earned XOR collision operation */
            char nb[4], mb[4]; bits(next, nb); bits(mask, mb);
            printf("  LEGAL next=%s xor_mask=%s collisions=%d\n",
                   nb, mb, pop3(mask));
            ++local_legal;
            ++total_legal_successors;
            if (next == cur) ++self_successors;
            else ++changed_successors;
            ++masks_by_pop[pop3(mask)];
        }
        if (local_legal != 3) {
            fprintf(stderr, "FAIL expected 3 legal successors per unresolved state\n");
            return EXIT_FAILURE;
        }
    }

    if (current_states != 3 || total_legal_successors != 9 ||
        self_successors != 3 || changed_successors != 6) {
        fprintf(stderr, "FAIL successor enumeration mismatch\n");
        return EXIT_FAILURE;
    }

    /* Moving the single active share requires flipping exactly two units. */
    if (masks_by_pop[0] != 3 || masks_by_pop[1] != 0 ||
        masks_by_pop[2] != 6 || masks_by_pop[3] != 0) {
        fprintf(stderr, "FAIL XOR mask classification mismatch\n");
        return EXIT_FAILURE;
    }

    printf("PASS three unresolved one-of-three states audited\n");
    printf("PASS each state has 3 conservation-compatible successors\n");
    printf("PASS 9 total legal state transitions: 3 unchanged + 6 changed\n");
    printf("PASS every changed successor requires XOR reversal of exactly 2 promoted units\n");
    printf("OBSERVATION earned constraints do not select stay, clockwise, or counterclockwise successor\n");
    printf("UNKNOWN transition remains underdetermined without an additional relationship/collision event rule\n");
    printf("STOP no cycling, randomness, decay, fracture, geometry, direction, or instability was invented\n");
    return EXIT_SUCCESS;
}
