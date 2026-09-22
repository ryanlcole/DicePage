using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace RistWorld;

/// <summary>
/// Source-grounded, deterministic project observer. It retrieves evidence; it does not
/// grant authority, promote canon, execute imported code, or redefine Rune/Glyph/SHAEP.
/// </summary>
public sealed class ReLiCObserverService(HttpClient http, DiscordAuthClient auth)
{
    const string PublicSeedPath = "data/relic-observer-seed.json";
    const string PrivateCorpusKey = "relic-observer/corpus.v1.json";
    const int MaxPrivateDocuments = 80;
    const int MaxPrivateCharacters = 5_000_000;
    const int MaxDocumentCharacters = 2_000_000;
    const int MaxProjectKnowledgeRecordsPerDocument = 3000;
    const int ChunkCharacters = 1400;
    const int ChunkOverlap = 180;
    const int MaxAssociationNeighbors = 6;
    const int MaxRareTermDocumentFrequency = 10;
    const int MaxSourceAssociationGroup = 24;
    const int AssociationSeedCount = 6;
    const double AssociationExpansionFactor = 0.28;

    static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true
    };

    static readonly HashSet<string> StopWords = new(StringComparer.Ordinal)
    {
        "a","an","and","are","as","at","be","been","but","by","can","do","does","for","from",
        "had","has","have","how","i","if","in","into","is","it","its","me","my","of","on","or",
        "our","that","the","their","then","there","these","this","to","was","we","were","what",
        "when","where","which","who","why","will","with","would","you","your"
    };

    ObserverPublicCorpus _public = new();
    ObserverPrivateCorpus _private = new();
    readonly List<IndexedEvidence> _documents = [];
    readonly Dictionary<string,int> _documentFrequency = new(StringComparer.Ordinal);
    readonly Dictionary<int,List<AssociationEdge>> _associations = [];
    double _averageLength = 1;
    bool _initializing;

    public event Action? Changed;
    public bool Loaded { get; private set; }
    public bool PublicSeedLoaded { get; private set; }
    public string Status { get; private set; } = "Not loaded";
    public int PublicSourceCount => _public.Sources.Count;
    public int PublicRecordCount => _public.Records.Count;
    public IReadOnlyList<ObserverPrivateDocument> PrivateDocuments => _private.Documents;
    public int IndexedEvidenceCount => _documents.Count;
    public int AssociationEdgeCount => _associations.Sum(x=>x.Value.Count)/2;
    public string SnapshotDate => _public.SnapshotDate;

    public async Task InitializeAsync()
    {
        if(Loaded || _initializing)return;
        _initializing=true;
        Status="Loading source ledger…";
        Changed?.Invoke();

        try
        {
            try
            {
                _public=await http.GetFromJsonAsync<ObserverPublicCorpus>(PublicSeedPath,JsonOptions) ?? new();
                PublicSeedLoaded=_public.Records.Count>0;
            }
            catch
            {
                _public=new();
                PublicSeedLoaded=false;
            }

            try
            {
                _private=await auth.DownloadJsonAsync<ObserverPrivateCorpus>(PrivateCorpusKey) ?? new();
                if(_private.SchemaVersion!=1)_private=new();
            }
            catch
            {
                // Private account storage can be unavailable during auth transitions.
                // Public evidence remains usable; private material never falls back to public storage.
                _private=new();
            }

            RebuildIndex();
            Loaded=true;
            Status=PublicSeedLoaded
                ? $"Ready · {_documents.Count:N0} evidence units indexed"
                : "Ready · public seed unavailable; private imports only";
        }
        finally
        {
            _initializing=false;
            Changed?.Invoke();
        }
    }

    public ObserverAnswer Query(string rawQuery, int topK=8)
    {
        var query=(rawQuery??"").Trim();
        if(query.Length==0)
            return ObserverAnswer.Empty("Enter a question or search phrase.");

        if(!Loaded)
            return ObserverAnswer.Empty("ReLiC Observer is still loading.");

        var queryTerms=Tokenize(query).Where(t=>!StopWords.Contains(t)).Distinct(StringComparer.Ordinal).Take(24).ToArray();
        if(queryTerms.Length==0)
            queryTerms=Tokenize(query).Distinct(StringComparer.Ordinal).Take(12).ToArray();

        if(queryTerms.Length==0)
            return ObserverAnswer.Empty("UNKNOWN — the query contains no searchable terms.");

        var normalizedPhrase=NormalizeForPhrase(query);
        var directScores=new Dictionary<int,double>();
        foreach(var document in _documents)
        {
            double score=0;
            foreach(var term in queryTerms)
            {
                if(!document.TermFrequency.TryGetValue(term,out var tf) || tf<=0)continue;
                var df=_documentFrequency.TryGetValue(term,out var found)?found:0;
                var idf=Math.Log(1.0+((_documents.Count-df+0.5)/(df+0.5)));
                const double k1=1.25;
                const double b=0.72;
                var denominator=tf+k1*(1-b+b*(document.TokenCount/_averageLength));
                score+=idf*((tf*(k1+1))/Math.Max(denominator,0.001));

                if(document.TitleTerms.Contains(term))score+=idf*1.35;
            }

            if(normalizedPhrase.Length>3 && document.NormalizedText.Contains(normalizedPhrase,StringComparison.Ordinal))
                score+=4.0;
            if(normalizedPhrase.Length>3 && document.NormalizedTitle.Contains(normalizedPhrase,StringComparison.Ordinal))
                score+=5.5;

            if(score>0)directScores[document.Index]=score;
        }

        if(directScores.Count==0)
        {
            return new ObserverAnswer
            {
                Query=query,
                TruthSummary="UNKNOWN",
                Answer="UNKNOWN — no loaded evidence supports an answer to this query. ReLiC will not invent a missing source.",
                IndexedEvidenceCount=_documents.Count,
                PublicSourceCount=PublicSourceCount,
                PrivateDocumentCount=_private.Documents.Count,
                AssociationEdgeCount=AssociationEdgeCount,
                RetrievalTrace="0 direct matches · 0 bounded associations"
            };
        }

        var combined=new Dictionary<int,double>(directScores);
        var associatedFrom=new Dictionary<int,(int Seed,string Reason,double Strength)>();
        var seeds=directScores
            .OrderByDescending(x=>x.Value)
            .ThenBy(x=>_documents[x.Key].Evidence.Title,StringComparer.OrdinalIgnoreCase)
            .Take(AssociationSeedCount)
            .ToArray();

        foreach(var seed in seeds)
        {
            if(!_associations.TryGetValue(seed.Key,out var edges))continue;
            foreach(var edge in edges)
            {
                var expansion=seed.Value*edge.Strength*AssociationExpansionFactor;
                if(expansion<=0)continue;
                if(combined.TryGetValue(edge.TargetIndex,out var existing))
                {
                    combined[edge.TargetIndex]=existing+expansion;
                    continue;
                }

                combined[edge.TargetIndex]=expansion;
                associatedFrom[edge.TargetIndex]=(seed.Key,edge.Reason,edge.Strength);
            }
        }

        var ranked=combined
            .Select(x=>(Evidence:_documents[x.Key],Score:x.Value,Direct:directScores.ContainsKey(x.Key)))
            .OrderByDescending(x=>x.Direct)
            .ThenByDescending(x=>x.Score)
            .ThenBy(x=>x.Evidence.Evidence.Title,StringComparer.OrdinalIgnoreCase)
            .Take(Math.Clamp(topK,1,16))
            .Select(x=>(x.Evidence,x.Score))
            .ToList();

        var hits=ranked.Select(x=>
        {
            var isDirect=directScores.ContainsKey(x.Evidence.Index);
            var association=associatedFrom.TryGetValue(x.Evidence.Index,out var found)?found:default;
            var path=isDirect
                ?"DIRECT"
                :association.Seed>=0
                    ?$"ASSOCIATED via {_documents[association.Seed].Evidence.Title}"
                    :"ASSOCIATED";
            var reason=isDirect
                ?"lexical/phrase evidence match"
                :association.Reason??"bounded association";
            return new ObserverHit
            {
                RecordId=x.Evidence.Evidence.RecordId,
                Title=x.Evidence.Evidence.Title,
                Category=x.Evidence.Evidence.Category,
                Status=x.Evidence.Evidence.Status,
                TruthDomain=NormalizeTruthDomain(x.Evidence.Evidence.TruthDomain),
                Scope=x.Evidence.Evidence.Scope,
                Visibility=x.Evidence.Evidence.Visibility,
                Provenance=x.Evidence.Evidence.Provenance,
                Score=Math.Round(x.Score,3),
                Excerpt=BestExcerpt(x.Evidence.Evidence.Text,queryTerms),
                Sources=x.Evidence.Evidence.Sources,
                RetrievalPath=path,
                RetrievalReason=reason,
                DirectMatch=isDirect
            };
        }).ToList();

        var truthDomains=hits.Where(h=>h.DirectMatch).Select(h=>h.TruthDomain).Distinct(StringComparer.Ordinal).ToArray();
        var truthSummary=truthDomains.Length switch
        {
            0=>"UNKNOWN",
            1=>truthDomains[0],
            _=>"MIXED"
        };
        var directExcerpts=hits.Where(h=>h.DirectMatch).Select(h=>h.Excerpt)
            .Where(x=>!string.IsNullOrWhiteSpace(x))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Take(4)
            .ToArray();

        var prefix=truthSummary switch
        {
            "FACT"=>"The strongest loaded FACT evidence says:",
            "FICTION"=>"The strongest loaded FICTION/canon evidence says:",
            "HYPOTHESIS"=>"The strongest loaded HYPOTHESIS evidence says:",
            "UNKNOWN"=>"The strongest loaded evidence is unresolved/UNKNOWN:",
            _=>"The strongest loaded evidence spans multiple truth domains:"
        };

        var answer=new StringBuilder(prefix);
        foreach(var excerpt in directExcerpts)
            answer.Append("\n\n• ").Append(excerpt);

        var associatedCount=hits.Count(h=>!h.DirectMatch);
        if(associatedCount>0)
            answer.Append($"\n\nReLiC also followed {associatedCount} bounded association{(associatedCount==1?"":"s")} to nearby evidence. Associated evidence is context, not proof of the query itself.");

        answer.Append("\n\nReLiC is reporting loaded evidence, not granting authority or silently promoting a source to canon.");

        return new ObserverAnswer
        {
            Query=query,
            TruthSummary=truthSummary,
            Answer=answer.ToString(),
            Hits=hits,
            IndexedEvidenceCount=_documents.Count,
            PublicSourceCount=PublicSourceCount,
            PrivateDocumentCount=_private.Documents.Count,
            AssociationEdgeCount=AssociationEdgeCount,
            RetrievalTrace=$"{directScores.Count} direct matches · {associatedFrom.Count} bounded associations · {hits.Count} returned"
        };
    }

    public string BuildEvidencePacket(ObserverAnswer answer)
    {
        ArgumentNullException.ThrowIfNull(answer);
        var packet=new
        {
            contract="relic.observer.evidence-packet",
            version=1,
            generatedAtUtc=DateTimeOffset.UtcNow,
            query=answer.Query,
            truthSummary=answer.TruthSummary,
            retrievalTrace=answer.RetrievalTrace,
            indexedEvidenceCount=answer.IndexedEvidenceCount,
            associationEdgeCount=answer.AssociationEdgeCount,
            evidence=answer.Hits.Select(hit=>new
            {
                recordId=hit.RecordId,
                title=hit.Title,
                category=hit.Category,
                status=hit.Status,
                truthDomain=hit.TruthDomain,
                scope=hit.Scope,
                visibility=hit.Visibility,
                direct=hit.DirectMatch,
                retrievalPath=hit.RetrievalPath,
                retrievalReason=hit.RetrievalReason,
                score=hit.Score,
                excerpt=hit.Excerpt,
                provenance=hit.Provenance,
                sources=hit.Sources.Select(source=>new
                {
                    sourceId=source.SourceId,
                    title=source.Title,
                    uri=source.Uri,
                    status=source.Status,
                    visibility=source.Visibility,
                    sourceOrigin=source.SourceOrigin
                })
            })
        };
        return JsonSerializer.Serialize(packet,JsonOptions);
    }

    public async Task<ObserverPrivateDocument> ImportPrivateTextAsync(string title,string content,string? fileName=null)
    {
        title=(title??"").Trim();
        content=NormalizeImportedText(content??"");
        if(title.Length==0)throw new InvalidOperationException("A source title is required.");
        if(content.Length==0)throw new InvalidOperationException("The source is empty.");
        if(content.Length>MaxDocumentCharacters)throw new InvalidOperationException("One imported source may contain at most 2,000,000 characters.");

        var currentCharacters=_private.Documents.Sum(x=>x.Content.Length);
        var existingId=StableId(title,content);
        var existing=_private.Documents.FirstOrDefault(x=>x.Id==existingId);
        if(existing is not null)return existing;

        if(_private.Documents.Count>=MaxPrivateDocuments)
            throw new InvalidOperationException($"Private source limit reached ({MaxPrivateDocuments}). Remove a source before importing another.");
        if(currentCharacters+content.Length>MaxPrivateCharacters)
            throw new InvalidOperationException("Private corpus limit reached. Remove older material before importing more.");

        var document=new ObserverPrivateDocument
        {
            Id=existingId,
            Title=title,
            FileName=(fileName??"").Trim(),
            ImportedAtUtc=DateTimeOffset.UtcNow,
            Content=content,
            SourceOrigin="UNKNOWN",
            ProvenanceHandling="OUTSIDER_AI/RED",
            Visibility="private-account-storage"
        };
        _private.Documents.Add(document);
        await SavePrivateCorpusAsync();
        RebuildIndex();
        Status=$"Imported privately · {title}";
        Changed?.Invoke();
        return document;
    }

    public async Task RemovePrivateDocumentAsync(string id)
    {
        var removed=_private.Documents.RemoveAll(x=>string.Equals(x.Id,id,StringComparison.Ordinal));
        if(removed==0)return;
        await SavePrivateCorpusAsync();
        RebuildIndex();
        Status="Private source removed from Observer corpus.";
        Changed?.Invoke();
    }

    public async Task ClearPrivateCorpusAsync()
    {
        _private=new();
        await SavePrivateCorpusAsync();
        RebuildIndex();
        Status="Private Observer corpus cleared.";
        Changed?.Invoke();
    }

    async Task SavePrivateCorpusAsync()
    {
        _private.SchemaVersion=1;
        _private.UpdatedAtUtc=DateTimeOffset.UtcNow;
        var json=JsonSerializer.Serialize(_private,JsonOptions);
        await auth.UploadTextAsync(PrivateCorpusKey,json,"application/json");
    }

    void RebuildIndex()
    {
        _documents.Clear();
        _documentFrequency.Clear();

        var publicSources=_public.Sources.ToDictionary(x=>x.SourceId,StringComparer.Ordinal);
        foreach(var record in _public.Records)
        {
            var refs=record.SourceIds
                .Where(publicSources.ContainsKey)
                .Select(id=>publicSources[id])
                .Select(s=>new ObserverSourceRef
                {
                    SourceId=s.SourceId,
                    Title=s.Title,
                    Uri=s.Uri,
                    Status=s.Status,
                    Visibility=s.Visibility,
                    SourceOrigin=s.SourceOrigin
                }).ToList();

            AddEvidence(new ObserverEvidence
            {
                RecordId=record.RecordId,
                Title=record.Title,
                Text=record.Text,
                Category=record.Category,
                Status=record.Status,
                TruthDomain=NormalizeTruthDomain(record.TruthDomain),
                Scope=record.Scope,
                Visibility="public-project-knowledge",
                Provenance="OUTSIDER_AI/RED extraction; source provenance preserved in ledger",
                Sources=refs
            });
        }

        foreach(var document in _private.Documents)
        {
            if(TryAddProjectKnowledgeDocument(document))continue;
            var chunks=Chunk(document.Content,ChunkCharacters,ChunkOverlap);
            for(var i=0;i<chunks.Count;i++)
            {
                AddEvidence(new ObserverEvidence
                {
                    RecordId=$"{document.Id}:chunk:{i+1}",
                    Title=chunks.Count==1?document.Title:$"{document.Title} · part {i+1}",
                    Text=chunks[i],
                    Category="private-import",
                    Status="imported-source",
                    TruthDomain="UNKNOWN",
                    Scope="private-owner",
                    Visibility=document.Visibility,
                    Provenance=$"{document.SourceOrigin}; handled as {document.ProvenanceHandling}",
                    Sources=
                    [
                        new ObserverSourceRef
                        {
                            SourceId=document.Id,
                            Title=document.Title,
                            Status="private-import",
                            Visibility=document.Visibility,
                            SourceOrigin=document.SourceOrigin
                        }
                    ]
                });
            }
        }

        _averageLength=_documents.Count==0?1:_documents.Average(x=>Math.Max(1,x.TokenCount));
        foreach(var document in _documents)
            foreach(var term in document.TermFrequency.Keys)
                _documentFrequency[term]=_documentFrequency.TryGetValue(term,out var count)?count+1:1;

        BuildAssociations();
    }

    void BuildAssociations()
    {
        _associations.Clear();
        if(_documents.Count<2)return;

        var pairScores=new Dictionary<(int Left,int Right),AssociationAccumulator>();

        void AddPair(int first,int second,double weight,string reason)
        {
            if(first==second||weight<=0)return;
            var key=first<second?(first,second):(second,first);
            if(!pairScores.TryGetValue(key,out var accumulator))
            {
                accumulator=new AssociationAccumulator();
                pairScores[key]=accumulator;
            }
            accumulator.Score+=weight;
            if(accumulator.Reasons.Count<3 && !accumulator.Reasons.Contains(reason,StringComparer.OrdinalIgnoreCase))
                accumulator.Reasons.Add(reason);
        }

        var sourceGroups=new Dictionary<string,List<int>>(StringComparer.Ordinal);
        foreach(var document in _documents)
        {
            foreach(var sourceId in document.Evidence.Sources.Select(x=>x.SourceId).Where(x=>!string.IsNullOrWhiteSpace(x)).Distinct(StringComparer.Ordinal))
            {
                if(!sourceGroups.TryGetValue(sourceId,out var group))
                {
                    group=[];
                    sourceGroups[sourceId]=group;
                }
                group.Add(document.Index);
            }
        }

        foreach(var group in sourceGroups.Values)
        {
            var members=group.Distinct().Take(MaxSourceAssociationGroup+1).ToArray();
            if(members.Length<2||members.Length>MaxSourceAssociationGroup)continue;
            for(var i=0;i<members.Length;i++)
                for(var j=i+1;j<members.Length;j++)
                    AddPair(members[i],members[j],1.6,"shared source");
        }

        var rareTermGroups=new Dictionary<string,List<int>>(StringComparer.Ordinal);
        foreach(var document in _documents)
        {
            foreach(var term in document.TermFrequency.Keys)
            {
                if(!_documentFrequency.TryGetValue(term,out var df)||df<2||df>MaxRareTermDocumentFrequency)continue;
                if(!rareTermGroups.TryGetValue(term,out var group))
                {
                    group=[];
                    rareTermGroups[term]=group;
                }
                group.Add(document.Index);
            }
        }

        foreach(var pair in rareTermGroups)
        {
            var members=pair.Value.Distinct().ToArray();
            var df=members.Length;
            if(df<2||df>MaxRareTermDocumentFrequency)continue;
            var weight=Math.Min(0.8,1.5/df);
            var reason=$"rare term: {pair.Key}";
            for(var i=0;i<members.Length;i++)
                for(var j=i+1;j<members.Length;j++)
                    AddPair(members[i],members[j],weight,reason);
        }

        var candidateEdges=new Dictionary<int,List<AssociationEdge>>();
        foreach(var pair in pairScores)
        {
            var strength=Math.Clamp(pair.Value.Score/2.6,0.05,1.0);
            var reason=string.Join(" + ",pair.Value.Reasons);
            if(!candidateEdges.TryGetValue(pair.Key.Left,out var left))
            {
                left=[];
                candidateEdges[pair.Key.Left]=left;
            }
            if(!candidateEdges.TryGetValue(pair.Key.Right,out var right))
            {
                right=[];
                candidateEdges[pair.Key.Right]=right;
            }
            left.Add(new AssociationEdge(pair.Key.Right,strength,reason));
            right.Add(new AssociationEdge(pair.Key.Left,strength,reason));
        }

        foreach(var pair in candidateEdges)
            _associations[pair.Key]=pair.Value
                .OrderByDescending(x=>x.Strength)
                .ThenBy(x=>_documents[x.TargetIndex].Evidence.Title,StringComparer.OrdinalIgnoreCase)
                .Take(MaxAssociationNeighbors)
                .ToList();
    }

    bool TryAddProjectKnowledgeDocument(ObserverPrivateDocument document)
    {
        if(!document.FileName.EndsWith(".json",StringComparison.OrdinalIgnoreCase)
           && !document.Content.TrimStart().StartsWith('{'))return false;

        try
        {
            using var json=JsonDocument.Parse(document.Content);
            var root=json.RootElement;
            if(!root.TryGetProperty("dataset_id",out var dataset)
               || !string.Equals(dataset.GetString(),"shaelvien-project-knowledge",StringComparison.Ordinal)
               || !root.TryGetProperty("records",out var records)
               || records.ValueKind!=JsonValueKind.Array)return false;

            var sources=new Dictionary<string,ObserverSourceRef>(StringComparer.Ordinal);
            if(root.TryGetProperty("sources",out var sourceArray) && sourceArray.ValueKind==JsonValueKind.Array)
            {
                foreach(var source in sourceArray.EnumerateArray())
                {
                    var id=JsonString(source,"source_id");
                    if(id.Length==0)continue;
                    sources[id]=new ObserverSourceRef
                    {
                        SourceId=id,
                        Title=JsonString(source,"title"),
                        Uri=JsonString(source,"uri"),
                        Status=JsonString(source,"status"),
                        Visibility="private-import",
                        SourceOrigin=JsonString(source,"source_origin")
                    };
                }
            }

            var count=0;
            foreach(var record in records.EnumerateArray())
            {
                if(count++>=MaxProjectKnowledgeRecordsPerDocument)break;
                var sourceRefs=new List<ObserverSourceRef>();
                if(record.TryGetProperty("source_ids",out var ids) && ids.ValueKind==JsonValueKind.Array)
                {
                    foreach(var item in ids.EnumerateArray())
                    {
                        var id=item.GetString()??"";
                        if(sources.TryGetValue(id,out var source))sourceRefs.Add(source);
                    }
                }
                if(sourceRefs.Count==0)
                    sourceRefs.Add(new ObserverSourceRef
                    {
                        SourceId=document.Id,
                        Title=document.Title,
                        Status="private-project-knowledge-import",
                        Visibility="private-import",
                        SourceOrigin=document.SourceOrigin
                    });

                AddEvidence(new ObserverEvidence
                {
                    RecordId=JsonString(record,"record_id",fallback:$"{document.Id}:record:{count}"),
                    Title=JsonString(record,"title",fallback:$"{document.Title} · record {count}"),
                    Text=JsonString(record,"text"),
                    Category=JsonString(record,"category",fallback:"private-project-knowledge"),
                    Status=JsonString(record,"status",fallback:"imported-source"),
                    TruthDomain=NormalizeTruthDomain(JsonString(record,"truth_domain",fallback:"UNKNOWN")),
                    Scope=JsonString(record,"scope",fallback:"private-owner"),
                    Visibility="private-account-storage",
                    Provenance=$"Private project corpus · {document.SourceOrigin}; handled as {document.ProvenanceHandling}",
                    Sources=sourceRefs
                });
            }
            return count>0;
        }
        catch(JsonException)
        {
            return false;
        }
    }

    void AddEvidence(ObserverEvidence evidence)
    {
        if(string.IsNullOrWhiteSpace(evidence.Text))return;
        var searchText=string.Join(' ',evidence.Title,evidence.Category,evidence.Status,evidence.TruthDomain,evidence.Scope,
            string.Join(' ',evidence.Sources.Select(s=>s.Title)),evidence.Text);
        var terms=Tokenize(searchText).Where(t=>!StopWords.Contains(t)).ToArray();
        var frequencies=new Dictionary<string,int>(StringComparer.Ordinal);
        foreach(var term in terms)
            frequencies[term]=frequencies.TryGetValue(term,out var count)?count+1:1;

        _documents.Add(new IndexedEvidence
        {
            Index=_documents.Count,
            Evidence=evidence,
            TermFrequency=frequencies,
            TitleTerms=Tokenize(evidence.Title).ToHashSet(StringComparer.Ordinal),
            TokenCount=Math.Max(1,terms.Length),
            NormalizedTitle=NormalizeForPhrase(evidence.Title),
            NormalizedText=NormalizeForPhrase(evidence.Text)
        });
    }

    static string BestExcerpt(string text,IReadOnlyCollection<string> queryTerms)
    {
        var candidates=text.Replace("\r","").Split(['\n','.','!','?'],StringSplitOptions.RemoveEmptyEntries|StringSplitOptions.TrimEntries)
            .Where(x=>x.Length>20)
            .Select(sentence=>new
            {
                Sentence=sentence,
                Score=Tokenize(sentence).Count(queryTerms.Contains)
            })
            .OrderByDescending(x=>x.Score)
            .ThenByDescending(x=>Math.Min(x.Sentence.Length,500))
            .Take(1)
            .Select(x=>x.Sentence)
            .ToArray();

        var excerpt=candidates.FirstOrDefault()??text.Trim();
        if(excerpt.Length>480)excerpt=excerpt[..477].TrimEnd()+"…";
        return excerpt;
    }

    static List<string> Chunk(string text,int size,int overlap)
    {
        var result=new List<string>();
        if(text.Length<=size){result.Add(text);return result;}
        var start=0;
        while(start<text.Length)
        {
            var take=Math.Min(size,text.Length-start);
            var end=start+take;
            if(end<text.Length)
            {
                var breakAt=text.LastIndexOfAny(['\n','.','!','?'],end-1,Math.Min(take,320));
                if(breakAt>start+size/2)end=breakAt+1;
            }
            var chunk=text[start..end].Trim();
            if(chunk.Length>0)result.Add(chunk);
            if(end>=text.Length)break;
            start=Math.Max(start+1,end-overlap);
        }
        return result;
    }

    static IEnumerable<string> Tokenize(string text)
    {
        if(string.IsNullOrWhiteSpace(text))yield break;
        var token=new StringBuilder(32);
        foreach(var c in text)
        {
            if(char.IsLetterOrDigit(c) || c=='_' || c=='-')
            {
                token.Append(char.ToLowerInvariant(c));
                continue;
            }
            if(token.Length>=2)yield return token.ToString();
            token.Clear();
        }
        if(token.Length>=2)yield return token.ToString();
    }

    static string NormalizeForPhrase(string text)
    {
        var builder=new StringBuilder(text.Length);
        var pendingSpace=false;
        foreach(var c in text)
        {
            if(char.IsLetterOrDigit(c))
            {
                if(pendingSpace && builder.Length>0)builder.Append(' ');
                builder.Append(char.ToLowerInvariant(c));
                pendingSpace=false;
            }
            else pendingSpace=true;
        }
        return builder.ToString();
    }

    static string NormalizeImportedText(string text)
        => text.Replace("\0","").Replace("\r\n","\n").Replace('\r','\n').Trim();

    static string StableId(string title,string content)
    {
        var bytes=Encoding.UTF8.GetBytes(title+"\n"+content);
        var hash=SHA256.HashData(bytes);
        return "private-"+Convert.ToHexString(hash)[..24].ToLowerInvariant();
    }

    static string NormalizeTruthDomain(string value)
    {
        var normalized=(value??"").Trim().ToUpperInvariant();
        return normalized is "FACT" or "HYPOTHESIS" or "FICTION" or "UNKNOWN"?normalized:"UNKNOWN";
    }

    static string JsonString(JsonElement element,string property,string fallback="")
    {
        if(element.TryGetProperty(property,out var value) && value.ValueKind==JsonValueKind.String)
            return value.GetString()?.Trim()??fallback;
        return fallback;
    }

    sealed class IndexedEvidence
    {
        public int Index { get; init; }
        public ObserverEvidence Evidence { get; init; } = new();
        public Dictionary<string,int> TermFrequency { get; init; } = new(StringComparer.Ordinal);
        public HashSet<string> TitleTerms { get; init; } = new(StringComparer.Ordinal);
        public int TokenCount { get; init; }
        public string NormalizedTitle { get; init; } = "";
        public string NormalizedText { get; init; } = "";
    }

    sealed class AssociationAccumulator
    {
        public double Score { get; set; }
        public List<string> Reasons { get; } = [];
    }

    sealed record AssociationEdge(int TargetIndex,double Strength,string Reason);

    sealed class ObserverEvidence
    {
        public string RecordId { get; init; } = "";
        public string Title { get; init; } = "";
        public string Text { get; init; } = "";
        public string Category { get; init; } = "";
        public string Status { get; init; } = "";
        public string TruthDomain { get; init; } = "UNKNOWN";
        public string Scope { get; init; } = "";
        public string Visibility { get; init; } = "";
        public string Provenance { get; init; } = "";
        public List<ObserverSourceRef> Sources { get; init; } = [];
    }
}

