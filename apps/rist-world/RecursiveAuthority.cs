namespace RistWorld;

public enum PermissionGrant
{
    None = 0,
    Public = 1,
    View = 2,
    Edit = 3,
    Deny = 4
}

public enum AuthorityResourceAction
{
    View,
    Edit
}

[Flags]
public enum DelegatedCapability
{
    None = 0,
    View = 1 << 0,
    Edit = 1 << 1,
    AssumeIdentity = 1 << 2,
    Observe = 1 << 3,
    Approve = 1 << 4,
    Operate = 1 << 5,
    ManagePermissions = 1 << 6
}

public enum AccountSensitiveAction
{
    ChangePassword,
    ChangeMfa,
    ChangeRecovery,
    ManagePaymentMethods,
    AcceptLegalAgreement,
    DeleteAccount,
    ChangeRootOwner,
    ExportPrivateUserData
}

public sealed record AuthorityDecision(
    bool Allowed,
    PermissionGrant EffectivePermission,
    string ResourceId,
    string? SourceResourceId,
    bool Inherited,
    string Reason,
    IReadOnlyList<string> Trace);

public sealed record SafetyDecision(bool Allowed, string Reason);

public sealed record ContentAccessContext(
    string? Band,
    IReadOnlyCollection<string> AccountAllowedDescriptors,
    IReadOnlyCollection<string> ResourceDescriptors,
    string? InteractingUserId = null);

public sealed record AuthorityAuditEvent(
    DateTimeOffset TimestampUtc,
    string EventType,
    string ActorUserId,
    string EffectiveUserId,
    string? ResourceId,
    string? DelegationId,
    bool Allowed,
    string Detail);

public sealed record AuthoritySession(
    string SessionId,
    string ActorUserId,
    string EffectiveUserId,
    string? DelegationId,
    DateTimeOffset StartedUtc,
    DateTimeOffset LastSeenUtc);

public sealed record ActivityFrame(
    string SessionId,
    string ActorUserId,
    string EffectiveUserId,
    string ResourceId,
    string Action,
    string Summary,
    DateTimeOffset TimestampUtc);

public sealed class AuthorityResourcePolicy
{
    internal AuthorityResourcePolicy(string resourceId, string ownerUserId)
    {
        ResourceId = resourceId;
        OwnerUserId = ownerUserId;
        Entries[ownerUserId] = PermissionGrant.Edit;
    }

    public string ResourceId { get; }
    public string OwnerUserId { get; }
    public bool StopsInheritance { get; internal set; }
    public IReadOnlyDictionary<string, PermissionGrant> Permissions => Entries;
    internal Dictionary<string, PermissionGrant> Entries { get; } = new(StringComparer.Ordinal);
}

public sealed record ContainmentEdge(
    string EdgeId,
    string ParentResourceId,
    string ChildResourceId,
    bool InheritPermissions);

public sealed class DelegationGrant
{
    internal DelegationGrant(
        string grantId,
        string ownerUserId,
        string delegateUserId,
        IEnumerable<string> resourceScope,
        DelegatedCapability capabilities,
        DateTimeOffset? expiresUtc,
        bool allowRedelegation)
    {
        GrantId = grantId;
        OwnerUserId = ownerUserId;
        DelegateUserId = delegateUserId;
        ResourceScope = new HashSet<string>(resourceScope, StringComparer.Ordinal);
        Capabilities = capabilities;
        ExpiresUtc = expiresUtc;
        AllowRedelegation = allowRedelegation;
    }

    public string GrantId { get; }
    public string OwnerUserId { get; }
    public string DelegateUserId { get; }
    public IReadOnlySet<string> ResourceScope { get; }
    public DelegatedCapability Capabilities { get; }
    public DateTimeOffset? ExpiresUtc { get; }
    public DateTimeOffset? RevokedUtc { get; internal set; }
    public bool AllowRedelegation { get; }

    public bool IsActive(DateTimeOffset nowUtc)
        => RevokedUtc is null && (ExpiresUtc is null || ExpiresUtc > nowUtc);
}

public sealed class GuardianLink
{
    internal GuardianLink(string guardianUserId, string juvenileUserId)
    {
        GuardianUserId = guardianUserId;
        JuvenileUserId = juvenileUserId;
    }

    public string GuardianUserId { get; }
    public string JuvenileUserId { get; }
    public bool RequireGuardianPresence { get; internal set; }
    public HashSet<string> ApprovedContentDescriptors { get; } = new(StringComparer.Ordinal);
    public HashSet<string> BlockedResourceIds { get; } = new(StringComparer.Ordinal);
    public HashSet<string> BlockedUserIds { get; } = new(StringComparer.Ordinal);
}

