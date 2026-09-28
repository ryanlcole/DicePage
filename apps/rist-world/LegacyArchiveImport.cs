using System.IO.Compression;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Xml.Linq;

namespace RistWorld;

public sealed record LegacyArchiveInspection(int FileCount,long ExpandedBytes);

public sealed record LegacyArchiveEntry(
    string Id,
    string Path,
    string ParentPath,
    string Name,
    string Category,
    string SuggestedLocation,
    long Size,
    string Sha256,
    string OriginalKey,
    string HtmlKey,
    string AssetKey,
    string ContentType,
    bool BrowserViewable,
    string Analysis);

public sealed record LegacyArchiveManifest(
    string Format,
    int Version,
    string WorldId,
    string WorldName,
    string SourceArchiveName,
    string SourceArchiveKey,
    string BinderKey,
    string NavigatorKey,
    string CreatedAtUtc,
    string ProgramExecutionPolicy,
    int FileCount,
    int ImageCount,
    int HtmlCount,
    int ProgramCount,
    List<LegacyArchiveEntry> Files);

public static class LegacyArchiveImport
{
    public const int MaxEntryCount=4000;
    public const long MaxExpandedBytes=500L*1024*1024;
    public const long MaxSingleEntryBytes=100L*1024*1024;

    static readonly HashSet<string> TextExtensions=new(StringComparer.OrdinalIgnoreCase)
    {
        ".txt",".md",".markdown",".log",".ini",".cfg",".conf",".csv",".tsv",".json",".xml",".yaml",".yml",
        ".html",".htm",".xhtml",".rtf",".tex",".org",".nfo",".asc",".lst"
    };
    static readonly HashSet<string> PackageTextExtensions=new(StringComparer.OrdinalIgnoreCase){".docx",".odt"};
    static readonly HashSet<string> LegacyTextExtensions=new(StringComparer.OrdinalIgnoreCase){".doc",".wpd",".wps",".sam",".ws",".wri",".602",".abw"};
    static readonly HashSet<string> BrowserImageExtensions=new(StringComparer.OrdinalIgnoreCase){".png",".jpg",".jpeg",".gif",".webp",".bmp"};
    static readonly HashSet<string> ImageExtensions=new(StringComparer.OrdinalIgnoreCase){".png",".jpg",".jpeg",".gif",".webp",".bmp",".pcx",".tga",".tif",".tiff",".wmf",".emf",".pict",".pct",".iff",".lbm"};
    static readonly HashSet<string> ProgramExtensions=new(StringComparer.OrdinalIgnoreCase)
    {
        ".bas",".pas",".c",".h",".cpp",".hpp",".cc",".for",".f",".f77",".f90",".cob",".cbl",".asm",".s",
        ".py",".pl",".rb",".js",".ts",".java",".cs",".vb",".vbs",".bat",".cmd",".ps1",".sh",".ksh",".awk",".lua",
        ".lisp",".scm",".clj",".pro",".sql",".php",".asp",".aspx",".exe",".com",".dll",".class",".jar"
    };

    static readonly JsonSerializerOptions JsonOptions=new(){WriteIndented=true};

    public static string ManifestKey(string worldId)=>$"worlds/{SafeSegment(worldId)}/legacy/manifest.json";

    public static LegacyArchiveInspection Validate(byte[] zipBytes)
    {
        using var memory=new MemoryStream(zipBytes,false);
        using var archive=new ZipArchive(memory,ZipArchiveMode.Read,false);
        var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var count=0;
        long expanded=0;

        foreach(var entry in archive.Entries)
        {
            var path=NormalizePath(entry.FullName);
            if(string.IsNullOrWhiteSpace(path)||IsDirectory(entry))continue;
            if(!seen.Add(path))throw new InvalidDataException($"Duplicate archive path: {path}");
            count++;
            if(count>MaxEntryCount)throw new InvalidDataException($"Archive exceeds {MaxEntryCount:N0} files.");
            if(entry.Length>MaxSingleEntryBytes)throw new InvalidDataException($"{path} exceeds the {MaxSingleEntryBytes/1024/1024} MB per-file limit.");
            expanded+=entry.Length;
            if(expanded>MaxExpandedBytes)throw new InvalidDataException($"Expanded archive exceeds {MaxExpandedBytes/1024/1024} MB.");
        }
        if(count==0)throw new InvalidDataException("The ZIP contains no files.");
        return new LegacyArchiveInspection(count,expanded);
    }

