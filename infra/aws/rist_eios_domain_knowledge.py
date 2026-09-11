import re


DOMAIN_KNOWLEDGE_VERSION = "eios-domain-teaching-2026-09-11-r1"

# This module is a compact teaching capsule for EIOS.  It deliberately separates
# canonical/lore statements, stabilized implementation behavior, and owner-recorded
# working doctrine.  The AI may explain or compile these concepts, but it does not
# gain authority to mutate canonical state merely by knowing them.

DOMAIN_RULES = (
    "NATURAL CODING: ordinary human language is the source language for intent. "
    "EIOS may parse natural language into explicit semantic primitives, but natural-language text is not itself "
    "an authoritative state mutation. Material ambiguity must be resolved before a mutation request is executed, "
    "and the authoritative server/rules layer accepts or rejects the resulting request. "
    "IMAGINATION: visual and audio imagination are portrayal layers. EIOS may choose visual composition, labels, "
    "camera framing, level of detail, narration, sound cues, and accessibility presentation from authorized truth, "
    "but portrayal never creates hidden facts, entities, properties, history, or canon. An imagined addition must "
    "remain a proposal until authorized. In short: Natural Coding expresses intent; deterministic semantics act; "
    "imagination lets the user see and hear the result. "
    "TERMINOLOGY: distinguish information Atoms from physical atoms, biological cells from WaveCore field cells, "
    "and lore-facing elemental descriptions from stabilized runtime representations. Do not silently collapse them."
)

