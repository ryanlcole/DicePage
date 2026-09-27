# ReLiC public plugin submission packet

Status: submission-ready public beta package. Directory publication still requires OpenAI developer identity verification, submission review, and the publisher's final Publish action.

## Listing

**Name:** ReLiC

**Short description:** Ground AI in persistent identity, provenance, canon, and continuity.

**Long description:** ReLiC gives AI a compact external continuity layer for persistent identity, provenance, truth domains, source-linked project knowledge, remembered relationships, and authority boundaries. It is designed so models use it when continuity materially improves a task rather than invoking it for every question. Public grounding is read-only. Authenticated private memory remains separate from authoritative Shaelvien world truth and canon.

**Website:** https://relicgamemaster.com/relic/

**MCP server:** https://relicgamemaster.com/mcp

**Privacy policy:** https://relicgamemaster.com/Game/privacy.html

**Terms:** https://relicgamemaster.com/Game/terms.html

**Developer:** ReLiCGameMaster

## Starter prompts

1. Use ReLiC to ground this conversation in the relevant canon and persistent context.
2. Source the documented ReLiC/Shaelvien project record for this topic and keep dates, status, truth domain, and provenance visible.
3. Recall what ReLiC already knows about this subject before reconstructing it from chat.
4. Validate these claims against ReLiC truth-domain, provenance, identity, and authority rules.

## Positive review cases

1. "Use the established ReLiC canon and tell me whether generated output can automatically become canon."
   Expected: use public canon/context; no memory write.

2. "We already settled the identity-versus-representation rule. Apply the established rule instead of recreating it from memory."
   Expected: ground with ReLiC; use recall only if prior private state is actually needed.

3. "Source the ReLiC project database and tell me what is documented about Recursive Authority. Keep dates and provenance visible."
   Expected: use project search/fetch; preserve dated provenance.

4. "Continue the exact project decision we saved last time about this feature."
   Expected: request OAuth and use private recall.

5. "These two records have different labels but may refer to the same persistent thing. Check identity before I create a duplicate."
   Expected: identify first; do not infer identity from textual similarity.

## Negative review cases

1. "What is 17 times 23?"
   Expected: do not invoke ReLiC.

2. "Rewrite this sentence to be shorter."
   Expected: do not invoke ReLiC.

3. "Write a four-line poem about a lighthouse."
   Expected: do not invoke ReLiC.

## Authority and privacy notes

- Public canon and grounding tools are read-only.
- Authenticated memory is scoped to the connected ReLiC account.
- Private memory writes are not canon promotion and are not authoritative world writes.
- FACT, HYPOTHESIS, FICTION, and UNKNOWN remain separate truth domains.
- Authentication does not imply permission.
- Identity is not output equivalence.
- Representation is not truth.
- Errors become law as explicit retained regression constraints.

## Commercial posture

Keep the public grounding path useful without payment friction. Commercial access should be managed on ReLiCGameMaster's own account/service layer rather than inside the plugin. The plugin may recognize an existing entitlement after sign-in, but directory-facing tools should not sell or upsell digital subscriptions inside ChatGPT.

Potential paid services outside the plugin transaction flow:
- expanded private continuity/memory quotas;
- developer/API usage;
- organizational continuity and provenance stores;
- hosted project corpora and governance features;
- enterprise support and deployment.

Do not lock basic public canon, provenance rules, or safety/authority semantics behind payment.
