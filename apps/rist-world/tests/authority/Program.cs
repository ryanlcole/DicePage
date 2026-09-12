using RistWorld;

static void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
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

authority.SetPermission(owner, "deck:1", h, PermissionGrant.Edit);
authority.SetPermission(owner, "deck:2", h, PermissionGrant.View);
authority.SetPermission(owner, "card:d", i, PermissionGrant.Deny);
authority.SetPermission(owner, "card:b", h, PermissionGrant.View);
authority.SetPermission(owner, "card:b", i, PermissionGrant.View);

authority.Attach(owner, "deck:1", "card:a");
authority.Attach(owner, "deck:1", "card:b");
authority.Attach(owner, "deck:1", "card:c");
authority.Attach(owner, "deck:1", "card:d");

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

// Delegation: the operator can act as h only inside the grant and can never exceed h's own resource authority.
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

authority.PublishActivity(delegatedH.SessionId, "deck:1", "edit", "Editing deck metadata");
var ownerPip = authority.GetObservableActivity(h, delegatedH.SessionId);
Check(ownerPip is not null && ownerPip.ActorUserId == delegateUser && ownerPip.EffectiveUserId == h,
    "Owner PIP must identify both operator and effective identity.");

authority.RevokeDelegation(h, delegation.GrantId);
Check(!authority.EvaluateSessionAccess(delegatedH.SessionId, "deck:1", AuthorityResourceAction.View).Allowed,
    "Revocation must immediately invalidate an already-open delegated session.");

// Guardian co-presence and platform content gating.
authority.SetPermission(owner, "card:safe", juvenile, PermissionGrant.View);
var guardianLink = authority.SetGuardianLink(
    guardian,
    juvenile,
    requireGuardianPresence: true,
    approvedContentDescriptors: ["violence-gore"]);
var juvenileSession = authority.StartSession(juvenile, juvenile, sessionId: "session:juvenile");

Check(!authority.EvaluateSessionAccess(juvenileSession.SessionId, "card:safe", AuthorityResourceAction.View).Allowed,
    "Required guardian co-presence must block the juvenile when guardian is absent.");
var guardianSession = authority.StartSession(guardian, guardian, sessionId: "session:guardian");
Check(authority.EvaluateSessionAccess(juvenileSession.SessionId, "card:safe", AuthorityResourceAction.View).Allowed,
    "Juvenile access should resume when the required guardian is directly present.");

var allowedMinorContent = new ContentAccessContext(
    ContentAllowancePolicy.Minor,
    ["violence-gore"],
    ["violence-gore"]);
Check(authority.EvaluateSessionAccess(juvenileSession.SessionId, "card:safe", AuthorityResourceAction.View, content: allowedMinorContent).Allowed,
    "Guardian-approved descriptor within the platform's minor allowance should pass.");

var disallowedMinorContent = new ContentAccessContext(
    ContentAllowancePolicy.Minor,
    ["explicit-sexual-content"],
    ["explicit-sexual-content"]);
Check(!authority.EvaluateSessionAccess(juvenileSession.SessionId, "card:safe", AuthorityResourceAction.View, content: disallowedMinorContent).Allowed,
    "Guardian permissions must not weaken the platform content floor.");

authority.PublishActivity(juvenileSession.SessionId, "card:safe", "view", "Viewing supervised content");
Check(authority.GetObservableActivity(guardian, juvenileSession.SessionId) is not null,
    "Linked guardian must be able to observe the juvenile semantic activity frame.");

// A guardian can tighten access further even when recursive authority would otherwise permit it.
guardianLink.BlockedResourceIds.Add("card:safe");
Check(!authority.EvaluateSessionAccess(juvenileSession.SessionId, "card:safe", AuthorityResourceAction.View).Allowed,
    "Guardian resource block must override an otherwise valid object permission.");

// Sensitive operations require distinct, scoped, expiring M-of-N approval.
var approval = authority.CreateApprovalRequest(
    requestedByUserId: "developer-requester",
    operationKey: "production-migration",
    targetResourceId: "system:production",
    requiredApprovals: 2,
    eligibleApprovers: ["dev:a", "dev:b", "dev:c"],
    lifetime: TimeSpan.FromMinutes(10),
    requestId: "approval:production-migration");
Check(authority.Approve(approval.RequestId, "dev:a"), "First eligible approval should count.");
Check(!authority.Approve(approval.RequestId, "dev:a"), "One identity must not count twice.");
Check(authority.Approve(approval.RequestId, "dev:b"), "Second distinct eligible approval should count.");
Check(approval.IsSatisfied(DateTimeOffset.UtcNow), "2-of-3 approval should now be satisfied.");
Check(authority.ConsumeApproval(approval.RequestId, "production-migration", "system:production"),
    "Satisfied approval should be consumable only for the exact operation and target.");
Check(!authority.ConsumeApproval(approval.RequestId, "production-migration", "system:production"),
    "Consumed approval must not be reusable.");

Check(authority.AuditTrail.Count > 0, "Authority decisions and mutations must produce audit events.");

Console.WriteLine("Recursive Authority contract tests: PASS");
