# Shaelvien Recursive Authority & Supervision System

Status: **FOUNDATIONAL**

This contract defines the shared authority model for Shaelvien user-created sections, assets, cards, sets/decks, realms, identities, studios, classrooms, and protected administrative areas.

## Core rule

**Credentials prove who authenticated. Permissions determine what that authenticated person may do and, when explicitly delegated, whose authority they may exercise.**

Authentication credentials are never shared through this system.

## Permission vocabulary

- `V` / `View` — may view the resource.
- `E` / `Edit` — may view and edit the resource.
- `P` / `Public` — publicly viewable. Public does not imply edit.
- `X` / `Deny` — explicitly denied at that resource.

Each resource has an owner and may contain exact per-user entries plus an optional `*` entry for everyone.

Exact per-user policy is evaluated before the local everyone policy. This allows patterns such as deny-all with named exceptions.

## World / region claim permissions

WorldBuilder and RegionDefiner claims use a request-and-grant authority flow rather than inferring edit rights from merely seeing a map.

Canonical flow:

1. A GM invites a user with a world-scoped link or membership.
2. The authenticated user opens WorldBuilder or RegionDefiner.
3. The user selects a spatial portion of the map.
4. The user submits **Claim**. Selection alone never changes world truth.
5. The owning GM receives a claim request/notification.
6. The GM decides the permission and, where applicable, the exact spatial/resource scope.

The GM-facing claim decisions are:

- **Blocked** — the user cannot submit a claim for that world/resource.
- **Restricted** — claim requests are allowed only for sections the user already has character/resource access to, such as a home or other explicit personal scope.
- **Limited** — claim requests are allowed, but the GM defines the exact cells, Tier, Layers, capabilities, and/or child resources granted.
- **Co-Operative** — the approved resource has multiple owners. Co-owners may manage that shared resource, but protected child resources may stop inheritance or carry explicit local denies so secrets remain secret.
- **Release Ownership** — a transfer operation, not a standing permission. The releasing owner must use a direct authenticated session and type the exact approval statement for the recipient. The releasing owner is then removed from that resource's ownership and the recipient receives that ownership.

`Release Ownership` must never be satisfied by a delegated session, a checkbox alone, or a generic yes/no confirmation. The core authority helper defines the exact approval text as:

`RELEASE OWNERSHIP OF {resourceId} TO {newOwnerUserId}`

Claims preserve the selected World ID, spatial cells, Tier, Layer scope, grid geometry, requester identity, and the GM decision. A GM may narrow a requested area; approval never silently broadens it.

Notifications and cross-account claim persistence are server-authority concerns. Browser state may preview a request, but it must not manufacture an approved grant.

## Recursive containment

Permissions may travel through containment relationships:

`realm -> section -> deck -> card`

If a child has no decisive local policy for the user/action, it inherits through its permission-bearing parent.

Important invariants:

1. **Inherited permission belongs to the containment relationship, not the child.**
2. Removing a card/object from a deck/set immediately removes authority inherited only through that relationship.
3. Explicit policy on the child remains with the child after removal.
4. A child may tighten or replace inherited authority for a named user. Example: parent grants `E`, child explicitly grants that user only `V`; the child is view-only for that user.
5. A child `X` blocks an ancestor grant for that user on that child.
6. A resource may enable `StopsInheritance`, creating a self/local authority boundary.
7. Nested sets may each establish their own boundary.
8. Containment cycles are forbidden.
9. Creating an **inheriting** containment relationship requires permission-management authority over both the parent and child, because inherited containment can change who may access the child. This prevents a container owner from exposing another owner's private asset. A non-inheriting placement may be created with parent authority alone because it cannot grant parent permissions to the child.

### Multiple parents

The same resource may appear in more than one set/deck. When multiple permission-bearing parents exist, authority is **contextual**. The caller must supply the active containment path. If the path is omitted, the evaluator denies rather than guessing which parent granted access.

This preserves the meaning of "this card while it is in this deck".

## Local public policy

`P` is a view grant, not an edit grant. A local public/view policy can make an object visible while an explicitly identified editor may still receive stronger authority through a named local policy or the active containment path.

A local `* = X` denies everyone except users given a more specific exact local entry.

## Delegated identity

A user may explicitly allow another authenticated user to act under their Shaelvien identity.

Example:

- Authenticated actor: `Ryan`
- Effective identity: `Sarah`
- Delegation: `Sarah -> Ryan`

The system always retains both identities.

Delegation requirements:

- explicit grant;
- explicit resource scope;
- explicit capabilities;
- revocable;
- optionally expiring;
- no credential disclosure;
- no implicit re-delegation;
- validated again on every protected access.

Delegation scope is recursive through the active permission-bearing containment path. A delegation scoped to a deck/realm may therefore cover contained resources while they are being accessed through that deck/realm, but the same multi-parent resource is not automatically authorized through a different container.

A delegated action must satisfy **both**:

1. the delegation permits the actor/capability/resource or the resource's active containing scope; and
2. the effective identity itself has authority to the resource.

Delegation therefore cannot manufacture rights the effective identity does not possess.

### Simultaneous sessions

