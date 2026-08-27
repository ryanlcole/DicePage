# ReLiC Secure Message Gateway Doctrine

Status: LOCKED architecture requirement for ReLiCGameMaster communications.

## Purpose

ReLiC does not use a conventional mailbox model. Internet email is treated as a compatibility transport into the ReLiC identity and communications system. Discord remains the user authentication surface; AWS remains the authority for message state, permissions, encryption, storage, delivery, and audit.

## Identity

- Discord authentication proves the logged-in user's ReLiC identity.
- ReLiC maintains an internal immutable user ID mapped to the Discord identity.
- Friendly `@relicgamemaster.com` aliases map to that internal identity; raw Discord IDs are not exposed as public email addresses.
- AWS, not Discord, is the canonical authority for message ownership, delivery state, permissions, and audit records.

## Inbound security pipeline

Every inbound message must pass through a staged trust pipeline before it is exposed to a receiver:

1. Amazon SES receives the message for `relicgamemaster.com`.
2. Preserve only the minimum transport/security metadata needed to perform immediate verification and a content-free audit outcome.
3. Evaluate the actual authenticated sending infrastructure rather than trusting the visible From header:
   - SPF
   - DKIM
   - DMARC
   - envelope/return-path domain
   - DKIM signing domain
   - sending IP reputation
   - domain reputation and age where reliable data is available
4. Extract link domains and assess them independently against reputable threat-intelligence / phishing / malware sources without automatically opening user-supplied links.
5. Content fact-checking, including sources such as Snopes when relevant, is a separate signal from sender authentication and technical reputation.
6. Attachments are scanned/validated in an isolated ephemeral processing path. They are not retained in a user-accessible quarantine.
7. Remote images, tracking pixels, executable content, scripts, automatic link previews, and automatic remote fetches are disabled by default.
8. Render message text only after sanitization.
9. Messages that pass required security and policy checks may proceed. Messages that fail required checks, contain disallowed dangerous content, or cannot be safely validated are immediately destroyed rather than quarantined.

No single reputation provider or fact-checking site is the sole authority for message safety.

## Fail-closed immediate destruction

- ReLiC has no quarantine mailbox, quarantine review queue, spam folder, administrator recovery queue, or user-accessible holding area for rejected mail.
- If an inbound message fails mandatory sender/security checks, malware/attachment checks, mandatory redaction rules, or any other fail-closed safety gate, its message content is immediately destroyed.
- If a processor cannot confidently determine that the message can proceed safely, the result is destruction, not retention for later review.
- Destruction includes raw MIME/body content, normalized text, attachments, extracted content, transient encrypted payload objects, temporary processing objects, retrieval tokens, and message-specific cryptographic material.
- Ephemeral plaintext or temporary scan artifacts must be removed at the end of processing and must never be written to persistent logs.
- A minimal content-free audit event may record that a message was rejected/destroyed, the processing timestamp, rule/category that caused rejection, and non-content operational identifiers needed for abuse/rate-limit controls. It must not retain enough information to reconstruct the message.
- The system must not forward rejected content to Gmail, Discord, the receiver, administrators, analytics, backups, or any other recovery destination.

## Encryption doctrine

### Inbound

- A received message must be encrypted as early as practical in the ingestion pipeline.
- Persistent accepted-message content must not be stored as plaintext.
- Raw accepted messages, normalized text, attachments, extracted structured content, and sensitive metadata are stored encrypted.
- Use AWS KMS-backed envelope encryption: a unique data-encryption key (DEK) per message or security object, with the DEK protected by KMS.
- Encrypted objects reside in private S3 with public access blocked and least-privilege IAM policies.
- DynamoDB records containing message content or sensitive structured fields must use encryption at rest and should store references/metadata rather than duplicating large plaintext payloads.
- Decryption is permitted only after authenticated authorization verifies the receiver's ReLiC identity and access to that message.
- Plaintext should exist only transiently in the authorized processing/rendering path and must not be written to logs, caches, analytics, browser local storage, or long-lived temporary files.
- Presigned access, if used, must be short-lived and scoped to the authorized object/action.