public sealed class MultiPartyApprovalRequest
{
    internal MultiPartyApprovalRequest(
        string requestId,
        string operationKey,
        string targetResourceId,
        string requestedByUserId,
        int requiredApprovals,
        IEnumerable<string> eligibleApprovers,
        DateTimeOffset expiresUtc,
        bool allowRequesterApproval)
    {
        RequestId = requestId;
        OperationKey = operationKey;
        TargetResourceId = targetResourceId;
        RequestedByUserId = requestedByUserId;
        RequiredApprovals = requiredApprovals;
        EligibleApprovers = new HashSet<string>(eligibleApprovers, StringComparer.Ordinal);
        ExpiresUtc = expiresUtc;
        AllowRequesterApproval = allowRequesterApproval;
    }

    public string RequestId { get; }
    public string OperationKey { get; }
    public string TargetResourceId { get; }
    public string RequestedByUserId { get; }
    public int RequiredApprovals { get; }
    public IReadOnlySet<string> EligibleApprovers { get; }
    public IReadOnlySet<string> Approvals => ApprovalSet;
    public DateTimeOffset ExpiresUtc { get; }
    public bool AllowRequesterApproval { get; }
    public bool Consumed { get; internal set; }
    internal HashSet<string> ApprovalSet { get; } = new(StringComparer.Ordinal);

    public bool IsSatisfied(DateTimeOffset nowUtc)
        => !Consumed && nowUtc < ExpiresUtc && ApprovalSet.Count >= RequiredApprovals;
}

/// <summary>
/// Shared evaluator for recursive resource permissions, delegated identity, guardian supervision,
/// semantic PIP observation, and direct-session M-of-N sensitive-operation approval.
/// Authentication proves the actor; this service decides what that actor may do and whose
/// explicitly delegated authority they may exercise. Credentials never flow through this service.
/// </summary>
public sealed class RecursiveAuthorityService
{
    public const string EveryonePrincipal = "*";
    public const int AuditCapacity = 4096;

    private readonly Dictionary<string, AuthorityResourcePolicy> resources = new(StringComparer.Ordinal);
    private readonly Dictionary<string, List<ContainmentEdge>> parentsByChild = new(StringComparer.Ordinal);
    private readonly Dictionary<string, DelegationGrant> delegations = new(StringComparer.Ordinal);
    private readonly Dictionary<string, AuthoritySession> sessions = new(StringComparer.Ordinal);
    private readonly Dictionary<string, GuardianLink> guardiansByJuvenile = new(StringComparer.Ordinal);
    private readonly Dictionary<string, ActivityFrame> activityBySession = new(StringComparer.Ordinal);
    private readonly Dictionary<string, MultiPartyApprovalRequest> approvals = new(StringComparer.Ordinal);
    private readonly List<AuthorityAuditEvent> audit = [];

    public IReadOnlyCollection<AuthorityResourcePolicy> Resources => resources.Values;
    public IReadOnlyCollection<DelegationGrant> Delegations => delegations.Values;
    public IReadOnlyCollection<AuthoritySession> Sessions => sessions.Values;
    public IReadOnlyList<AuthorityAuditEvent> AuditTrail => audit;

    public AuthorityResourcePolicy EnsureResource(string resourceId, string ownerUserId, bool stopsInheritance = false)
    {
        RequireId(resourceId, nameof(resourceId));
        RequireId(ownerUserId, nameof(ownerUserId));
        if (resources.TryGetValue(resourceId, out var existing)) return existing;

        var policy = new AuthorityResourcePolicy(resourceId, ownerUserId)
        {
            StopsInheritance = stopsInheritance
        };
        resources.Add(resourceId, policy);
        return policy;
    }

    public bool CanManagePermissions(string actorUserId, string resourceId, string? delegationId = null)
    {
        if (!resources.TryGetValue(resourceId, out var policy)) return false;
        if (StringComparer.Ordinal.Equals(policy.OwnerUserId, actorUserId)) return true;
        if (delegationId is null || !delegations.TryGetValue(delegationId, out var grant)) return false;

        return grant.IsActive(DateTimeOffset.UtcNow)
            && StringComparer.Ordinal.Equals(grant.DelegateUserId, actorUserId)
            && StringComparer.Ordinal.Equals(grant.OwnerUserId, policy.OwnerUserId)
            && grant.Capabilities.HasFlag(DelegatedCapability.ManagePermissions)
            && ScopeMatches(grant.ResourceScope, resourceId, null);
    }

