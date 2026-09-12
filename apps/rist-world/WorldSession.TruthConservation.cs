using System.Security.Cryptography;
using System.Text;

namespace RistWorld;

/// <summary>
/// Resource accounting for operations that were proven to preserve semantic truth.
/// The counters are advisory only; they never authorize or suppress a mutation by themselves.
/// </summary>
public readonly record struct TruthConservationMetrics(
    long Comparisons,
    long SemanticNoOps,
    long PersistenceWritesAvoided,
    long BytesAvoided,
    long PersistenceWritesCommitted,
    long PureStateCommits);

public sealed partial class WorldSession
{
    sealed record PersistedTruthStamp(string Fingerprint, int Bytes);

    readonly Dictionary<string, PersistedTruthStamp> _persistedTruth = new(StringComparer.Ordinal);
    long _truthComparisons;
    long _truthSemanticNoOps;
    long _truthWritesAvoided;
    long _truthBytesAvoided;
    long _truthWritesCommitted;
    long _truthPureStateCommits;

    public TruthConservationMetrics TruthConservation => new(
        _truthComparisons,
        _truthSemanticNoOps,
        _truthWritesAvoided,
        _truthBytesAvoided,
        _truthWritesCommitted,
        _truthPureStateCommits);

    /// <summary>
    /// Content identity for an authoritative serialized representation. SHA-256 is used so
    /// the optimization can fail closed: an unknown identity is persisted rather than guessed.
    /// </summary>
    public static string ComputeTruthFingerprint(string canonicalText)
    {
        var bytes = Encoding.UTF8.GetBytes(canonicalText ?? string.Empty);
        return Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    }

    public bool IsPureStateNoOp<T>(T current, T next)
    {
        _truthComparisons++;
        if (!EqualityComparer<T>.Default.Equals(current, next)) return false;
        _truthSemanticNoOps++;
        return true;
    }

    public void RecordPureStateCommit(int count = 1)
    {
        if (count > 0) _truthPureStateCommits += count;
    }

    string PersistedTruthKey(string scope, string identity) => $"{scope}\u001f{identity}";

    bool IsKnownPersistedTruth(string scope, string identity, string fingerprint)
    {
        _truthComparisons++;
        if (!_persistedTruth.TryGetValue(PersistedTruthKey(scope, identity), out var known) ||
            !string.Equals(known.Fingerprint, fingerprint, StringComparison.Ordinal)) return false;

        _truthSemanticNoOps++;
        _truthWritesAvoided++;
        _truthBytesAvoided += Math.Max(0, known.Bytes);
        return true;
    }

    void RememberPersistedTruth(string scope, string identity, string fingerprint, int bytes, bool countWrite = true)
    {
        _persistedTruth[PersistedTruthKey(scope, identity)] = new(fingerprint, Math.Max(0, bytes));
        if (countWrite) _truthWritesCommitted++;
    }

    bool IsKnownPersistedText(string scope, string identity, string text, out string fingerprint)
    {
        fingerprint = ComputeTruthFingerprint(text);
        return IsKnownPersistedTruth(scope, identity, fingerprint);
    }

    void RememberPersistedText(string scope, string identity, string text, string? fingerprint = null, bool countWrite = true)
    {
        fingerprint ??= ComputeTruthFingerprint(text);
        RememberPersistedTruth(scope, identity, fingerprint, Encoding.UTF8.GetByteCount(text), countWrite);
    }
}