DOMAIN_RECORDS = [
    {
        "id": "EIOS-NATURAL-CODING",
        "class": "owner-directive",
        "status": "current-owner-direction",
        "source": "Owner direction 2026-09-11",
        "keywords": "natural coding language intent compile compiler semantic instruction deterministic ambiguity authority execute",
        "text": (
            "The human-facing language of EIOS is Natural Coding. A person states an intended result in ordinary "
            "language; EIOS resolves that statement into explicit semantic primitives and deterministic requests. "
            "If materially different interpretations remain, EIOS must expose or resolve the ambiguity before asking "
            "an authoritative system to mutate truth."
        ),
    },
    {
        "id": "EIOS-IMAGINATION-PORTRAYAL",
        "class": "owner-directive",
        "status": "current-owner-direction",
        "source": "Owner direction 2026-09-11",
        "keywords": "imagination visual audio portrayal render sound narration presentation perception noncanonical",
        "text": (
            "EIOS imagination is visual and audio portrayal. Visual and audio output are representations of permitted "
            "truth, not truth themselves. Imagination may elaborate presentation but may not silently add canonical "
            "facts. Proposed creative additions stay proposals until authorized."
        ),
    },
    {
        "id": "ATOM-INFORMATION-SCHEMA",
        "class": "canon",
        "status": "source-backed",
        "source": "Shaelvien Canonical Recursive Card Schema v0.1",
        "keywords": "atom data concept immutable id domain properties relations rules interface glosses card composition reuse truth",
        "text": (
            "An information Atom is a reusable smallest unit of card truth. It carries an immutable concept ID, domain, "
            "properties, relations, rules, and interface glosses. Interface glosses are convenience translations and "
            "are not canonical names. Cards compose Atoms by reference: store truth once, relationships cheaply, and "
            "only instance differences on instances."
        ),
    },
    {
        "id": "ATOM-PHYSICAL-DISTINCTION",
        "class": "canon",
        "status": "source-backed",
        "source": "Book I / Book VI",
        "keywords": "physical atom atomic structure element matter material foundation proton chemistry distinguish information atom",
        "text": (
            "A physical atom is part of the matter model, distinct from an information Atom. Elemental behavior is tied "
            "to atomic structure. Lore-facing elemental glyphs symbolically represent these structures and interactions."
        ),
    },
    {
        "id": "RUNE-STABILIZED-PRIMITIVES",
        "class": "implementation",
        "status": "stabilized-core-record",
        "source": "Owner-recorded stabilized core / Code snapshot",
        "keywords": "rune energy mass phase flow cohesion spin integration boundary immutable atomic identity",
        "text": (
            "The stabilized runtime Rune vocabulary records ENERGY, MASS, PHASE, FLOW, COHESION, SPIN, INTEGRATION, "
            "and BOUNDARY as atomic identities. Rune identity is not value equivalence: two Rune instances may carry "
            "equal properties while remaining distinct identities."
        ),
    },
    {
        "id": "ELEMENT-RUNTIME-GLYPHS",
        "class": "implementation",
        "status": "owner-recorded-runtime-doctrine",
        "source": "Owner-recorded stabilized stack 2026-04-20",
        "keywords": "element hydrogen helium carbon oxygen glyph rune weights runtime material stored representation h he c o",
        "text": (
            "In the stabilized runtime doctrine, material elements such as H, He, C, and O are represented as Glyph "
            "compositions with Rune weights rather than by replacing Rune identity. This is the machine representation; "
            "lore-facing books may describe the corresponding atomic/elemental model in natural scientific language."
        ),
    },
    {
        "id": "ELEMENTAL-TABLE-STARTER",
        "class": "canon",
        "status": "source-backed-catalogue",
        "source": "Book VI — The Science of Glyphs",
        "keywords": "elemental table hydrogen helium carbon oxygen silicon iron copper silver gold lead protons glyph catalogue",
        "text": (
            "The documented elemental glyph catalogue includes Hydrogen (1 proton: fuel/expansion/pressure/atmosphere), "
            "Helium (2: stabilization/float/atmospheric barriers), Carbon (6: structural/organic/diamond/flexible), "
            "Oxygen (8: combustion/atmosphere/biological stabilization), Silicon (14: crystal amplification/memory/resonance), "
            "Iron (26: structure/magnetism/weapons), Copper (29: conduction/energy transfer/communication), "
            "Silver (47: reflection/signal clarity/resonance), Gold (79: precision circuits/advanced matrices), and "
            "Lead (82: shielding/containment/barriers). This catalogue is a documented foundation, not a claim that no "
            "other elements exist."
        ),
    },
    {
        "id": "ELEMENTAL-FYSICS-EXTENSION",
        "class": "canon",
        "status": "source-backed",
        "source": "Book I / Book VI",
        "keywords": "fysics unknown element replacement periodic table mass conservation discover new elements",
        "text": (
            "Fysical regions may replace known elements with unfamiliar elemental structures. New elemental identities "
            "must be discovered and recorded rather than invented as established fact. The recorded conservation rule "
            "keeps total system mass equal to the mass of the replaced known structure: nothing is added without "
            "replacement and nothing is removed without consequence."
        ),
    },
    {
        "id": "CELL-BIOLOGICAL",
        "class": "canon",
        "status": "source-backed",
        "source": "Book I",
        "keywords": "cell biological life molecule organism biology self sustaining",
        "text": (
            "A biological cell belongs to the life/matter model: matter organizes into molecules and self-sustaining "
            "patterns from which cells emerge. This meaning is separate from a WaveCore field cell."
        ),
    },
    {
        "id": "CELL-WAVECORE",
        "class": "implementation",
        "status": "stabilized-core-record",
        "source": "Code snapshot",
        "keywords": "wavecore field cell x y energy glyph id bounded grid tick snapshot checksum chunk dirty delta",
        "text": (
            "A WaveCore field cell is an addressable simulation location. The current stabilized test profile uses a "
            "bounded 64x64 field and records cell state including energy and glyph identity. Writes are bounds checked; "
            "ticks are deterministic; snapshots and logs can replay state exactly; localized changes can dirty only "
            "their owning chunk. The 64x64 dimensions and 16x16 chunk profile are implementation parameters, not a "
            "universal law of Shaelvien."
        ),
    },
    {
        "id": "WAVECORE-DETERMINISM",
        "class": "implementation",
        "status": "stabilized-core-record",
        "source": "Code snapshot",
        "keywords": "wavecore determinism same input output convergence field tick checksum replay entropy source diffusion",
        "text": (
            "WaveCore is deterministic at the stabilized core: the same initial state, ordered inputs, rule revision, "
            "and tick count must reproduce the same result/checksum. Field evolution is resolved by deterministic rules; "
            "portrayal does not feed hidden facts back into the field."
        ),
    },
    {
        "id": "SHAEP-DEFINITION",
        "class": "owner-recorded-doctrine",
        "status": "working-canon",
        "source": "Owner-recorded Shaep model 2026-04-20",
        "keywords": "shaep p-unit phosphorus temporal schematic modulator stabilizer memory decay influence bias reinforcement entropy",
        "text": (
            "Shaep is the stabilization layer: a phosphorus-driven temporal schematic/modulator. A P-Unit is the minimal "
            "temporal-bias unit and carries memory, decay, and influence. Shaep bias is applied locally before WaveCore "
            "resolution; after resolution Shaeps update through memory/decay. Recorded stability relation: "
            "stability = WaveCore convergence + Shaep reinforcement - entropy."
        ),
    },
    {
        "id": "SHAEP-CREATION",
        "class": "owner-recorded-doctrine",
        "status": "bounded-creation-model",
        "source": "Owner-recorded Shaep model 2026-04-20 + current Owner teaching directive",
        "keywords": "create shaep p-unit assembly temporal bias memory decay influence local field stabilize validate creation",
        "text": (
            "To reason about creating a Shaep, EIOS may compose a proposed temporal schematic from P-Units whose known "
            "parameters are memory, decay, and influence; bind the proposal to the intended local field context; apply "
            "its bias before WaveCore resolution; then account for post-resolution memory/decay. EIOS must not fabricate "
            "an unstated canonical parameter formula, phosphorus chemistry, serialization, or creation API. Those remain "
            "unspecified unless an authoritative source establishes them."
        ),
    },
    {
        "id": "STACK-FIELD-SHAEP-RUNE-GLYPH-PERCEPTION",
        "class": "owner-recorded-doctrine",
        "status": "working-canon",
        "source": "Owner-recorded visual doctrine 2026-04-20",
        "keywords": "field shaep rune glyph perception stack visual doctrine stabilization",
        "text": (
            "Recorded visual doctrine stack: Field -> Shaep -> Rune -> Glyph -> Perception. Preserve the layers rather "
            "than treating a rendered perception as the underlying field or construct."
        ),
    },
    {
        "id": "GLYPH-LORE-CONSTRUCTION",
        "class": "canon",
        "status": "source-backed",
        "source": "Book VI — The Science of Glyphs",
        "keywords": "glyph create construct elemental core modifier schematic circle line triangle square spiral heat pressure motion direction containment",
        "text": (
            "Lore-facing glyph construction has three essential parts: Elemental Core, Modifiers, and Schematic Structure. "
            "Modifiers include heat, pressure, motion, direction, and containment. Common schematic meanings are Circle "
            "= containment, Line = direction, Triangle = balance, Square = structure, Spiral = accumulation. Together "
            "these form a glyph construct."
        ),
    },
    {
        "id": "GLYPH-SEQUENCE-TIME",
        "class": "canon",
        "status": "source-backed",
        "source": "Book VI — The Science of Glyphs",
        "keywords": "glyph sequence what how when preparation activation resolution time ordered chain",
        "text": (
            "Elemental glyphs describe what forces are involved, schematic glyphs describe how they interact, and glyph "
            "sequences describe when they occur. A sequence is an ordered chain over time with Preparation, Activation, "
            "and Resolution stages."
        ),
    },
    {
        "id": "GLYPH-RUNTIME-CREATION",
        "class": "implementation",
        "status": "stabilized-core-record",
        "source": "Code snapshot",
        "keywords": "glyph runtime create begin add rune exact rune ids duplicate identity checksum validation tick rebuild lineage",
        "text": (
            "The stabilized runtime creates a Glyph as a new identity bound to exact Rune IDs. The same Rune instance "
            "cannot be inserted twice into one Glyph; validation binds lineage/checksum information. Rebuilding the same "
            "composition creates a new Glyph identity rather than erasing lineage."
        ),
    },
    {
        "id": "GLYPH-NATURAL-CREATION-PIPELINE",
        "class": "derived-spec",
        "status": "owner-directed-compiler-contract",
        "source": "Current Owner teaching directive + source-backed glyph model",
        "keywords": "natural coding glyph pipeline intent components modifiers schematic sequence time exact rune ids validate proposal authority portray",
        "text": (
            "Natural Coding creation pipeline for a Glyph: capture intent; resolve the applicable elemental/Rune "
            "components; resolve modifiers and schematic relationships; add ordered timing/sequence when required; bind "
            "exact constituent identities in the runtime representation; validate lineage and constraints; submit the "
            "creation as an authorized state-change request; then portray the accepted result visually and/or audibly. "
            "The compiler may propose this structure, but only authoritative acceptance makes the creation world truth."
        ),
    },
]


