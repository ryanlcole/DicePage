using RistWorld;

static void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}

static void CheckThrows<T>(Action action, string message) where T : Exception
{
    try
    {
        action();
    }
    catch (T)
    {
        return;
    }

    throw new InvalidOperationException(message);
}

var authority = new RecursiveAuthorityService();

const string owner = "owner";
const string h = "h";
const string i = "i";
const string delegateUser = "delegate";
const string guardian = "guardian";
const string juvenile = "juvenile";

authority.EnsureResource("deck:1", owner);
authority.EnsureResource("deck:2", owner);
authority.EnsureResource("card:a", owner);
authority.EnsureResource("card:b", owner);
authority.EnsureResource("card:c", owner);
authority.EnsureResource("card:d", owner);
authority.EnsureResource("card:public", owner);
authority.EnsureResource("card:safe", owner);
authority.EnsureResource("card:foreign", "other-owner");

authority.SetPermission(owner, "deck:1", h, PermissionGrant.Edit);
authority.SetPermission(owner, "deck:2", h, PermissionGrant.View);
authority.SetPermission(owner, "card:d", i, PermissionGrant.Deny);
authority.SetPermission(owner, "card:b", h, PermissionGrant.View);
authority.SetPermission(owner, "card:b", i, PermissionGrant.View);

authority.Attach(owner, "deck:1", "card:a");
authority.Attach(owner, "deck:1", "card:b");
authority.Attach(owner, "deck:1", "card:c");
authority.Attach(owner, "deck:1", "card:d");

// A container owner must not be able to expose another owner's private child through inherited authority.
CheckThrows<UnauthorizedAccessException>(
    () => authority.Attach(owner, "deck:1", "card:foreign", inheritPermissions: true),
    "Inherited containment must require authority over both parent and child.");
// Non-inheriting placement is allowed because it cannot manufacture access to the foreign child.
authority.Attach(owner, "deck:1", "card:foreign", inheritPermissions: false);
Check(!authority.Resolve("card:foreign", h, AuthorityResourceAction.View, ["deck:1"]).Allowed,
    "Non-inheriting containment must not leak parent permissions into a foreign child.");

var inheritedEdit = authority.Resolve("card:d", h, AuthorityResourceAction.Edit);
Check(inheritedEdit.Allowed && inheritedEdit.EffectivePermission == PermissionGrant.Edit && inheritedEdit.Inherited,
    "Child without local policy must inherit deck edit authority.");

var localTightening = authority.Resolve("card:b", h, AuthorityResourceAction.Edit);
Check(!localTightening.Allowed && localTightening.EffectivePermission == PermissionGrant.View,
    "Local V must tighten inherited E for the same user.");
Check(authority.Resolve("card:b", h, AuthorityResourceAction.View).Allowed,
    "Local V must still allow view.");

var localDeny = authority.Resolve("card:d", i, AuthorityResourceAction.View);
Check(!localDeny.Allowed && localDeny.EffectivePermission == PermissionGrant.Deny,
    "Local X must deny the user on that child.");

Check(authority.Detach(owner, "deck:1", "card:d"), "Detach should remove the containment edge.");
Check(!authority.Resolve("card:d", h, AuthorityResourceAction.Edit).Allowed,
    "Inherited authority must disappear when the child leaves the deck.");

authority.SetStopsInheritance(owner, "card:c", true);
Check(!authority.Resolve("card:c", h, AuthorityResourceAction.View).Allowed,
    "Self/local inheritance stop must block parent inheritance.");

authority.Attach(owner, "deck:2", "card:a");
var ambiguous = authority.Resolve("card:a", h, AuthorityResourceAction.View);
Check(!ambiguous.Allowed && ambiguous.Reason.Contains("explicit containment path", StringComparison.OrdinalIgnoreCase),
    "Multiple parents must deny when containment context is ambiguous.");
var deck1Context = authority.Resolve("card:a", h, AuthorityResourceAction.Edit, ["deck:1"]);
Check(deck1Context.Allowed && deck1Context.EffectivePermission == PermissionGrant.Edit,
    "Explicit deck:1 path must resolve h=E.");
var deck2Context = authority.Resolve("card:a", h, AuthorityResourceAction.Edit, ["deck:2"]);
Check(!deck2Context.Allowed && deck2Context.EffectivePermission == PermissionGrant.View,
    "Explicit deck:2 path must resolve h=V and deny edit.");