    public void SetPermission(
        string actorUserId,
        string resourceId,
        string principalUserId,
        PermissionGrant grant,
        string? delegationId = null)
    {
        RequireId(principalUserId, nameof(principalUserId));
        if (!resources.TryGetValue(resourceId, out var policy))
            throw new InvalidOperationException($"Unknown authority resource '{resourceId}'.");
        if (!CanManagePermissions(actorUserId, resourceId, delegationId))
        {
            Record("permission-change", actorUserId, actorUserId, resourceId, delegationId, false, "Permission management denied.");
            throw new UnauthorizedAccessException("Permission management denied.");
        }

        if (grant == PermissionGrant.None)
            policy.Entries.Remove(principalUserId);
        else
            policy.Entries[principalUserId] = grant;

        Record("permission-change", actorUserId, policy.OwnerUserId, resourceId, delegationId, true,
            $"{principalUserId}={grant}");
    }

    public void SetStopsInheritance(
        string actorUserId,
        string resourceId,
        bool stopsInheritance,
        string? delegationId = null)
    {
        if (!resources.TryGetValue(resourceId, out var policy))
            throw new InvalidOperationException($"Unknown authority resource '{resourceId}'.");
        if (!CanManagePermissions(actorUserId, resourceId, delegationId))
            throw new UnauthorizedAccessException("Permission management denied.");

        policy.StopsInheritance = stopsInheritance;
        Record("inheritance-policy", actorUserId, policy.OwnerUserId, resourceId, delegationId, true,
            stopsInheritance ? "Local/self policy stops inheritance." : "Inheritance enabled.");
    }

    public ContainmentEdge Attach(
        string actorUserId,
        string parentResourceId,
        string childResourceId,
        bool inheritPermissions = true,
        string? edgeId = null,
        string? delegationId = null)
    {
        if (!resources.ContainsKey(parentResourceId) || !resources.ContainsKey(childResourceId))
            throw new InvalidOperationException("Both parent and child resources must exist before containment is created.");
        if (!CanManagePermissions(actorUserId, parentResourceId, delegationId))
            throw new UnauthorizedAccessException("Parent containment management denied.");

        // Inheriting containment can change who may access the child. The actor therefore needs
        // permission-management authority over both ends. Non-inheriting placement only needs
        // authority over the parent container.
        if (inheritPermissions && !CanManagePermissions(actorUserId, childResourceId, delegationId))
        {
            Record("containment-attach", actorUserId, resources[parentResourceId].OwnerUserId, childResourceId, delegationId, false,
                "Inherited containment denied because child authority is not controlled by actor.");
            throw new UnauthorizedAccessException("Inherited containment requires authority over both parent and child.");
        }

        if (StringComparer.Ordinal.Equals(parentResourceId, childResourceId) || WouldCreateCycle(parentResourceId, childResourceId))
            throw new InvalidOperationException("Recursive authority containment cannot contain a cycle.");

        var list = GetParentEdges(childResourceId);
        var existing = list.FirstOrDefault(x => StringComparer.Ordinal.Equals(x.ParentResourceId, parentResourceId));
        if (existing is not null) return existing;

        var edge = new ContainmentEdge(
            edgeId ?? $"{parentResourceId}>{childResourceId}",
            parentResourceId,
            childResourceId,
            inheritPermissions);
        list.Add(edge);
        Record("containment-attach", actorUserId, resources[parentResourceId].OwnerUserId, childResourceId, delegationId, true,
            $"parent={parentResourceId}; inherit={inheritPermissions}");
        return edge;
    }

    public bool Detach(
        string actorUserId,
        string parentResourceId,
        string childResourceId,
        string? delegationId = null)
    {
        if (!CanManagePermissions(actorUserId, parentResourceId, delegationId))
            throw new UnauthorizedAccessException("Parent containment management denied.");
        if (!parentsByChild.TryGetValue(childResourceId, out var list)) return false;

        var removed = list.RemoveAll(x => StringComparer.Ordinal.Equals(x.ParentResourceId, parentResourceId)) > 0;
        if (list.Count == 0) parentsByChild.Remove(childResourceId);
        if (removed)
        {
            Record("containment-detach", actorUserId, resources[parentResourceId].OwnerUserId, childResourceId, delegationId, true,
                $"parent={parentResourceId}; inherited authority removed with relationship");
        }
        return removed;
    }

    public AuthorityDecision Resolve(
        string resourceId,
        string principalUserId,
        AuthorityResourceAction action,
        IReadOnlyList<string>? containmentPath = null)
    {
        RequireId(resourceId, nameof(resourceId));
        RequireId(principalUserId, nameof(principalUserId));
        return ResolveInternal(resourceId, principalUserId, action, containmentPath, 0, new HashSet<string>(StringComparer.Ordinal), []);
    }