    public static async Task<LegacyArchiveManifest> ImportAsync(
        byte[] zipBytes,string sourceName,string worldId,string worldName,string appBaseUri,
        DiscordAuthClient auth,IProgress<string>? progress=null)
    {
        var inspection=Validate(zipBytes);
        var root=$"worlds/{SafeSegment(worldId)}/legacy";
        var sourceKey=$"{root}/source/{DateTimeOffset.UtcNow:yyyyMMdd-HHmmss}-{SafeSegment(Path.GetFileName(sourceName))}";
        await auth.UploadBytesAsync(sourceKey,zipBytes,"application/zip");

        using var memory=new MemoryStream(zipBytes,false);
        using var archive=new ZipArchive(memory,ZipArchiveMode.Read,false);
        var files=archive.Entries.Where(e=>!IsDirectory(e)).ToList();
        var result=new List<LegacyArchiveEntry>(files.Count);

        for(var i=0;i<files.Count;i++)
        {
            var entry=files[i];
            var path=NormalizePath(entry.FullName);
            progress?.Report($"Legacy {i+1:N0}/{files.Count:N0} · {path}");

            byte[] bytes;
            await using(var input=entry.Open())
            using(var output=new MemoryStream())
            {
                await input.CopyToAsync(output);
                bytes=output.ToArray();
            }

            var ext=Path.GetExtension(path).ToLowerInvariant();
            var id=IdFor(path);
            var sha=Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
            var category=Category(ext);
            var suggested=SuggestedLocation(path,category);
            var contentType=ContentType(ext);
            var originalKey=$"{root}/originals/{id}/{SafeStoragePath(path)}";
            await auth.UploadBytesAsync(originalKey,bytes,contentType);

            var assetKey="";
            var browserViewable=false;
            if(ImageExtensions.Contains(ext))
            {
                assetKey=$"assets/images/world/legacy/{SafeSegment(worldId)}/{id}{ext}";
                await auth.UploadBytesAsync(assetKey,bytes,contentType);
                browserViewable=BrowserImageExtensions.Contains(ext);
            }

            var text=ExtractText(bytes,ext,out var extraction);
            var analysis=ProgramExtensions.Contains(ext)?AnalyzeProgram(bytes,ext):extraction;
            if(!string.IsNullOrWhiteSpace(extraction)&&ProgramExtensions.Contains(ext))analysis+=" "+extraction;

            var htmlKey=$"{root}/html/{id}.html";
            var html=RepresentationHtml(worldName,path,category,suggested,sha,entry.Length,text,analysis,assetKey);
            await auth.UploadTextAsync(htmlKey,html,"text/html; charset=utf-8");

            result.Add(new LegacyArchiveEntry(
                id,path,Parent(path),Path.GetFileName(path),category,suggested,entry.Length,sha,
                originalKey,htmlKey,assetKey,contentType,browserViewable,analysis));
        }

        result=result.OrderBy(x=>x.Path,StringComparer.OrdinalIgnoreCase).ToList();
        var binderKey=$"{root}/binder.pdf";
        var navigatorKey=$"{root}/index.html";
        var manifest=new LegacyArchiveManifest(
            "rist-legacy-archive",1,worldId,worldName,sourceName,sourceKey,binderKey,navigatorKey,
            DateTimeOffset.UtcNow.ToString("O"),
            "quarantined-static-analysis-only; never execute imported programs in the browser",
            inspection.FileCount,
            result.Count(x=>x.Category=="IMAGE"),
            result.Count,
            result.Count(x=>x.Category=="PROGRAM"),
            result);

        await auth.UploadTextAsync(navigatorKey,NavigatorHtml(manifest,appBaseUri),"text/html; charset=utf-8");
        await auth.UploadBytesAsync(binderKey,BinderPdf(manifest,appBaseUri),"application/pdf");
        await auth.UploadTextAsync(ManifestKey(worldId),JsonSerializer.Serialize(manifest,JsonOptions),"application/json");

        progress?.Report($"Legacy binder created for {result.Count:N0} files.");
        return manifest;
    }