public sealed class ObserverPublicCorpus
{
    public int SchemaVersion { get; set; } = 1;
    public string DatasetId { get; set; } = "";
    public string SnapshotDate { get; set; } = "";
    public string CorpusSha256 { get; set; } = "";
    public string ExtractionProvenance { get; set; } = "";
    public List<ObserverPublicSource> Sources { get; set; } = [];
    public List<ObserverPublicRecord> Records { get; set; } = [];
}

public sealed class ObserverPublicSource
{
    public string SourceId { get; set; } = "";
    public string Title { get; set; } = "";
    public string Kind { get; set; } = "";
    public string Uri { get; set; } = "";
    public string Status { get; set; } = "";
    public string Visibility { get; set; } = "";
    public string ObservedAt { get; set; } = "";
    public string Sha256 { get; set; } = "";
    public string SourceOrigin { get; set; } = "";
}

public sealed class ObserverPublicRecord
{
    public string RecordId { get; set; } = "";
    public string Title { get; set; } = "";
    public string Category { get; set; } = "";
    public string Status { get; set; } = "";
    public string TruthDomain { get; set; } = "UNKNOWN";
    public string Scope { get; set; } = "";
    public string EffectiveDate { get; set; } = "";
    public List<string> SourceIds { get; set; } = [];
    public string SourceLocator { get; set; } = "";
    public string Text { get; set; } = "";
}