    public DelegationGrant CreateDelegation(
        string ownerUserId,
        string delegateUserId,
        IEnumerable<string> resourceScope,
        DelegatedCapability capabilities,
        DateTimeOffset? expiresUtc = null,
        bool allowRedelegation = false,
        string? grantId = null)
    {
        RequireId(ownerUserId, nameof(ownerUserId));
        RequireId(delegateUserId, nameof(delegateUserId));
        if (StringComparer.Ordinal.Equals(ownerUserId, delegateUserId))
            throw new InvalidOperationException("A user does not need delegation to act as themselves.");

        var scope = new HashSet<string>(resourceScope ?? [], StringComparer.Ordinal);
        if (scope.Count == 0) throw new InvalidOperationException("Delegation must have an explicit resource scope.");
        if (!capabilities.HasFlag(DelegatedCapability.AssumeIdentity))
            throw new InvalidOperationException("Identity delegation must explicitly include AssumeIdentity.");

        var id = grantId ?? Guid.NewGuid().ToString("N");
        if (delegations.ContainsKey(id)) throw new InvalidOperationException($"Delegation '{id}' already exists.");

        var grant = new DelegationGrant(id, ownerUserId, delegateUserId, scope, capabilities, expiresUtc, allowRedelegation);
        delegations.Add(id, grant);
        Record("delegation-create", ownerUserId, ownerUserId, null, id, true,
            $"delegate={delegateUserId}; capabilities={capabilities}; redelegation={allowRedelegation}");
        return grant;
    }

    public bool RevokeDelegation(string ownerUserId, string grantId)
    {
        if (!delegations.TryGetValue(grantId, out var grant)) return false;
        if (!StringComparer.Ordinal.Equals(grant.OwnerUserId, ownerUserId))
            throw new UnauthorizedAccessException("Only the delegating identity can revoke this grant.");
        if (grant.RevokedUtc is not null) return false;

        grant.RevokedUtc = DateTimeOffset.UtcNow;
        Record("delegation-revoke", ownerUserId, ownerUserId, null, grantId, true, $"delegate={grant.DelegateUserId}");
        return true;
    }

    public AuthoritySession StartSession(
        string actorUserId,
        string effectiveUserId,
        string? delegationId = null,
        string? sessionId = null)
    {
        RequireId(actorUserId, nameof(actorUserId));
        RequireId(effectiveUserId, nameof(effectiveUserId));
        var now = DateTimeOffset.UtcNow;

        if (!StringComparer.Ordinal.Equals(actorUserId, effectiveUserId))
        {
            if (delegationId is null || !delegations.TryGetValue(delegationId, out var grant)
                || !grant.IsActive(now)
                || !StringComparer.Ordinal.Equals(grant.OwnerUserId, effectiveUserId)
                || !StringComparer.Ordinal.Equals(grant.DelegateUserId, actorUserId)
                || !grant.Capabilities.HasFlag(DelegatedCapability.AssumeIdentity))
            {
                Record("session-start", actorUserId, effectiveUserId, null, delegationId, false, "Delegated identity assumption denied.");
                throw new UnauthorizedAccessException("Delegated identity assumption denied.");
            }
        }
        else if (delegationId is not null)
        {
            throw new InvalidOperationException("Direct sessions must not claim a delegation.");
        }

        var id = sessionId ?? Guid.NewGuid().ToString("N");
        if (sessions.ContainsKey(id)) throw new InvalidOperationException($"Session '{id}' already exists.");

        var session = new AuthoritySession(id, actorUserId, effectiveUserId, delegationId, now, now);
        sessions.Add(id, session);
        Record("session-start", actorUserId, effectiveUserId, null, delegationId, true,
            StringComparer.Ordinal.Equals(actorUserId, effectiveUserId) ? "direct" : "delegated");
        return session;
    }

    public bool EndSession(string sessionId)
    {
        if (!sessions.Remove(sessionId, out var session)) return false;
        activityBySession.Remove(sessionId);
        Record("session-end", session.ActorUserId, session.EffectiveUserId, null, session.DelegationId, true, "ended");
        return true;
    }

    public bool CanPerformAccountAction(string sessionId, AccountSensitiveAction action)
    {
        if (!sessions.TryGetValue(sessionId, out var session)) return false;
        var direct = IsDirectSession(session);
        Record("account-sensitive-action", session.ActorUserId, session.EffectiveUserId, null, session.DelegationId, direct,
            action.ToString());
        return direct;
    }