    static string Category(string ext)
    {
        if(ImageExtensions.Contains(ext))return "IMAGE";
        if(ProgramExtensions.Contains(ext))return "PROGRAM";
        if(TextExtensions.Contains(ext)||PackageTextExtensions.Contains(ext)||LegacyTextExtensions.Contains(ext))return "DOCUMENT";
        if(ext==".pdf")return "PDF";
        if(ext is ".xls" or ".xlsx" or ".ods" or ".wk1" or ".wk3" or ".dbf" or ".mdb")return "DATA";
        if(ext is ".wav" or ".mp3" or ".ogg" or ".flac" or ".mid" or ".midi")return "AUDIO";
        if(ext is ".avi" or ".mp4" or ".mov" or ".mkv" or ".mpg" or ".mpeg")return "VIDEO";
        return "FILE";
    }

    static string SuggestedLocation(string path,string category)
    {
        var p=path.ToLowerInvariant();
        if(category=="IMAGE"||p.Contains("map")||p.Contains("paint"))return "MY ASSETS";
        if(p.Contains("npc")||p.Contains("character")||p.Contains("people"))return "NPCS / CHARACTERS";
        if(p.Contains("encounter")||p.Contains("combat")||p.Contains("battle"))return "ENCOUNTERS";
        if(p.Contains("history")||p.Contains("timeline")||p.Contains("chron"))return "HISTORY";
        if(p.Contains("rule")||p.Contains("system"))return "RULES";
        if(p.Contains("lore")||p.Contains("story")||p.Contains("note")||p.Contains("journal"))return "LORE / JOURNAL";
        if(category=="DATA")return "DATA";
        if(category=="PROGRAM")return "QUARANTINED PROGRAM";
        return "LEGACY ARCHIVE";
    }

    static string ExtractText(byte[] bytes,string ext,out string note)
    {
        note="";
        try
        {
            if(ext==".docx"){note="DOCX text normalized to HTML; original preserved.";return XmlPackageText(bytes,"word/document.xml");}
            if(ext==".odt"){note="OpenDocument text normalized to HTML; original preserved.";return XmlPackageText(bytes,"content.xml");}
            if(ext==".rtf")
            {
                var raw=Decode(bytes);
                raw=Regex.Replace(raw,@"\\'[0-9a-fA-F]{2}",m=>{try{return ((char)Convert.ToByte(m.Value[2..],16)).ToString();}catch{return ""; }});
                raw=Regex.Replace(raw,@"\\[a-zA-Z]+-?\d* ?"," ");
                note="RTF controls removed; readable text preserved.";
                return Limit(Collapse(raw.Replace("{","").Replace("}","")));
            }
            if(TextExtensions.Contains(ext))
            {
                var raw=Decode(bytes);
                if(ext is ".html" or ".htm" or ".xhtml")
                {
                    raw=Regex.Replace(raw,@"<script\b[^>]*>[\s\S]*?</script>"," ",RegexOptions.IgnoreCase);
                    raw=Regex.Replace(raw,@"<style\b[^>]*>[\s\S]*?</style>"," ",RegexOptions.IgnoreCase);
                    raw=WebUtility.HtmlDecode(Regex.Replace(raw,@"<[^>]+>"," "));
                    note="Executable HTML removed; readable text preserved.";
                }
                return Limit(Collapse(raw));
            }
            if(LegacyTextExtensions.Contains(ext))
            {
                note="Legacy binary document: printable text recovered where possible; original preserved.";
                return Limit(PrintableStrings(bytes));
            }
            if(ProgramExtensions.Contains(ext)&&!LooksBinary(bytes))
            {
                note="Program source represented as text; execution remains quarantined.";
                return Limit(Collapse(Decode(bytes)));
            }
        }
        catch(Exception ex){note="Text extraction safely failed: "+ex.Message;}
        return "";
    }

    static string XmlPackageText(byte[] bytes,string member)
    {
        using var ms=new MemoryStream(bytes,false);
        using var zip=new ZipArchive(ms,ZipArchiveMode.Read,false);
        var entry=zip.GetEntry(member)??throw new InvalidDataException($"{member} is missing.");
        using var reader=new StreamReader(entry.Open(),Encoding.UTF8,true);
        var doc=XDocument.Parse(reader.ReadToEnd(),LoadOptions.PreserveWhitespace);
        var sb=new StringBuilder();
        foreach(var node in doc.Descendants())
        {
            var n=node.Name.LocalName;
            if(n=="t")sb.Append(node.Value);
            else if(n=="tab")sb.Append('\t');
            else if(n is "br" or "line-break" or "p")sb.AppendLine();
        }
        return Limit(Collapse(sb.ToString()));
    }