public sealed class ObserverPrivateCorpus
{
    public int SchemaVersion { get; set; } = 1;
    public DateTimeOffset? UpdatedAtUtc { get; set; }
    public List<ObserverPrivateDocument> Documents { get; set; } = [];
}

public sealed class ObserverPrivateDocument
{
    public string Id { get; set; } = "";
    public string Title { get; set; } = "";
    public string FileName { get; set; } = "";
    public DateTimeOffset ImportedAtUtc { get; set; }
    public string Content { get; set; } = "";
    public string SourceOrigin { get; set; } = "UNKNOWN";
    public string ProvenanceHandling { get; set; } = "OUTSIDER_AI/RED";
    public string Visibility { get; set; } = "private-account-storage";
}

public sealed class ObserverSourceRef
{
    public string SourceId { get; set; } = "";
    public string Title { get; set; } = "";
    public string Uri { get; set; } = "";
    public string Status { get; set; } = "";
    public string Visibility { get; set; } = "";
    public string SourceOrigin { get; set; } = "";
}

public sealed class ObserverHit
{
    public string RecordId { get; set; } = "";
    public string Title { get; set; } = "";
    public string Category { get; set; } = "";
    public string Status { get; set; } = "";
    public string TruthDomain { get; set; } = "UNKNOWN";
    public string Scope { get; set; } = "";
    public string Visibility { get; set; } = "";
    public string Provenance { get; set; } = "";
    public double Score { get; set; }
    public string Excerpt { get; set; } = "";
    public List<ObserverSourceRef> Sources { get; set; } = [];
    public string RetrievalPath { get; set; } = "DIRECT";
    public string RetrievalReason { get; set; } = "";
    public bool DirectMatch { get; set; }
}

public sealed class ObserverAnswer
{
    public string Query { get; set; } = "";
    public string TruthSummary { get; set; } = "UNKNOWN";
    public string Answer { get; set; } = "";
    public int IndexedEvidenceCount { get; set; }
    public int PublicSourceCount { get; set; }
    public int PrivateDocumentCount { get; set; }
    public int AssociationEdgeCount { get; set; }
    public string RetrievalTrace { get; set; } = "";
    public List<ObserverHit> Hits { get; set; } = [];

    public static ObserverAnswer Empty(string message)=>new(){Answer=message,TruthSummary="UNKNOWN"};
}