    public AuthorityDecision EvaluateSessionAccess(
        string sessionId,
        string resourceId,
        AuthorityResourceAction action,
        IReadOnlyList<string>? containmentPath = null,
        ContentAccessContext? content = null)
    {
        if (!sessions.TryGetValue(sessionId, out var session))
            return Denied(resourceId, PermissionGrant.None, null, false, "Unknown session.", [resourceId]);

        if (session.DelegationId is not null)
        {
            if (!delegations.TryGetValue(session.DelegationId, out var grant)
                || !grant.IsActive(DateTimeOffset.UtcNow)
                || !StringComparer.Ordinal.Equals(grant.OwnerUserId, session.EffectiveUserId)
                || !StringComparer.Ordinal.Equals(grant.DelegateUserId, session.ActorUserId)
                || !ScopeMatches(grant.ResourceScope, resourceId, containmentPath)
                || !DelegationAllows(grant, action))
            {
                var denied = Denied(resourceId, PermissionGrant.Deny, resourceId, false,
                    "Delegation is revoked, expired, out of recursive scope, or lacks capability.", [resourceId]);
                RecordDecision(session, resourceId, denied);
                return denied;
            }
        }

        var safety = EvaluateSafety(session.EffectiveUserId, resourceId, content, containmentPath);
        if (!safety.Allowed)
        {
            var denied = Denied(resourceId, PermissionGrant.Deny, resourceId, false, safety.Reason, [resourceId]);
            RecordDecision(session, resourceId, denied);
            return denied;
        }

        var decision = Resolve(resourceId, session.EffectiveUserId, action, containmentPath);
        RecordDecision(session, resourceId, decision);
        return decision;
    }

    public GuardianLink SetGuardianLink(
        string guardianUserId,
        string juvenileUserId,
        bool requireGuardianPresence,
        IEnumerable<string>? approvedContentDescriptors = null,
        IEnumerable<string>? blockedResourceIds = null,
        IEnumerable<string>? blockedUserIds = null)
    {
        RequireId(guardianUserId, nameof(guardianUserId));
        RequireId(juvenileUserId, nameof(juvenileUserId));
        if (StringComparer.Ordinal.Equals(guardianUserId, juvenileUserId))
            throw new InvalidOperationException("Guardian and juvenile must be different identities.");

        var link = new GuardianLink(guardianUserId, juvenileUserId)
        {
            RequireGuardianPresence = requireGuardianPresence
        };
        link.ApprovedContentDescriptors.UnionWith(approvedContentDescriptors ?? []);
        link.BlockedResourceIds.UnionWith(blockedResourceIds ?? []);
        link.BlockedUserIds.UnionWith(blockedUserIds ?? []);
        guardiansByJuvenile[juvenileUserId] = link;
        Record("guardian-policy", guardianUserId, juvenileUserId, null, null, true,
            $"presence={requireGuardianPresence}; approved={link.ApprovedContentDescriptors.Count}; blockedResources={link.BlockedResourceIds.Count}; blockedUsers={link.BlockedUserIds.Count}");
        return link;
    }

    public bool RemoveGuardianLink(string guardianUserId, string juvenileUserId)
    {
        if (!guardiansByJuvenile.TryGetValue(juvenileUserId, out var link)) return false;
        if (!StringComparer.Ordinal.Equals(link.GuardianUserId, guardianUserId))
            throw new UnauthorizedAccessException("Guardian relationship mismatch.");
        guardiansByJuvenile.Remove(juvenileUserId);
        Record("guardian-policy-remove", guardianUserId, juvenileUserId, null, null, true, "removed");
        return true;
    }

    public SafetyDecision EvaluateSafety(
        string effectiveUserId,
        string resourceId,
        ContentAccessContext? content,
        IReadOnlyList<string>? containmentPath = null)
    {
        guardiansByJuvenile.TryGetValue(effectiveUserId, out var guardian);
        if (guardian is not null)
        {
            if (ResourceOrAncestorMatches(guardian.BlockedResourceIds, resourceId, containmentPath))
                return new SafetyDecision(false, "Guardian policy blocks this resource or its containing scope.");
            if (content?.InteractingUserId is not null && guardian.BlockedUserIds.Contains(content.InteractingUserId))
                return new SafetyDecision(false, "Guardian policy blocks interaction with this user.");
            if (guardian.RequireGuardianPresence && !HasDirectActiveSession(guardian.GuardianUserId))
                return new SafetyDecision(false, "Guardian co-presence is required.");
        }

        if (content is null) return new SafetyDecision(true, "No content gate supplied.");

        var guardianApproved = guardian?.ApprovedContentDescriptors ?? [];
        var allowed = ContentAllowancePolicy.CampaignAllowed(
            content.Band,
            content.AccountAllowedDescriptors,
            content.ResourceDescriptors,
            guardianApproved);

        return allowed
            ? new SafetyDecision(true, "Content allowance passed.")
            : new SafetyDecision(false, "Platform/account/guardian content allowance denied access.");
    }