    static string AnalyzeProgram(byte[] bytes,string ext)
    {
        if(LooksBinary(bytes))
            return "Quarantined binary. Not executed. Preserved for a future no-network, resource-limited Legacy sandbox.";

        var source=Decode(bytes);
        var hints=new List<string>();
        foreach(var (pattern,label) in new (string,string)[]
        {
            (@"\b(input|read|readln|scanf|gets|stdin|console\.read)\b","input"),
            (@"\b(print|println|printf|write|writeln|stdout|console\.write)\b","output"),
            (@"\b(open|fopen|ifstream|ofstream|streamreader|streamwriter)\b","file I/O"),
            (@"\b(socket|http|ftp|telnet|winsock|curl|wget)\b","network reference")
        })
            if(Regex.IsMatch(source,pattern,RegexOptions.IgnoreCase))hints.Add(label);

        var names=Regex.Matches(source,@"['""]([^'""]+\.(?:txt|dat|csv|db|sav|ini|cfg|map|bin|json|xml))['""]",RegexOptions.IgnoreCase)
            .Select(m=>m.Groups[1].Value).Distinct(StringComparer.OrdinalIgnoreCase).Take(10).ToArray();

        var summary="Quarantined source. Not executed. Static I/O hints: "+(hints.Count==0?"none detected":string.Join(", ",hints.Distinct()))+".";
        if(names.Length>0)summary+=" Referenced files: "+string.Join(", ",names)+".";
        return summary;
    }

    static string RepresentationHtml(string world,string path,string category,string suggested,string sha,long size,string text,string analysis,string assetKey)
    {
        var body=string.IsNullOrWhiteSpace(text)
            ?"<p class=\"empty\">No readable text representation was extracted. The original file is still preserved.</p>"
            :"<pre>"+WebUtility.HtmlEncode(text)+"</pre>";
        return "<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>"
            +WebUtility.HtmlEncode(Path.GetFileName(path))
            +"</title><style>body{margin:0;padding:24px;background:#071017;color:#e8dfc8;font:15px/1.55 system-ui}main{max-width:980px;margin:auto}small{color:#78c8ef;font-weight:900;letter-spacing:.08em}h1{color:#f0d58c;font:700 28px/1.1 Georgia}code,pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#0d1820;border:1px solid #30444e;border-radius:10px;padding:14px;color:#e9edf0}dl{display:grid;grid-template-columns:max-content 1fr;gap:5px 10px}dt{color:#8fb3c5;font-weight:800}dd{margin:0}.analysis{border-left:3px solid #8f7136;padding:10px 12px;background:#10170f}.empty{color:#a9b7bd}</style></head><body><main><small>RIST LEGACY · "
            +WebUtility.HtmlEncode(category)+"</small><h1>"+WebUtility.HtmlEncode(Path.GetFileName(path))
            +"</h1><dl><dt>World</dt><dd>"+WebUtility.HtmlEncode(world)
            +"</dd><dt>Archive path</dt><dd><code>"+WebUtility.HtmlEncode(path)
            +"</code></dd><dt>Suggested RIST location</dt><dd>"+WebUtility.HtmlEncode(suggested)
            +"</dd><dt>Size</dt><dd>"+size.ToString("N0")
            +" bytes</dd><dt>SHA-256</dt><dd><code>"+sha
            +"</code></dd>"+(string.IsNullOrWhiteSpace(assetKey)?"":"<dt>My Assets</dt><dd><code>"+WebUtility.HtmlEncode(assetKey)+"</code></dd>")
            +"</dl>"+(string.IsNullOrWhiteSpace(analysis)?"":"<p class=\"analysis\">"+WebUtility.HtmlEncode(analysis)+"</p>")+body+"</main></body></html>";
    }

