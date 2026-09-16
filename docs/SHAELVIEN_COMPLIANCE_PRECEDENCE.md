# Shaelvien/RIST Compliance Precedence Memorandum

Status: **FOUNDATIONAL ENGINEERING CONSTRAINT**  
Adopted for the semantic/perception rebuild: 2026-09-16.

This memorandum governs implementation decisions. It is an engineering control, not a substitute for legal advice or jurisdiction-specific legal review.

## Core rule

**Semantic efficiency never outranks lawful human requirements, consent, privacy, safety, accessibility, ownership, or established Shaelvien/RIST policy.**

Rune/Glyph/SHAEP/CCTV mechanisms may represent, transport, verify, or enforce an authorized result. They may not reinterpret a legal or policy restriction into permission.

When a requirement is unknown, ambiguous, conflicting, stale, jurisdiction-dependent, or not yet implemented safely, the protected operation must fail closed or preserve the prior lawful behavior until human review resolves it.

## Precedence

For implementation and deployment decisions, apply the strongest applicable restriction from all relevant sources. The following ordering is a discovery and escalation order, not a claim that every source has the same legal force:

1. Applicable law, regulation, binding order, verified lawful process, and other mandatory legal obligation.
2. Human safety, consent, privacy, accessibility, child/guardian protections, intellectual-property rights, and nondelegable legal/account acts.
3. Published ReLiCGameMaster/RIST terms, privacy, safety, copyright/DMCA, accessibility, and AI-access policies.
4. Foundational Shaelvien/RIST contracts, including Recursive Authority & Supervision, provenance boundaries, SHAEP identity, semantic-language rules, and canon/governance memoranda.
5. Product requirements, feature rules, GameMaster/world rules, and authorized user/developer instructions.
6. Semantic-runtime optimization, compact transport, rendering, caching, bandwidth reduction, and other implementation choices.
7. UI representation and cosmetic behavior.

A lower layer may become stricter. It may not weaken a higher applicable restriction.

## Human and AI authority

- Authentication, identity, role, authority, and capability remain distinct.
- Natural-language instructions do not create authority by themselves.
- Self-asserted human, AI, governmental, administrator, GameMaster, developer, or service identity does not grant access.
- Delegation may not expand the effective identity's authority.
- Unknown or ambiguous authority is denied.
- Legal-agreement acceptance, credential/security changes, private-data export, and other nondelegable operations remain direct-human-owner actions where the authority contract requires that.
- AI access remains subject to the deployed AI policy, provenance rules, human review requirements, and any stronger applicable legal or safety requirement.
- No AI, EI, agent, model, script, plugin, Rune, Glyph, or semantic packet receives an exemption from these constraints because of substrate, embodiment, speed, compression, autonomy, or implementation language.

## Truth and perception

- Server/trusted runtime stores authoritative truth.
- Browser/client produces only authorized perception.
- Pixels, audio, video, DOM, text, layout, and compact opcodes are representations, never authority.
- Hidden facts, credentials, secrets, restricted content, private records, and unauthorized user content must not be sent to a client merely because the presentation layer intends to hide them.
- A semantic packet is a request or authorized perception result, not proof of permission.
- All truth-changing actions require trusted-side authentication, schema/context validation, Recursive Authority resolution, applicable content/safety/guardian checks, and audit where required.

## Privacy and data minimization

- Collect, transmit, expose, and retain only the data needed for the authorized purpose.
- Passwords, credentials, secrets, file contents, private records, and other sensitive values must not be copied into generic semantic feedback or diagnostics.
- User-created material may not be altered, reused, or repurposed outside authorization or another lawful basis.
- Provenance must survive transformation. Human-modified AI-derived material does not silently become purely human-origin material.
- Legal disclosure requires verified lawful process and must be limited to the legally required scope under the deployed AI policy.

## Children and guardians

The current public alpha is not intended for children under 13. Do not weaken that gate or begin collecting personal information from a known under-13 user merely because a semantic or AI feature can technically support it. Any future younger-user path requires the applicable parental-consent/privacy design and must remain conjunctive with the platform content floor and guardian policy.

## Safety and removal obligations

Do not remove or bypass the platform's safety-reporting, copyright/DMCA, or nonconsensual-intimate-image removal mechanisms during a UI/runtime rewrite. Rendering or transport changes must preserve discoverability and operability of those processes.

As of the adoption date, the repository's public safety page includes a TAKE IT DOWN process with a 48-hour target for valid covered requests. Engineering changes must not degrade that workflow.

## Accessibility

No essential action may depend on sight, color, sound, vibration, drag, pointer precision, or one input mechanism alone when an accessible alternative is required by project policy or applicable law. Semantic identity should improve accessibility by allowing equivalent representations and inputs to resolve to the same permitted intent.

A pixel-first/perception-first client therefore still requires semantic labels, state, relationships, keyboard/assistive input paths, captions or textual equivalents where applicable, and meaningful change announcements.

## Change and deployment gate

Before a semantic-runtime migration may replace existing behavior:

1. Preserve or intentionally supersede every applicable published policy and foundational contract.
2. Verify that no client receives hidden authoritative truth solely for convenience.
3. Verify that protected actions still resolve server/trusted-side authority.
4. Verify that consent/privacy/guardian/content restrictions remain conjunctive.
5. Verify that legal/safety/reporting/accessibility surfaces remain available.
6. Keep a reversible compatibility path until the replacement behavior is validated.
7. Record known mismatches instead of silently reconciling them.
8. If applicable law or a binding requirement cannot be confidently determined, stop the affected deployment path and escalate for qualified human/legal review.

## Current external verification notes

These notes are implementation reminders, not an exhaustive legal inventory.

- FTC TAKE IT DOWN Act guidance states that covered platforms must provide a removal process and remove covered nonconsensual intimate depictions and known identical copies within 48 hours of a valid request; Section 3 enforcement began May 19, 2026.
- FTC COPPA guidance continues to require verifiable parental consent for covered collection/use/disclosure of personal information from children under 13, subject to the rule's scope and current amendments/guidance.
- U.S. Copyright Office Section 512 guidance describes conditions for DMCA safe harbors, including designated-agent requirements for service providers relying on the relevant safe harbor.
- U.S. Department of Justice web-accessibility guidance states that ADA obligations can apply to online goods/services of covered public accommodations; project accessibility requirements remain mandatory engineering constraints regardless of the minimum legal floor.

External legal requirements must be rechecked when product scope, jurisdiction, audience, data practices, monetization, advertising, payments, employment/classroom use, or third-party integrations materially change.

## Non-bypass rule

**No optimization may convert DENY into ALLOW. No representation may manufacture authority. No AI may waive a human right or legal obligation. No human instruction may authorize unlawful behavior.**
