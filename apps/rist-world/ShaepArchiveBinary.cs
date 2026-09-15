using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace RistWorld;

/// <summary>
/// Binary packing for the SHAEP v2 hot archive profile. The archive is not the
/// source decoder: a decoder/converter first produces normalized hot chunks
/// (image planes, video frames/ranges, audio ranges, etc.), then this codec
/// writes those chunks behind a compact front index for immediate random access.
/// </summary>
public static class ShaepArchiveBinary
{
    public const int BinaryVersion = 1;
    public const int PrefixBytes = 16;
    public const int MaxIndexBytes = 16 * 1024 * 1024;
    static readonly byte[] Magic = Encoding.ASCII.GetBytes("SHAEP2\0\0");
    static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public static void Write(Stream destination, IEnumerable<ShaepArchiveChunk> sourceChunks)
    {
        ArgumentNullException.ThrowIfNull(destination);
        ArgumentNullException.ThrowIfNull(sourceChunks);
        if (!destination.CanWrite) throw new InvalidOperationException("SHAEP destination stream is not writable.");

        var chunks = sourceChunks.ToList();
        if (chunks.Count == 0) throw new InvalidDataException("SHAEP archive requires at least one hot chunk.");

        var seen = new HashSet<string>(StringComparer.Ordinal);
        long payloadOffset = 0;
        var entries = new List<ShaepArchiveChunkIndex>(chunks.Count);

        foreach (var chunk in chunks)
        {
            ValidateChunk(chunk);
            if (!seen.Add(chunk.Id)) throw new InvalidDataException($"Duplicate SHAEP chunk id '{chunk.Id}'.");

            var hash = Convert.ToHexString(SHA256.HashData(chunk.Data)).ToLowerInvariant();
            entries.Add(new ShaepArchiveChunkIndex(
                chunk.Id,
                chunk.Kind,
                chunk.MediaType,
                chunk.TrackIndex,
                chunk.PlaneIndex,
                chunk.Sequence,
                chunk.StartSeconds,
                chunk.DurationSeconds,
                chunk.Width,
                chunk.Height,
                chunk.SampleRate,
                chunk.Channels,
                chunk.PixelFormat,
                chunk.SampleFormat,
                payloadOffset,
                chunk.Data.LongLength,
                hash));
            payloadOffset = checked(payloadOffset + chunk.Data.LongLength);
        }

        var index = new ShaepArchiveIndex(
            ShaepFormat.Name,
            ShaepFormat.CurrentVersion,
            BinaryVersion,
            ShaepFormat.ArchiveProfile,
            ShaepFormat.ArchiveLayout,
            entries);
        var indexBytes = JsonSerializer.SerializeToUtf8Bytes(index, JsonOptions);
        if (indexBytes.Length > MaxIndexBytes)
            throw new InvalidDataException($"SHAEP archive index exceeds {MaxIndexBytes} bytes.");

        Span<byte> prefix = stackalloc byte[PrefixBytes];
        Magic.CopyTo(prefix);
        BinaryPrimitives.WriteInt32LittleEndian(prefix[8..12], BinaryVersion);
        BinaryPrimitives.WriteInt32LittleEndian(prefix[12..16], indexBytes.Length);
        destination.Write(prefix);
        destination.Write(indexBytes);
        foreach (var chunk in chunks) destination.Write(chunk.Data);
    }

    public static ShaepArchiveIndex ReadIndex(Stream source)
    {
        ArgumentNullException.ThrowIfNull(source);
        if (!source.CanRead) throw new InvalidOperationException("SHAEP source stream is not readable.");

        Span<byte> prefix = stackalloc byte[PrefixBytes];
        ReadExactly(source, prefix);
        if (!prefix[..8].SequenceEqual(Magic)) throw new InvalidDataException("SHAEP archive magic is invalid.");

        var binaryVersion = BinaryPrimitives.ReadInt32LittleEndian(prefix[8..12]);
        if (binaryVersion != BinaryVersion)
            throw new InvalidDataException($"Unsupported SHAEP binary version {binaryVersion}.");

        var indexLength = BinaryPrimitives.ReadInt32LittleEndian(prefix[12..16]);
        if (indexLength <= 0 || indexLength > MaxIndexBytes)
            throw new InvalidDataException("SHAEP archive index length is invalid.");

        var indexBytes = new byte[indexLength];
        ReadExactly(source, indexBytes);
        var index = JsonSerializer.Deserialize<ShaepArchiveIndex>(indexBytes, JsonOptions)
            ?? throw new InvalidDataException("SHAEP archive index was empty.");
        ValidateIndex(index);
        return index;
    }

    public static byte[] ReadChunk(Stream source, ShaepArchiveChunkIndex entry, bool verifyIntegrity = true)
    {
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(entry);
        if (!source.CanRead || !source.CanSeek)
            throw new InvalidOperationException("SHAEP random-access reads require a readable, seekable stream.");
        if (entry.Offset < 0 || entry.Length < 0)
            throw new InvalidDataException("SHAEP chunk offset/length is invalid.");

        source.Position = 0;
        var index = ReadIndex(source);
        var authoritative = index.Chunks.FirstOrDefault(x => string.Equals(x.Id, entry.Id, StringComparison.Ordinal))
            ?? throw new InvalidDataException($"SHAEP chunk '{entry.Id}' is not present in the archive index.");
        if (authoritative.Offset != entry.Offset || authoritative.Length != entry.Length)
            throw new InvalidDataException("SHAEP chunk locator does not match the archive index.");
        if (authoritative.Length > int.MaxValue)
            throw new InvalidDataException("SHAEP chunk is too large for an in-memory read.");

        var payloadBase = checked((long)PrefixBytes + JsonSerializer.SerializeToUtf8Bytes(index, JsonOptions).LongLength);
        source.Position = checked(payloadBase + authoritative.Offset);
        var bytes = new byte[(int)authoritative.Length];
        ReadExactly(source, bytes);

        if (verifyIntegrity && !string.IsNullOrWhiteSpace(authoritative.Sha256))
        {
            var actual = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
            if (!string.Equals(actual, authoritative.Sha256, StringComparison.Ordinal))
                throw new InvalidDataException($"SHAEP chunk '{authoritative.Id}' failed integrity verification.");
        }
        return bytes;
    }

