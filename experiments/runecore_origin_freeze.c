#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* RuneCore absolute-origin freeze experiment.

   Deliberately narrow claim:
   - R1 is one occupied binary Rion slot at absolute origin.
   - Each insertion adds exactly one Rion to the bounded structure.
   - No Big Bang, expansion, gravity, velocity, chemistry, atomic identity,
     attraction, repulsion, displacement, merge energy, or explosion is coded.
   - Existing earned collision operation remains XOR for directional state.
   - Satomicnumbermax is only a STOP CEILING. This experiment does not claim
     that the ceiling is physically derivable from the present rules.

   The hardware question is therefore architectural: can repeated R1 insertion
   conserve membership and freeze exactly at the configured ceiling WITHOUT
   executing an over-ceiling insertion? */

enum { SATOMICNUMBERMAX = 118 };

typedef struct {
    uint8_t flow;      /* 0 or 1 only */
    uint8_t occupied;  /* membership / mass-1 slot */
} Rion;

typedef struct {
    Rion r[SATOMICNUMBERMAX + 1]; /* +1 is a sentinel, never valid membership */
    unsigned count;
    unsigned insertions;
    int frozen;
} OriginSwath;

static int valid(const OriginSwath *s) {
    if (s->count > SATOMICNUMBERMAX) return 0;
    unsigned occupied = 0;
    for (unsigned i = 0; i < SATOMICNUMBERMAX + 1; ++i) {
        if (s->r[i].flow > 1u) return 0;
        occupied += s->r[i].occupied ? 1u : 0u;
    }
    return occupied == s->count;
}

/* Insert R1 at the same relational origin. We do NOT invent a spatial response.
   The new Rion simply becomes another member of the bounded origin structure.
   Its initial flow is 0 because no earned rule tells us to choose otherwise. */
static int insert_r1(OriginSwath *s) {
    if (s->frozen || s->count >= SATOMICNUMBERMAX) {
        s->frozen = 1;
        return 0;
    }
    s->r[s->count].occupied = 1;
    s->r[s->count].flow = 0;
    s->count++;
    s->insertions++;
    if (s->count == SATOMICNUMBERMAX) s->frozen = 1;
    return 1;
}

/* Earned binary collision behavior from earlier hardware test. */
static void collide(Rion *r) {
    if (r->occupied) r->flow ^= 1u;
}

int main(void) {
    OriginSwath s = {0};

    /* Absolute origin begins as R1, not empty space. */
    if (!insert_r1(&s) || s.count != 1u || !valid(&s)) {
        fputs("FAIL absolute origin did not initialize as R1\n", stderr);
        return EXIT_FAILURE;
    }

    while (!s.frozen) {
        if (!insert_r1(&s) || !valid(&s)) {
            fputs("FAIL recursive R1 insertion before ceiling\n", stderr);
            return EXIT_FAILURE;
        }
    }

    if (s.count != SATOMICNUMBERMAX || s.insertions != SATOMICNUMBERMAX) {
        fputs("FAIL freeze did not occur exactly at Satomicnumbermax\n", stderr);
        return EXIT_FAILURE;
    }

    /* Snapshot the frozen state before asking for any next R1. */
    OriginSwath frozen = s;

    /* Attempting another insertion must be refused without mutation. */
    if (insert_r1(&s) != 0 || s.count != frozen.count ||
        s.insertions != frozen.insertions || !valid(&s)) {
        fputs("FAIL over-ceiling insertion mutated frozen state\n", stderr);
        return EXIT_FAILURE;
    }

    /* Sentinel proves no hidden 119th member was written. */
    if (s.r[SATOMICNUMBERMAX].occupied != 0u) {
        fputs("FAIL sentinel occupied: hidden over-ceiling Rion\n", stderr);
        return EXIT_FAILURE;
    }

    /* Verify the previously earned local binary transition still preserves count. */
    collide(&s.r[0]);
    if (s.r[0].flow != 1u || s.count != SATOMICNUMBERMAX || !valid(&s)) {
        fputs("FAIL binary collision changed membership/count\n", stderr);
        return EXIT_FAILURE;
    }
    collide(&s.r[0]);
    if (s.r[0].flow != 0u || s.count != SATOMICNUMBERMAX || !valid(&s)) {
        fputs("FAIL binary collision was not reversible\n", stderr);
        return EXIT_FAILURE;
    }

    printf("PASS absolute origin initialized as R1\n");
    printf("PASS recursive insertion conserved one Rion of mass per insertion\n");
    printf("PASS frozen count=%u at Satomicnumbermax=%u\n", s.count, SATOMICNUMBERMAX);
    printf("PASS attempted R%u was refused before state mutation\n", SATOMICNUMBERMAX + 1u);
    printf("PASS frozen snapshot retained count=%u insertions=%u\n", frozen.count, frozen.insertions);
    printf("PASS earned XOR collision remained reversible at frozen ceiling\n");
    printf("UNKNOWN why Satomicnumbermax=%u; ceiling is configured, not derived\n", SATOMICNUMBERMAX);
    printf("UNKNOWN spatial response to same-origin R1 insertion; none was invented\n");
    printf("STOP pre-explosion: no post-freeze transition executed\n");
    return EXIT_SUCCESS;
}