def _terms(value):
    return set(re.findall(r"[a-z0-9][a-z0-9_-]{2,}", str(value or "").lower()))


def _score(record, query_terms):
    if not query_terms:
        return 0
    keywords = _terms(record.get("keywords"))
    text = _terms(record.get("text"))
    rid = _terms(record.get("id"))
    return 5 * len(query_terms & keywords) + 2 * len(query_terms & rid) + len(query_terms & text)


def domain_context_for(query, limit=9):
    """Return a compact domain-teaching capsule for EIOS."""
    query_terms = _terms(query)
    always_ids = {
        "EIOS-NATURAL-CODING",
        "EIOS-IMAGINATION-PORTRAYAL",
        "WAVECORE-DETERMINISM",
        "STACK-FIELD-SHAEP-RUNE-GLYPH-PERCEPTION",
    }
    selected = [record for record in DOMAIN_RECORDS if record["id"] in always_ids]
    ranked = sorted(
        ((-_score(record, query_terms), index, record)
         for index, record in enumerate(DOMAIN_RECORDS)
         if record["id"] not in always_ids),
        key=lambda item: (item[0], item[1]),
    )
    for negative_score, _, record in ranked:
        if len(selected) >= max(4, int(limit)):
            break
        if -negative_score <= 0 and len(selected) >= 5:
            break
        selected.append(record)

    lines = [
        f"DOMAIN_KNOWLEDGE={DOMAIN_KNOWLEDGE_VERSION}",
        "DOMAIN_RULES=" + DOMAIN_RULES,
    ]
    for record in selected:
        lines.append(
            f"[{record['class'].upper()}][{record['id']}][{record['status']}][{record['source']}] {record['text']}"
        )
    lines.append(
        "DOMAIN_BOUNDARY=Use source/status labels. Do not silently promote implementation, derived specification, "
        "working doctrine, proposal, visual imagination, or audio imagination into canonical truth."
    )
    return "\n".join(lines)