    public ActivityFrame PublishActivity(string sessionId, string resourceId, string action, string summary)
    {
        if (!sessions.TryGetValue(sessionId, out var session))
            throw new InvalidOperationException("Cannot publish activity for an unknown session.");

        var now = DateTimeOffset.UtcNow;
        sessions[sessionId] = session with { LastSeenUtc = now };
        var frame = new ActivityFrame(
            sessionId,
            session.ActorUserId,
            session.EffectiveUserId,
            resourceId,
            action,
            summary,
            now);
        activityBySession[sessionId] = frame;
        return frame;
    }

    public ActivityFrame? GetObservableActivity(string observerUserId, string targetSessionId)
    {
        if (!sessions.TryGetValue(targetSessionId, out var target)) return null;
        if (!activityBySession.TryGetValue(targetSessionId, out var frame)) return null;

        var ownerWatchingDelegate = !StringComparer.Ordinal.Equals(target.ActorUserId, target.EffectiveUserId)
            && StringComparer.Ordinal.Equals(observerUserId, target.EffectiveUserId);
        var guardianWatchingJuvenile = guardiansByJuvenile.TryGetValue(target.EffectiveUserId, out var guardian)
            && StringComparer.Ordinal.Equals(observerUserId, guardian.GuardianUserId);
        var self = StringComparer.Ordinal.Equals(observerUserId, target.ActorUserId)
            || StringComparer.Ordinal.Equals(observerUserId, target.EffectiveUserId);

        return ownerWatchingDelegate || guardianWatchingJuvenile || self ? frame : null;
    }

    public MultiPartyApprovalRequest CreateApprovalRequest(
        string requesterSessionId,
        string operationKey,
        string targetResourceId,
        int requiredApprovals,
        IEnumerable<string> eligibleApprovers,
        TimeSpan lifetime,
        bool allowRequesterApproval = false,
        string? requestId = null)
    {
        if (!sessions.TryGetValue(requesterSessionId, out var requester) || !IsDirectSession(requester))
            throw new UnauthorizedAccessException("Sensitive approval requests require a direct authenticated requester session.");

        var eligible = new HashSet<string>(eligibleApprovers ?? [], StringComparer.Ordinal);
        if (requiredApprovals < 2)
            throw new InvalidOperationException("Sensitive multi-party authorization requires at least two distinct approvals.");
        if (eligible.Count < requiredApprovals)
            throw new InvalidOperationException("Eligible approvers must be at least the required approval count.");
        if (lifetime <= TimeSpan.Zero)
            throw new InvalidOperationException("Approval requests require a positive lifetime.");

        var id = requestId ?? Guid.NewGuid().ToString("N");
        if (approvals.ContainsKey(id)) throw new InvalidOperationException($"Approval request '{id}' already exists.");

        var request = new MultiPartyApprovalRequest(
            id,
            operationKey,
            targetResourceId,
            requester.ActorUserId,
            requiredApprovals,
            eligible,
            DateTimeOffset.UtcNow.Add(lifetime),
            allowRequesterApproval);
        approvals.Add(id, request);
        Record("approval-request", requester.ActorUserId, requester.EffectiveUserId, targetResourceId, null, true,
            $"operation={operationKey}; required={requiredApprovals}; eligible={eligible.Count}; session={requesterSessionId}");
        return request;
    }

    public bool Approve(string requestId, string approverSessionId)
    {
        if (!approvals.TryGetValue(requestId, out var request)) return false;
        if (!sessions.TryGetValue(approverSessionId, out var approver) || !IsDirectSession(approver)) return false;

        var now = DateTimeOffset.UtcNow;
        var approverUserId = approver.ActorUserId;
        if (request.Consumed || now >= request.ExpiresUtc) return false;
        if (!request.EligibleApprovers.Contains(approverUserId)) return false;
        if (!request.AllowRequesterApproval && StringComparer.Ordinal.Equals(request.RequestedByUserId, approverUserId)) return false;

        var added = request.ApprovalSet.Add(approverUserId);
        if (added)
        {
            Record("approval", approverUserId, approverUserId, request.TargetResourceId, null, true,
                $"request={requestId}; session={approverSessionId}; {request.ApprovalSet.Count}/{request.RequiredApprovals}");
        }
        return added;
    }