    static string NavigatorHtml(LegacyArchiveManifest manifest,string baseUri)
    {
        var sb=new StringBuilder("<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Legacy TOC</title><style>body{background:#071017;color:#e8dfc8;font:14px/1.4 system-ui;padding:20px}h1{color:#f0d58c}.e{display:block;padding:7px 9px;margin:2px 0;border:1px solid #263943;border-radius:7px;color:#dfe9ed;text-decoration:none;background:#0b151b}.m{color:#80b8d4;font-size:10px}</style></head><body>");
        sb.Append("<h1>").Append(WebUtility.HtmlEncode(manifest.WorldName)).Append(" · Legacy</h1>");
        foreach(var entry in manifest.Files)
        {
            var depth=entry.Path.Count(ch=>ch=='/');
            sb.Append("<a class=\"e\" style=\"margin-left:").Append(Math.Min(120,depth*12)).Append("px\" href=\"")
              .Append(WebUtility.HtmlEncode(LegacyEntryUrl(baseUri,manifest.WorldId,entry.Id))).Append("\">")
              .Append(WebUtility.HtmlEncode(entry.Name)).Append(" <span class=\"m\">· ")
              .Append(WebUtility.HtmlEncode(entry.Category)).Append(" · ")
              .Append(WebUtility.HtmlEncode(entry.SuggestedLocation)).Append("</span></a>");
        }
        return sb.Append("</body></html>").ToString();
    }

    static byte[] BinderPdf(LegacyArchiveManifest manifest,string baseUri)
    {
        const int perPage=40;
        var pages=Math.Max(1,(int)Math.Ceiling(manifest.Files.Count/(double)perPage));
        var objects=new List<string>{"","","<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"};
        int Add(string value){objects.Add(value);return objects.Count;}
        var pageIds=new List<int>();

        for(var p=0;p<pages;p++)
        {
            var lines=manifest.Files.Skip(p*perPage).Take(perPage).ToList();
            var stream=new StringBuilder();
            stream.Append("BT /F1 16 Tf 38 758 Td (").Append(Pdf(manifest.WorldName+" - LEGACY")).Append(") Tj ET\n");
            stream.Append("BT /F1 8 Tf 38 742 Td (").Append(Pdf("Source: "+manifest.SourceArchiveName)).Append(") Tj ET\n");
            var annots=new List<int>();
            for(var i=0;i<lines.Count;i++)
            {
                var e=lines[i];
                var y=716-i*16;
                var depth=Math.Min(7,e.Path.Count(ch=>ch=='/'));
                var label=new string(' ',depth*2)+e.Name+" ["+e.Category+"]";
                stream.Append("BT /F1 9 Tf ").Append(40+depth*7).Append(' ').Append(y).Append(" Td (").Append(Pdf(label)).Append(") Tj ET\n");
                var url=LegacyEntryUrl(baseUri,manifest.WorldId,e.Id);
                annots.Add(Add($"<< /Type /Annot /Subtype /Link /Rect [36 {y-3} 576 {y+10}] /Border [0 0 0] /A << /S /URI /URI ({Pdf(url)}) >> >>"));
            }
            var content=stream.ToString();
            var contentId=Add($"<< /Length {Encoding.ASCII.GetByteCount(content)} >>\nstream\n{content}endstream");
            var a=annots.Count==0?"":"/Annots ["+string.Join(' ',annots.Select(x=>$"{x} 0 R"))+"]";
            pageIds.Add(Add($"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {contentId} 0 R {a} >>"));
        }

        objects[0]="<< /Type /Catalog /Pages 2 0 R >>";
        objects[1]=$"<< /Type /Pages /Kids [{string.Join(' ',pageIds.Select(x=>$"{x} 0 R"))}] /Count {pageIds.Count} >>";

        using var ms=new MemoryStream();
        void Write(string s){var bytes=Encoding.ASCII.GetBytes(s);ms.Write(bytes,0,bytes.Length);}
        Write("%PDF-1.4\n%RISTLEGACY\n");
        var offsets=new long[objects.Count+1];
        for(var i=0;i<objects.Count;i++){offsets[i+1]=ms.Position;Write($"{i+1} 0 obj\n{objects[i]}\nendobj\n");}
        var xref=ms.Position;
        Write($"xref\n0 {objects.Count+1}\n0000000000 65535 f \n");
        for(var i=1;i<=objects.Count;i++)Write($"{offsets[i]:D10} 00000 n \n");
        Write($"trailer\n<< /Size {objects.Count+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF");
        return ms.ToArray();
    }