    static void ValidateChunk(ShaepArchiveChunk chunk)
    {
        ArgumentNullException.ThrowIfNull(chunk);
        if (string.IsNullOrWhiteSpace(chunk.Id)) throw new InvalidDataException("SHAEP chunk id is required.");
        if (string.IsNullOrWhiteSpace(chunk.Kind)) throw new InvalidDataException("SHAEP chunk kind is required.");
        if (string.IsNullOrWhiteSpace(chunk.MediaType)) throw new InvalidDataException("SHAEP chunk media type is required.");
        if (chunk.Data is null || chunk.Data.Length == 0) throw new InvalidDataException("SHAEP hot chunk data is required.");
        if (chunk.TrackIndex < 0 || chunk.PlaneIndex < 0 || chunk.Sequence < 0)
            throw new InvalidDataException("SHAEP chunk track/plane/sequence values cannot be negative.");
        if (chunk.StartSeconds < 0 || chunk.DurationSeconds < 0)
            throw new InvalidDataException("SHAEP chunk time values cannot be negative.");
        if (chunk.Width < 0 || chunk.Height < 0 || chunk.SampleRate < 0 || chunk.Channels < 0)
            throw new InvalidDataException("SHAEP chunk media dimensions cannot be negative.");
    }

    static void ValidateIndex(ShaepArchiveIndex index)
    {
        if (!string.Equals(index.Format, ShaepFormat.Name, StringComparison.Ordinal))
            throw new InvalidDataException($"Unsupported SHAEP archive format '{index.Format}'.");
        if (index.Version != ShaepFormat.CurrentVersion)
            throw new InvalidDataException($"Unsupported SHAEP archive version {index.Version}.");
        if (index.BinaryVersion != BinaryVersion)
            throw new InvalidDataException($"Unsupported SHAEP binary version {index.BinaryVersion}.");
        if (!string.Equals(index.Profile, ShaepFormat.ArchiveProfile, StringComparison.Ordinal))
            throw new InvalidDataException($"Unsupported SHAEP archive profile '{index.Profile}'.");
        if (!string.Equals(index.Layout, ShaepFormat.ArchiveLayout, StringComparison.Ordinal))
            throw new InvalidDataException($"Unsupported SHAEP archive layout '{index.Layout}'.");
        if (index.Chunks is null || index.Chunks.Count == 0)
            throw new InvalidDataException("SHAEP archive index contains no chunks.");

        long expectedOffset = 0;
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var chunk in index.Chunks)
        {
            if (string.IsNullOrWhiteSpace(chunk.Id) || !seen.Add(chunk.Id))
                throw new InvalidDataException("SHAEP archive chunk ids must be present and unique.");
            if (chunk.Offset != expectedOffset || chunk.Length <= 0)
                throw new InvalidDataException("SHAEP archive chunk offsets must be contiguous and lengths positive.");
            if (chunk.Sha256.Length != 64 || chunk.Sha256.Any(c => !Uri.IsHexDigit(c)))
                throw new InvalidDataException("SHAEP archive chunk SHA-256 is invalid.");
            expectedOffset = checked(expectedOffset + chunk.Length);
        }
    }

    static void ReadExactly(Stream source, Span<byte> buffer)
    {
        var total = 0;
        while (total < buffer.Length)
        {
            var read = source.Read(buffer[total..]);
            if (read <= 0) throw new EndOfStreamException("Unexpected end of SHAEP archive.");
            total += read;
        }
    }

    static void ReadExactly(Stream source, byte[] buffer) => ReadExactly(source, buffer.AsSpan());
}

public sealed record ShaepArchiveChunk(
    string Id,
    string Kind,
    string MediaType,
    byte[] Data,
    int TrackIndex = 0,
    int PlaneIndex = 0,
    long Sequence = 0,
    double StartSeconds = 0,
    double DurationSeconds = 0,
    int Width = 0,
    int Height = 0,
    int SampleRate = 0,
    int Channels = 0,
    string PixelFormat = "",
    string SampleFormat = "");

public sealed record ShaepArchiveChunkIndex(
    string Id,
    string Kind,
    string MediaType,
    int TrackIndex,
    int PlaneIndex,
    long Sequence,
    double StartSeconds,
    double DurationSeconds,
    int Width,
    int Height,
    int SampleRate,
    int Channels,
    string PixelFormat,
    string SampleFormat,
    long Offset,
    long Length,
    string Sha256);

public sealed record ShaepArchiveIndex(
    string Format,
    int Version,
    int BinaryVersion,
    string Profile,
    string Layout,
    IReadOnlyList<ShaepArchiveChunkIndex> Chunks);