authority.SetPermission(owner, "card:public", RecursiveAuthorityService.EveryonePrincipal, PermissionGrant.Public);
Check(authority.Resolve("card:public", "stranger", AuthorityResourceAction.View).Allowed,
    "P must grant public view.");
Check(!authority.Resolve("card:public", "stranger", AuthorityResourceAction.Edit).Allowed,
    "P must never imply edit.");

// Delegation: operator can act as h only inside the grant and can never exceed h's own authority.
var delegation = authority.CreateDelegation(
    h,
    delegateUser,
    ["*"],
    DelegatedCapability.AssumeIdentity | DelegatedCapability.View | DelegatedCapability.Edit,
    DateTimeOffset.UtcNow.AddHours(1),
    grantId: "grant:h-to-delegate");

var directH = authority.StartSession(h, h, sessionId: "session:h");
var delegatedH = authority.StartSession(delegateUser, h, delegation.GrantId, "session:delegate-as-h");
Check(authority.Sessions.Count >= 2, "Owner and delegate must be allowed to remain active simultaneously.");
Check(authority.EvaluateSessionAccess(delegatedH.SessionId, "deck:1", AuthorityResourceAction.Edit).Allowed,
    "Delegate should exercise h's E authority on deck:1.");
Check(!authority.EvaluateSessionAccess(delegatedH.SessionId, "card:b", AuthorityResourceAction.Edit).Allowed,
    "Delegation must not bypass h's tighter local V on card:b.");
Check(authority.CanPerformAccountAction(directH.SessionId, AccountSensitiveAction.ChangeMfa),
    "Direct owner session should be eligible for sensitive account actions.");
Check(!authority.CanPerformAccountAction(delegatedH.SessionId, AccountSensitiveAction.ChangeMfa),
    "Delegated session must not perform sensitive account actions.");

// Delegation scoped to a container must recurse only through the active containment path.
var scopedDelegation = authority.CreateDelegation(
    h,
    "delegate:scoped",
    ["deck:1"],
    DelegatedCapability.AssumeIdentity | DelegatedCapability.View,
    DateTimeOffset.UtcNow.AddHours(1),
    grantId: "grant:h-deck1-only");
var scopedSession = authority.StartSession("delegate:scoped", h, scopedDelegation.GrantId, "session:delegate-scoped");
Check(authority.EvaluateSessionAccess(scopedSession.SessionId, "card:b", AuthorityResourceAction.View, ["deck:1"]).Allowed,
    "Deck-scoped delegation must recurse to a contained card on the explicit deck path.");
Check(!authority.EvaluateSessionAccess(scopedSession.SessionId, "card:a", AuthorityResourceAction.View, ["deck:2"]).Allowed,
    "Deck:1 delegation must not authorize the same multi-parent card through deck:2.");

authority.PublishActivity(delegatedH.SessionId, "deck:1", "edit", "Editing deck metadata");
var ownerPip = authority.GetObservableActivity(h, delegatedH.SessionId);
Check(ownerPip is not null && ownerPip.ActorUserId == delegateUser && ownerPip.EffectiveUserId == h,
    "Owner PIP must identify both operator and effective identity.");

authority.RevokeDelegation(h, delegation.GrantId);
Check(!authority.EvaluateSessionAccess(delegatedH.SessionId, "deck:1", AuthorityResourceAction.View).Allowed,
    "Revocation must immediately invalidate an already-open delegated session.");

// Guardian co-presence and platform content gating.
authority.SetPermission(owner, "card:safe", juvenile, PermissionGrant.View);
authority.Attach(owner, "deck:1", "card:safe");
var guardianLink = authority.SetGuardianLink(
    guardian,
    juvenile,
    requireGuardianPresence: true,
    approvedContentDescriptors: ["violence-gore"]);
var juvenileSession = authority.StartSession(juvenile, juvenile, sessionId: "session:juvenile");

Check(!authority.EvaluateSessionAccess(juvenileSession.SessionId, "card:safe", AuthorityResourceAction.View, ["deck:1"]).Allowed,
    "Required guardian co-presence must block the juvenile when guardian is absent.");