    static string LegacyEntryUrl(string baseUri,string worldId,string entryId)
    {
        var root=string.IsNullOrWhiteSpace(baseUri)?"https://relicgamemaster.com/":baseUri;
        if(!root.EndsWith('/'))root+="/";
        return root+"legacy/index.html?world="+Uri.EscapeDataString(worldId)+"&entry="+Uri.EscapeDataString(entryId);
    }

    static string NormalizePath(string raw)
    {
        raw=(raw??"").Replace('\\','/').Trim();
        if(raw.StartsWith('/')||Regex.IsMatch(raw,@"^[A-Za-z]:"))throw new InvalidDataException("Archive contains an absolute path.");
        var parts=raw.Split('/',StringSplitOptions.RemoveEmptyEntries);
        if(parts.Any(x=>x is "." or ".."))throw new InvalidDataException("Archive contains an unsafe relative path.");
        return string.Join('/',parts);
    }

    static bool IsDirectory(ZipArchiveEntry e)=>e.FullName.EndsWith('/')||string.IsNullOrEmpty(e.Name);
    static string Parent(string path){var at=path.LastIndexOf('/');return at<0?"":path[..at];}
    static string IdFor(string path)=>Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(path)).AsSpan(0,8)).ToLowerInvariant();
    static string SafeStoragePath(string path)=>string.Join('/',path.Split('/').Select(SafeSegment));
    static string SafeSegment(string value){var s=Regex.Replace((value??"").Trim(),@"[^A-Za-z0-9._ -]+","_").Trim(' ','.');return string.IsNullOrWhiteSpace(s)?"unnamed":s.Length>120?s[..120]:s;}
    static string Limit(string value)=>value.Length>250_000?value[..250_000]+"\n\n[Representation truncated; original preserved.]":value;
    static string Collapse(string value){value=value.Replace("\r\n","\n").Replace('\r','\n');value=Regex.Replace(value,@"[\t ]+"," ");value=Regex.Replace(value,@"\n{4,}","\n\n\n");return value.Trim();}
    static string Decode(byte[] bytes){if(bytes.Length>=2&&bytes[0]==0xff&&bytes[1]==0xfe)return Encoding.Unicode.GetString(bytes);if(bytes.Length>=3&&bytes[0]==0xef&&bytes[1]==0xbb&&bytes[2]==0xbf)return Encoding.UTF8.GetString(bytes,3,bytes.Length-3);try{return new UTF8Encoding(false,true).GetString(bytes);}catch{return Encoding.Latin1.GetString(bytes);}}
    static bool LooksBinary(byte[] bytes){var n=Math.Min(bytes.Length,8192);if(n==0)return false;var zero=0;var control=0;for(var i=0;i<n;i++){var b=bytes[i];if(b==0)zero++;else if(b<9||(b>13&&b<32))control++;}return zero>n/50||control>n/8;}
    static string PrintableStrings(byte[] bytes){var sb=new StringBuilder();var run=new StringBuilder();foreach(var b in bytes.Take(2_000_000)){if(b is >=32 and <=126||b is 9 or 10 or 13)run.Append((char)b);else{if(run.Length>=4)sb.AppendLine(run.ToString());run.Clear();}if(sb.Length>250_000)break;}if(run.Length>=4)sb.AppendLine(run.ToString());return sb.ToString();}
    static string Pdf(string value){var ascii=new string((value??"").Select(ch=>ch is >= ' ' and <= '~'?ch:'?').ToArray());return ascii.Replace("\\","\\\\").Replace("(","\\(").Replace(")","\\)");}
    static string ContentType(string ext)=>ext switch{".png"=>"image/png",".jpg" or ".jpeg"=>"image/jpeg",".gif"=>"image/gif",".webp"=>"image/webp",".bmp"=>"image/bmp",".pdf"=>"application/pdf",".json"=>"application/json",".xml"=>"application/xml",".html" or ".htm"=>"text/html",".csv"=>"text/csv",".txt" or ".md" or ".log"=>"text/plain",".zip"=>"application/zip",".mp3"=>"audio/mpeg",".wav"=>"audio/wav",".ogg"=>"audio/ogg",".mp4"=>"video/mp4",_=>"application/octet-stream"};
}