### Outbound

- ReLiC-authored outgoing message payloads are encrypted before persistent storage and before secure delivery packaging.
- A recipient-facing email may carry an encrypted payload or, preferably, a secure ReLiC retrieval link to the encrypted message.
- A separate decryption code is sent independently from the primary encrypted-message notification.
- The decryption code must be random, single-use where practical, rate-limited, expire after a bounded interval, and never be stored in plaintext after derivation/verification data is established.
- The code and encrypted payload must never appear in the same email/message.
- For recipients who have a ReLiC/Discord identity, the preferred higher-security second channel is an authenticated ReLiC/Discord notification rather than a second message to the same external mailbox.
- When compatibility requires the second code to be delivered by email, it must be sent as a separate message and treated as a weaker fallback because compromise of the same external mailbox can expose both factors.

## Retention and destructive deletion

- ReLiC message storage is transient by design and must not become a general-purpose archival mailbox.
- Every accepted inbound and outbound message has a default 30-day retention period from receipt/send time.
- Reading, replying to, starring, or otherwise interacting with a message does not extend retention.
- Before expiration, a user may deliberately save selected content into a separate authorized ReLiC storage area or export it outside the transient message store.
- Saved/exported copies become independent user-controlled records and are governed by the retention rules of their destination, not the mailbox retention clock.
- At the end of 30 days, any message not explicitly preserved elsewhere is automatically destroyed.
- User-initiated Delete is immediate and destructive: there is no Trash, recycle bin, undo window, administrator restore path, or user-facing recovery mechanism for message content.
- Destruction must remove the encrypted original, normalized text objects, attachments, derived content, retrieval tokens, and the encrypted DEK or equivalent cryptographic material required to decrypt the message.
- Any minimal audit record retained after deletion/expiration must contain no message body, recoverable attachment data, decryption key material, or other content sufficient to reconstruct the message.
- Transient mail storage must not use recovery/versioning settings that would silently make a deleted or expired message recoverable. Durable user storage is a separate subsystem and may use normal backup/versioning controls.

## Receiver UI decomposition

An accepted inbound message is represented as separate controlled objects rather than one executable HTML email:

- Message record / conversation ID
- Sanitized text body
- Extracted links as inert URL records with reputation status
- Attachments as validated/encrypted blobs with IDs, hashes, MIME type, size, and scan state
- Sender/authentication evidence
- Risk/reputation findings
- Immutable reference to the encrypted original message while the message remains within retention

## Privacy-preserving support relay

- Public help/support mail is received at `query@relicgamemaster.com`.
- Messages to this address must pass the same inbound authentication, reputation, sanitization, malware/link analysis, encryption, redaction, and retention controls as all other ReLiC mail.
- Only after a support message is validated as safe may its sanitized text, approved links, and safe attachments be forwarded into the support handling mailbox `relic.gamemaster@gmail.com`.
- ReLiC assigns a unique opaque support ticket code to each accepted support conversation.
- The ticket code is inserted into the forwarded Gmail subject line and is the only routing identifier support staff need to see.
- The external user's actual address or ReLiC identity must not be exposed to the Gmail support mailbox unless a narrowly defined support/security exception explicitly requires it.
- ReLiC retains the private mapping between ticket code and the authoritative originating user/message record inside AWS.
- Replies arriving from `relic.gamemaster@gmail.com` must contain a valid active ticket code. AWS resolves that code to the intended recipient, verifies thread state and authorization, and relays the reply through the ReLiC gateway.
- The Gmail responder does not need to know, store, or type the user's actual email address. The user receives the response as coming from the ReLiC support relay, not directly from the Gmail mailbox.
- Direct reply headers, quoted content, attachment metadata, and forwarding behavior must be sanitized so the private external address is not leaked into the support-side conversation.
- Ticket codes must be unguessable, rate-limited, scoped to a single support thread, and invalidated when the support conversation closes or expires.
- Support relay messages remain subject to the 30-day transient-message policy unless deliberately saved/exported into a separate support record system.