_ = authority.StartSession(guardian, guardian, sessionId: "session:guardian");
Check(authority.EvaluateSessionAccess(juvenileSession.SessionId, "card:safe", AuthorityResourceAction.View, ["deck:1"]).Allowed,
    "Juvenile access should resume when the required guardian is directly present.");

var allowedMinorContent = new ContentAccessContext(
    ContentAllowancePolicy.Minor,
    ["violence-gore"],
    ["violence-gore"]);
Check(authority.EvaluateSessionAccess(
        juvenileSession.SessionId,
        "card:safe",
        AuthorityResourceAction.View,
        ["deck:1"],
        allowedMinorContent).Allowed,
    "Guardian-approved descriptor within the platform's minor allowance should pass.");

var disallowedMinorContent = new ContentAccessContext(
    ContentAllowancePolicy.Minor,
    ["explicit-sexual-content"],
    ["explicit-sexual-content"]);
Check(!authority.EvaluateSessionAccess(
        juvenileSession.SessionId,
        "card:safe",
        AuthorityResourceAction.View,
        ["deck:1"],
        disallowedMinorContent).Allowed,
    "Guardian permissions must not weaken the platform content floor.");

authority.PublishActivity(juvenileSession.SessionId, "card:safe", "view", "Viewing supervised content");
Check(authority.GetObservableActivity(guardian, juvenileSession.SessionId) is not null,
    "Linked guardian must be able to observe the juvenile semantic activity frame.");

// Guardian blocking is recursive: blocking a deck blocks a contained card even when the card itself grants V.
guardianLink.BlockedResourceIds.Add("deck:1");
Check(!authority.EvaluateSessionAccess(juvenileSession.SessionId, "card:safe", AuthorityResourceAction.View, ["deck:1"]).Allowed,
    "Guardian container block must override an otherwise valid child permission.");

// Sensitive operations require separately authenticated direct sessions, distinct approvers, scope, expiry, and one-time use.
var requesterSession = authority.StartSession("developer-requester", "developer-requester", sessionId: "session:developer-requester");
var devASession = authority.StartSession("dev:a", "dev:a", sessionId: "session:dev-a");
var devBSession = authority.StartSession("dev:b", "dev:b", sessionId: "session:dev-b");

var approval = authority.CreateApprovalRequest(
    requesterSessionId: requesterSession.SessionId,
    operationKey: "production-migration",
    targetResourceId: "system:production",
    requiredApprovals: 2,
    eligibleApprovers: ["dev:a", "dev:b", "dev:c"],
    lifetime: TimeSpan.FromMinutes(10),
    requestId: "approval:production-migration");

// A delegated session acting as dev:a is intentionally not accepted as a second-human approval.
var devADelegation = authority.CreateDelegation(
    "dev:a",
    "approval-helper",
    ["system:production"],
    DelegatedCapability.AssumeIdentity | DelegatedCapability.Approve,
    DateTimeOffset.UtcNow.AddMinutes(10),
    grantId: "grant:dev-a-approval-helper");
var delegatedApprover = authority.StartSession("approval-helper", "dev:a", devADelegation.GrantId, "session:approval-helper-as-dev-a");
Check(!authority.Approve(approval.RequestId, delegatedApprover.SessionId),
    "Delegated identity must not count as a separately authenticated sensitive-operation approver.");
Check(!authority.Approve(approval.RequestId, "dev:a"),
    "Supplying a user ID instead of an authenticated session ID must not approve anything.");
Check(authority.Approve(approval.RequestId, devASession.SessionId), "First direct eligible approval should count.");
Check(!authority.Approve(approval.RequestId, devASession.SessionId), "One identity must not count twice.");
Check(authority.Approve(approval.RequestId, devBSession.SessionId), "Second distinct direct eligible approval should count.");
Check(approval.IsSatisfied(DateTimeOffset.UtcNow), "2-of-3 direct-session approval should now be satisfied.");
Check(authority.ConsumeApproval(approval.RequestId, "production-migration", "system:production"),
    "Satisfied approval should be consumable only for the exact operation and target.");
Check(!authority.ConsumeApproval(approval.RequestId, "production-migration", "system:production"),
    "Consumed approval must not be reusable.");

Check(authority.AuditTrail.Count > 0, "Authority decisions and mutations must produce audit events.");

Console.WriteLine("Recursive Authority contract tests: PASS");