Identity is not a single exclusive session. The owner and one or more authorized delegates may be active simultaneously.

Every audit event records:

- authenticated actor;
- effective identity;
- delegation ID when present;
- target resource/action;
- allow/deny decision and reason.

## Non-delegable account security

Delegated sessions may never perform the following owner-account operations:

- password changes;
- MFA changes;
- recovery changes;
- payment-method management;
- legal-agreement acceptance;
- account deletion;
- root-owner transfer;
- export of private user data.

Those require a direct authenticated owner session.

## Live owner / guardian observation (PIP)

Shaelvien supports a semantic live activity frame for supervised sessions. It is designed to power picture-in-picture or inspector UI without requiring credential sharing or raw remote-desktop access.

A frame can identify:

- operator / authenticated actor;
- effective identity;
- current resource/location;
- current action/tool;
- short activity summary;
- timestamp.

An identity owner may observe a delegate acting as that identity. A linked guardian may observe the juvenile identity under their guardianship. Supervision is visible rather than covert.

## Guardian / juvenile policy

A guardian link may:

- require guardian co-presence;
- approve permitted content descriptors within the platform's existing age/content rules;
- block specific resources or an entire containing scope recursively;
- block interaction with specific users;
- observe the juvenile's semantic activity feed.

Guardian rules are **additive restrictions**. They never weaken the platform content floor.

Effective juvenile access therefore requires:

`recursive authority AND platform/account content allowance AND guardian policy`

A GM may make access stricter for a particular player. A GM cannot use an object permission to bypass the platform/account/guardian content gate.

## Multi-person authorization

Sensitive areas and operations may require M-of-N approval by separately authenticated users.

Rules:

- creation of a sensitive approval request requires a **direct authenticated requester session**;
- every counted approval requires a **direct authenticated approver session**;
- delegated/assumed identities do not count as an independent human approval;
- sensitive requests require at least two approvals;
- eligible approvers are explicit;
- one identity counts once;
- requester approval is excluded by default;
- requests expire;
- approval is bound to one exact operation and target;
- approval is consumed after use;
- every approval is audited.

This supports protections such as two-developer production access or approval of destructive migrations without turning ordinary work into a two-person process. It also prevents an attacker holding one delegated identity from satisfying a two-human gate by switching personas.

## Resolution order

For a resource/user/action, the resolver follows this model:

1. exact local user policy;
2. decisive local everyone policy (`X`, public edit, or public view for view actions);
3. self/local inheritance stop;
4. validated active containment path;
5. a single unambiguous permission-bearing parent;
6. otherwise deny.

For delegated sessions, delegation scope/capability is checked before recursive authority. Guardian/content safety is checked before the authority grant becomes effective.

## Example

Given:

- Deck `1` contains cards `a`, `b`, `d`.
- Deck `1` grants user `h = E`.
- Card `d` gives user `i = X`.
- Card `b` gives users `h = V` and `i = V`.

Then:

- `h` inherits `E` on children with no tighter local policy.
- `h` receives only `V` on `b`, because `b` explicitly tightens `h`.
- `i` is denied on `d` regardless of a possible ancestor grant on that path.
- Removing an otherwise inheriting card from Deck `1` removes Deck `1`'s inherited authority from that card immediately.

## Implementation authority

The first dependency-free evaluator is `RecursiveAuthority.cs`.

`ContentAllowancePolicy.cs` remains the content eligibility authority. The recursive permission service does not replace it; access is conjunctive.

Persistence/UI/API integrations must consume this shared evaluator rather than reimplementing permission precedence independently.

## Security posture

This system is defense-in-depth, not a claim of perfect security. Production deployment should pair it with server-side enforcement, hardware-backed MFA for privileged staff, short-lived sessions, durable append-only audit storage, least privilege, and a tightly controlled emergency recovery process.


## Campaign connected-identity directory

Status: **LOCKED**

Campaign includes a human identity directory presented as **Victims & Co-Conspirators**.

- An authenticated user may generate a one-use connection code and send it to another authenticated user.
- The recipient may redeem that code to create a reciprocal account connection.
- Connection codes are secrets; the server stores only their cryptographic hashes and enforces expiry and one-use redemption.
- Connecting two identities never shares credentials and never delegates identity.
- Connecting two identities never grants World, Region, Local, Instance, card, asset, campaign, claim, or other resource access by itself.
- The connection exists only to make the linked authenticated identity selectable in permission-management interfaces.
- Either connected identity may unlink the relationship. Unlinking removes the directory relationship but does not silently reinterpret historical audit records.
- Resource permission remains explicit, inherited through authorized containment, or public according to the normal Recursive Authority rules.

### Asset permission default

Every asset is permission-bearing.

For a non-owner/non-GM user with no explicit or inherited permission:

**visible state = `Waiting for GM`**

This is the presentation of the absence of a grant. It does **not** imply View.

The explicit permission vocabulary remains:

- `Public`
- `View`
- `Edit`
- `Deny`

`Waiting for GM` is the default pending presentation before an applicable grant exists.

Campaign permission pickers should source authenticated user identities from the connected-identity directory rather than requiring the GM to type raw account/user IDs.
