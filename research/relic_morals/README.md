# ReLiC Moral Learning

ReLiC may study authorized private conversations for recurring moral principles, but it must preserve a strict boundary between **learning from a person** and **declaring universal morality**.

## Pipeline

`Private chat -> authorized observation -> candidate statement -> source digest -> deduplicate -> contradiction check -> CANDIDATE -> human review -> optional PROJECT_CANON`

Raw chat text is not committed to the public repository. By default the durable moral layer keeps only:

- a normalized candidate moral;
- one-way source digests;
- support classification;
- provenance;
- contradiction evidence;
- scope and status;
- explicit human confirmation state.

## Non-negotiable rules

1. A repeated statement is evidence of a recurring project value, not proof of universal moral truth.
2. AI extraction cannot promote its own candidate to canon.
3. Sensitive personal traits must not be inferred as part of moral learning.
4. Contradictory chat evidence is preserved rather than discarded.
5. Casual remarks, jokes, fiction, roleplay, brainstorms, and hypotheticals must not silently become morals.
6. Promotion requires explicit human confirmation and is limited to the project scope handled by this layer.
7. Raw private chats stay private unless their owner explicitly authorizes publication.
8. A later correction can supersede a prior candidate, but the earlier evidence remains traceable.

## Seed

`candidate_morals.json` contains generalized, de-identified candidates found in the available conversation history. It intentionally contains no private chat excerpts.

The seed is useful as a starting hypothesis set. It is not a substitute for future evidence review.