    public bool ConsumeApproval(string requestId, string operationKey, string targetResourceId)
    {
        if (!approvals.TryGetValue(requestId, out var request)) return false;
        if (!request.IsSatisfied(DateTimeOffset.UtcNow)) return false;
        if (!StringComparer.Ordinal.Equals(request.OperationKey, operationKey)
            || !StringComparer.Ordinal.Equals(request.TargetResourceId, targetResourceId))
            return false;

        request.Consumed = true;
        Record("approval-consume", request.RequestedByUserId, request.RequestedByUserId, targetResourceId, null, true,
            $"request={requestId}; operation={operationKey}");
        return true;
    }

    private AuthorityDecision ResolveInternal(
        string resourceId,
        string principalUserId,
        AuthorityResourceAction action,
        IReadOnlyList<string>? containmentPath,
        int pathIndex,
        HashSet<string> visited,
        List<string> trace)
    {
        if (!visited.Add(resourceId))
            return Denied(resourceId, PermissionGrant.Deny, resourceId, true,
                "Containment cycle encountered during resolution.", [.. trace, resourceId]);
        if (!resources.TryGetValue(resourceId, out var policy))
            return Denied(resourceId, PermissionGrant.None, null, trace.Count > 0,
                "Unknown authority resource.", [.. trace, resourceId]);

        trace.Add(resourceId);

        if (policy.Entries.TryGetValue(principalUserId, out var exact))
            return FromGrant(resourceId, policy.ResourceId, exact, action, trace.Count > 1, "Explicit user policy.", trace);

        policy.Entries.TryGetValue(EveryonePrincipal, out var everyone);
        if (everyone == PermissionGrant.Deny)
            return Denied(resourceId, PermissionGrant.Deny, policy.ResourceId, trace.Count > 1,
                "Explicit local deny-all policy.", [.. trace]);
        if (everyone == PermissionGrant.Edit)
            return FromGrant(resourceId, policy.ResourceId, everyone, action, trace.Count > 1,
                "Explicit local public-edit policy.", trace);
        if (action == AuthorityResourceAction.View && everyone is PermissionGrant.Public or PermissionGrant.View)
            return FromGrant(resourceId, policy.ResourceId, everyone, action, trace.Count > 1,
                "Explicit local public/view policy.", trace);

        if (policy.StopsInheritance)
        {
            return everyone is PermissionGrant.Public or PermissionGrant.View
                ? FromGrant(resourceId, policy.ResourceId, everyone, action, trace.Count > 1,
                    "Local/self policy stops inheritance.", trace)
                : Denied(resourceId, PermissionGrant.None, policy.ResourceId, trace.Count > 1,
                    "Local/self policy stops inheritance.", [.. trace]);
        }

        var parents = ParentEdges(resourceId).Where(x => x.InheritPermissions).ToArray();
        if (containmentPath is not null && pathIndex < containmentPath.Count)
        {
            var requestedParent = containmentPath[pathIndex];
            var edge = parents.FirstOrDefault(x => StringComparer.Ordinal.Equals(x.ParentResourceId, requestedParent));
            if (edge is null)
                return Denied(resourceId, PermissionGrant.None, null, true,
                    "Requested containment path is not valid for this resource.", [.. trace]);
            return ResolveInternal(requestedParent, principalUserId, action, containmentPath, pathIndex + 1, visited, trace);
        }

        if (parents.Length == 1)
            return ResolveInternal(parents[0].ParentResourceId, principalUserId, action, containmentPath, pathIndex, visited, trace);
        if (parents.Length > 1)
            return Denied(resourceId, PermissionGrant.None, null, true,
                "Multiple permission-bearing parents require an explicit containment path.", [.. trace]);

        return Denied(resourceId, PermissionGrant.None, null, trace.Count > 1,
            "No explicit or inherited permission grants this action.", [.. trace]);
    }

    private static AuthorityDecision FromGrant(
        string requestedResourceId,
        string sourceResourceId,
        PermissionGrant grant,
        AuthorityResourceAction action,
        bool inherited,
        string reason,
        IReadOnlyList<string> trace)
    {
        var allowed = grant switch
        {
            PermissionGrant.Edit => true,
            PermissionGrant.View or PermissionGrant.Public => action == AuthorityResourceAction.View,
            _ => false
        };

        return allowed
            ? new AuthorityDecision(true, grant, requestedResourceId, sourceResourceId, inherited, reason, [.. trace])
            : Denied(requestedResourceId, grant, sourceResourceId, inherited,
                grant == PermissionGrant.Deny ? "Explicit deny." : $"{grant} does not grant {action}.", [.. trace]);
    }