### Mandatory support redaction gate

Before any support text, link annotation, attachment-derived text, quoted reply, filename-derived text, or other content projection is exposed to `relic.gamemaster@gmail.com`, ReLiC must apply a deterministic redaction pass. The encrypted authoritative original remains protected inside AWS only when the message successfully passes the redaction and other mandatory safety gates.

- Any nine-digit numeric sequence must be redacted, including common punctuation/spacing variants that still represent a nine-digit value.
- Numerical words that express or reconstruct a nine-digit numeric value must be redacted as well; normalization must occur before redaction so simple spelling or separator changes do not bypass the rule.
- All dates found in message content, attachment-derived text, quoted content, filenames, or extracted link labels must be redacted except the authoritative message send timestamp and receive timestamp presented as metadata.
- All addresses must be redacted from support-visible content. This includes postal/street addresses and email addresses, plus address-like contact strings when confidently detected.
- The user's originating address, reply-to address, forwarding address, and any address embedded in quoted headers must never be exposed to the Gmail support mailbox.
- Allowed exceptions are limited to ReLiC-generated metadata needed to operate the ticket and official ReLiCGameMaster business contact information.
- ReLiCGameMaster's own approved business email, postal, telephone, domain, and other official contact data may remain visible where operationally necessary.
- Metadata exceptions do not permit copying otherwise-redacted user content into metadata fields. Metadata must be generated from trusted transport/system records rather than scraped from message text.
- Redaction occurs before support forwarding, before searchable indexing of the Gmail-side projection, and again on Gmail replies before any quoted/support-side content is relayed back to the user.
- Redaction failures fail closed by immediate destruction. If the sanitizer cannot confidently produce a safe support projection, ReLiC destroys the message content and cryptographic material; it is not quarantined, retained for manual review, or forwarded.

Intended flow:

External user -> `query@relicgamemaster.com` -> SES/security pipeline -> mandatory validation/redaction gate -> if safe: encrypted ReLiC ticket -> safe projection forwarded to `relic.gamemaster@gmail.com` with ticket code -> Gmail reply containing ticket code -> ReLiC validates/resolves ticket -> reply redaction/sanitization -> relay to originating user without exposing the user's address to Gmail. Any mandatory-gate failure -> immediate destructive deletion.

## Outbound authorization

- The browser may request a reply but never decides whether it is authorized.
- AWS verifies Discord/ReLiC identity, alias ownership, thread permissions, recipient policy, rate limits, and abuse controls before sending.
- SES handles compatible internet email delivery.
- DKIM, SPF, and DMARC are required for `relicgamemaster.com` sending identities before production use.
- Every accepted send creates an audit event linked to the authoritative conversation record.

## Security boundaries

The intended trust chain is:

Internet email -> SES transport screening -> ephemeral isolated validation/scanning -> immediate destruction on failure OR encryption/normalization on acceptance -> ReLiC authority -> authenticated Discord/ReLiC receiver.

Receiving a message must never provide the sender an authentication path into the receiver's ReLiC account.

## Non-negotiable operational controls

- Least-privilege IAM roles.
- KMS key rotation and auditable key policy.
- CloudTrail/CloudWatch auditability without plaintext message logging.
- DynamoDB point-in-time recovery for authoritative non-message state.
- Durable user storage may use S3 versioning/recovery controls; transient message storage must honor destructive deletion and expiration.
- Rate limiting and abuse controls on send, code verification, retrieval, support-ticket resolution, and attachment access.
- Attachment and link processing occurs in isolated ephemeral paths; rejected content is destroyed rather than quarantined.
- No automatic execution of message content.
- No secret, raw encryption key, plaintext decryption code, or decrypted message body is committed to GitHub.

## Architectural note on the second email code

The product requirement allows an encrypted outgoing message plus a second email containing the decryption code. This is implemented as a compatibility mode, not treated as true independent-channel multi-factor delivery. The stronger default for ReLiC members is encrypted delivery plus a decryption code/approval delivered through the authenticated ReLiC/Discord identity channel.
