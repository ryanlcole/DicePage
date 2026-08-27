# ReLiC Secure Message Gateway Doctrine

Status: LOCKED architecture requirement for ReLiCGameMaster communications.

## Purpose

ReLiC does not use a conventional mailbox model. Internet email is treated as a compatibility transport into the ReLiC identity and communications system. Discord remains the user authentication surface; AWS remains the authority for message state, permissions, encryption, storage, delivery, retention, and audit.

## Identity

- Discord authentication proves the logged-in user's ReLiC identity.
- ReLiC maintains an internal immutable user ID mapped to the Discord identity.
- Friendly `@relicgamemaster.com` aliases map to that internal identity; raw Discord IDs are not exposed as public email addresses.
- AWS, not Discord, is the canonical authority for message ownership, delivery state, permissions, and audit records.

## Inbound security pipeline

Every inbound message must pass through a staged trust pipeline before it is exposed to a receiver:

1. Amazon SES receives the message for `relicgamemaster.com`.
2. Preserve the original transport/security metadata needed for audit and verification.
3. Evaluate the actual authenticated sending infrastructure rather than trusting the visible From header:
   - SPF
   - DKIM
   - DMARC
   - envelope/return-path domain
   - DKIM signing domain
   - sending IP reputation
   - domain reputation and age where reliable data is available
4. Extract link domains and assess them independently against reputable threat-intelligence / phishing / malware sources.
5. Content fact-checking, including sources such as Snopes when relevant, is a separate signal from sender authentication and technical reputation.
6. Attachments enter quarantine first and are identified by generated immutable IDs and cryptographic hashes.
7. Remote images, tracking pixels, executable content, scripts, automatic link previews, and automatic remote fetches are disabled by default.
8. Render message text only after sanitization.
9. Classify messages as trusted, suspicious/quarantined, or blocked based on multiple independent signals. Sender identity confidence and content confidence are separate scores.

No single reputation provider or fact-checking site is the sole authority for message safety.

## Encryption doctrine

### Inbound

- A received message must be encrypted as early as practical in the ingestion pipeline.
- Persistent message content must not be stored as plaintext.
- Raw messages, normalized text, attachments, extracted structured content, and sensitive metadata are stored encrypted.
- Use AWS KMS-backed envelope encryption: a unique data-encryption key (DEK) per message or security object, with the DEK protected by KMS.
- Encrypted objects reside in private S3 with public access blocked and least-privilege IAM policies.
- The transient mailbox/quarantine storage path must be designed for destructive deletion rather than archival recovery; it must not retain recoverable object versions after user deletion or expiration.
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

ReLiC messaging is intentionally not a permanent mailbox service.

- Every received or sent message has a default retention period of 30 days from receipt/send time.
- The 30-day limit applies to the encrypted original, normalized text, attachments, extracted links, message payloads, and receiver-facing message state stored in the communications gateway.
- DynamoDB message records use expiration/TTL metadata aligned to the 30-day policy, with cleanup workers responsible for deleting associated S3 objects and encryption material.
- S3 lifecycle controls provide a second enforcement layer for expired transient message objects.
- Before expiration, a user may explicitly preserve information by:
  - saving selected content into a separate authorized ReLiC user-storage area that is not governed by mailbox retention, or
  - exporting/downloading it to storage controlled by the user.
- Saving or exporting must be an explicit user action. Merely opening, replying to, starring, or viewing a message does not extend its retention.
- The normal communications UI should show the remaining retention time and warn users before expiration when practical.
- Expired messages are automatically destroyed rather than archived.
- When a user selects Delete, deletion is immediate and destructive for message content. There is no Trash folder, undo window, restore button, or administrator-facing message-content recovery mechanism.
- Destructive deletion must remove the message content objects, attachment objects, encrypted original, derived message payloads, and the stored encrypted DEK/material needed to decrypt those objects. This provides crypto-shredding in addition to object deletion.
- The transient communications storage path must not preserve noncurrent S3 versions or snapshots that would allow deleted message content to be restored later.
- Minimal non-content security/audit records may survive deletion when required for abuse prevention, rate limiting, security investigation, billing, or legal compliance, but those records must not contain recoverable message bodies, attachments, links-as-content, raw email, plaintext keys, or encrypted keys sufficient to recover deleted content.
- The retention policy exists specifically to discourage ReLiC from becoming a primary archival email provider and to reduce the security, abuse, privacy, and storage consequences of indefinite mailbox accumulation.

## Receiver UI decomposition

An inbound message is represented as separate controlled objects rather than one executable HTML email:

- Message record / conversation ID
- Sanitized text body
- Extracted links as inert URL records with reputation status
- Attachments as quarantined/encrypted blobs with IDs, hashes, MIME type, size, and scan state
- Sender/authentication evidence
- Risk/reputation findings
- Immutable reference to the encrypted original message while it remains inside the retention window
- Retention expiration timestamp

## Outbound authorization

- The browser may request a reply but never decides whether it is authorized.
- AWS verifies Discord/ReLiC identity, alias ownership, thread permissions, recipient policy, rate limits, and abuse controls before sending.
- SES handles compatible internet email delivery.
- DKIM, SPF, and DMARC are required for `relicgamemaster.com` sending identities before production use.
- Every send creates an audit event linked to the authoritative conversation record.

## Security boundaries

The intended trust chain is:

Internet email -> SES transport screening -> encrypted quarantine -> parsing/scanning/reputation -> ReLiC authority -> authenticated Discord/ReLiC receiver.

Receiving a message must never provide the sender an authentication path into the receiver's ReLiC account.

## Non-negotiable operational controls

- Least-privilege IAM roles.
- KMS key rotation and auditable key policy.
- CloudTrail/CloudWatch auditability without plaintext message logging.
- DynamoDB point-in-time recovery for authoritative non-message state; message-content retention must still obey the destructive deletion doctrine.
- S3 recovery/versioning controls are permitted for durable user storage, but transient gateway message storage must not defeat destructive deletion or 30-day expiration.
- Rate limiting and abuse controls on send, code verification, retrieval, and attachment access.
- Attachment and link processing occurs in isolated/quarantined paths.
- No automatic execution of message content.
- No secret, raw encryption key, plaintext decryption code, or decrypted message body is committed to GitHub.

## Architectural note on the second email code

The product requirement allows an encrypted outgoing message plus a second email containing the decryption code. This is implemented as a compatibility mode, not treated as true independent-channel multi-factor delivery. The stronger default for ReLiC members is encrypted delivery plus a decryption code/approval delivered through the authenticated ReLiC/Discord identity channel.