    private static AuthorityDecision Denied(
        string resourceId,
        PermissionGrant grant,
        string? sourceResourceId,
        bool inherited,
        string reason,
        IReadOnlyList<string> trace)
        => new(false, grant, resourceId, sourceResourceId, inherited, reason, trace);

    private bool ScopeMatches(IReadOnlySet<string> scope, string resourceId, IReadOnlyList<string>? containmentPath)
    {
        if (scope.Contains(EveryonePrincipal) || scope.Contains(resourceId)) return true;
        return ResourceOrAncestorMatches(scope, resourceId, containmentPath);
    }

    private bool ResourceOrAncestorMatches(IReadOnlySet<string> targets, string resourceId, IReadOnlyList<string>? containmentPath)
    {
        if (targets.Contains(resourceId)) return true;
        if (containmentPath is not null)
            return containmentPath.Any(targets.Contains);

        var pending = new Stack<string>();
        var seen = new HashSet<string>(StringComparer.Ordinal) { resourceId };
        foreach (var edge in ParentEdges(resourceId).Where(x => x.InheritPermissions))
            pending.Push(edge.ParentResourceId);

        while (pending.Count > 0)
        {
            var current = pending.Pop();
            if (!seen.Add(current)) continue;
            if (targets.Contains(current)) return true;
            foreach (var edge in ParentEdges(current).Where(x => x.InheritPermissions))
                pending.Push(edge.ParentResourceId);
        }

        return false;
    }

    private bool WouldCreateCycle(string parentResourceId, string childResourceId)
    {
        var pending = new Stack<string>();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        pending.Push(parentResourceId);

        while (pending.Count > 0)
        {
            var current = pending.Pop();
            if (!seen.Add(current)) continue;
            if (StringComparer.Ordinal.Equals(current, childResourceId)) return true;
            foreach (var edge in ParentEdges(current))
                pending.Push(edge.ParentResourceId);
        }
        return false;
    }

    private List<ContainmentEdge> GetParentEdges(string childResourceId)
    {
        if (!parentsByChild.TryGetValue(childResourceId, out var list))
        {
            list = [];
            parentsByChild.Add(childResourceId, list);
        }
        return list;
    }

    private IReadOnlyList<ContainmentEdge> ParentEdges(string childResourceId)
        => parentsByChild.TryGetValue(childResourceId, out var list) ? list : [];

    private static bool DelegationAllows(DelegationGrant grant, AuthorityResourceAction action)
        => action switch
        {
            AuthorityResourceAction.View => grant.Capabilities.HasFlag(DelegatedCapability.View)
                || grant.Capabilities.HasFlag(DelegatedCapability.Edit)
                || grant.Capabilities.HasFlag(DelegatedCapability.Operate),
            AuthorityResourceAction.Edit => grant.Capabilities.HasFlag(DelegatedCapability.Edit)
                || grant.Capabilities.HasFlag(DelegatedCapability.Operate),
            _ => false
        };

    private bool HasDirectActiveSession(string userId)
        => sessions.Values.Any(x => StringComparer.Ordinal.Equals(x.ActorUserId, userId)
            && StringComparer.Ordinal.Equals(x.EffectiveUserId, userId)
            && x.DelegationId is null);

    private static bool IsDirectSession(AuthoritySession session)
        => StringComparer.Ordinal.Equals(session.ActorUserId, session.EffectiveUserId)
            && session.DelegationId is null;

    private void RecordDecision(AuthoritySession session, string resourceId, AuthorityDecision decision)
        => Record("access", session.ActorUserId, session.EffectiveUserId, resourceId, session.DelegationId, decision.Allowed,
            $"permission={decision.EffectivePermission}; source={decision.SourceResourceId ?? "none"}; reason={decision.Reason}");

    private void Record(
        string eventType,
        string actorUserId,
        string effectiveUserId,
        string? resourceId,
        string? delegationId,
        bool allowed,
        string detail)
    {
        audit.Add(new AuthorityAuditEvent(
            DateTimeOffset.UtcNow,
            eventType,
            actorUserId,
            effectiveUserId,
            resourceId,
            delegationId,
            allowed,
            detail));
        if (audit.Count > AuditCapacity)
            audit.RemoveRange(0, audit.Count - AuditCapacity);
    }

    private static void RequireId(string value, string paramName)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentException("Identifier cannot be empty.", paramName);
    }
}
