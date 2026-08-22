using System.Net.Http.Json;
using Microsoft.JSInterop;

namespace RistWorld;

public sealed partial class WorldSession(HttpClient http, IJSRuntime js)
{
    private const string SaveKey = "rist.world.blazor.v2";
    public event Action? Changed;
    public List<AtlasTile> AtlasTiles { get; } = [];
    public List<CardItem> Cards { get; } = [];
    public List<PieceItem> Pieces { get; private set; } = [];
    public List<TileItem> PlacedTiles { get; private set; } = [];
    public List<StagedAsset> StagedAssets { get; } = [];
    public List<RollItem> Rolls { get; } = [];
    public List<GemItem> Gems { get; } = [];
    public List<HandCard> HandCards { get; } = [];
    public HandCard? EditingHandCard { get; private set; }
    public string? DraggedDieKey { get; private set; }

    public string WorldMapUrl { get; } = "";
    public string MapName { get; private set; } = "Shaelvien";
    public IReadOnlyList<DiceSpec> DiceSet { get; } =
    [
        new("d4", "D4", "assets/dice/d4.png", 4, 8, 1, 8, 4, VisualAspect:1.06),
        new("d5-bonus", "+D5", "assets/dice/d5-bonus.png", 5, 10, 1, 10, 8, VisualAspect:.77),
        new("d5-penalty", "-D5", "assets/dice/d5-penalty.png", 5, 10, 1, 10, 8, 1, -1, .73),
        new("d6", "D6", "assets/dice/d6.png", 6, 12, 1, 12, 10, VisualAspect:.83),
        new("d8", "D8", "assets/dice/d8.png", 8, 16, 1, 16, 14, VisualAspect:.92),
        new("d10", "D10", "assets/dice/d10.png", 10, 10, 2, 20, 18, 0, 1, .87),
        new("d10-inverse", "D10 dark", "assets/dice/d10-inverse.png", 10, 10, 2, 20, 18, 0, 1, .88),
        new("d12", "D12", "assets/dice/d12.png", 12, 12, 2, 24, 22, VisualAspect:.92),
        new("d20", "D20", "assets/dice/d20.png", 20, 10, 4, 40, 38, VisualAspect:.79)
    ];

    public int BonusD5Value { get; set; } = 1;
    public int PenaltyD5Value { get; set; } = 1;
    public bool MixerOpen { get; set; }
    public bool CharacterEditMode { get; private set; } = true;
    public string CharacterName { get; set; } = "";
    public string CharacterSpecies { get; set; } = "";
    public string CharacterAge { get; set; } = "";
    public string CharacterAlignment { get; set; } = "";
    public string CharacterDescription { get; set; } = "";
    public string CharacterBackground { get; set; } = "";
    public string CharacterNotes { get; set; } = "";
    public string CharacterTab { get; set; } = "Description";
    public string FieldSearch { get; set; } = "";
    public List<CharacterField> CharacterFields { get; } = [];
    public IReadOnlyList<CharacterFieldOption> FieldVocabulary { get; } =
    [
        new("Health","POOL","Pools"), new("HP","POOL","Pools"), new("Hit Points","POOL","Pools"), new("Vitality","POOL","Pools"), new("Life","POOL","Pools"), new("Wounds","POOL","Pools"), new("Stamina","POOL","Pools"), new("Endurance","POOL","Pools"), new("Mana","POOL","Pools"), new("MP","POOL","Pools"), new("Spell Points","POOL","Pools"), new("Sanity","POOL","Pools"), new("Resolve","POOL","Pools"), new("Morale","POOL","Pools"), new("Luck","POOL","Pools"),
        new("Strength","VALUE","Skills"), new("Dexterity","VALUE","Skills"), new("Constitution","VALUE","Skills"), new("Intelligence","VALUE","Skills"), new("Wisdom","VALUE","Skills"), new("Charisma","VALUE","Skills"), new("Perception","VALUE","Skills"), new("Knowledge","VALUE","Skills"), new("Athletics","VALUE","Skills"), new("Acrobatics","VALUE","Skills"), new("Swim","VALUE","Skills"), new("Stealth","VALUE","Skills"), new("Insight","VALUE","Skills"), new("Survival","VALUE","Skills"), new("Craft","VALUE","Skills"), new("Investigation","VALUE","Skills"), new("Persuasion","VALUE","Skills"), new("Deception","VALUE","Skills"), new("Intimidation","VALUE","Skills"), new("Initiative","VALUE","Skills"), new("Defense","VALUE","Skills"), new("Armor","VALUE","Skills"), new("Armor Class","VALUE","Skills"),
        new("Feat","ABILITY","Feats"), new("Talent","ABILITY","Feats"), new("Trait","ABILITY","Feats"), new("Ability","ABILITY","Feats"), new("Power","ABILITY","Feats"), new("Advantage","ABILITY","Feats"), new("Disadvantage","ABILITY","Feats"), new("Feature","ABILITY","Feats")
    ];
    public IEnumerable<CharacterFieldOption> FilteredFieldVocabulary => FieldVocabulary.Where(x => string.IsNullOrWhiteSpace(FieldSearch) || x.Name.Contains(FieldSearch,StringComparison.OrdinalIgnoreCase)).Take(12);

    public List<MixerChannel> MixerChannels { get; } = [new("Knowledge",0,20),new("Swim",0,20),new("Perception",0,20),new("Athletics",0,20),new("Stealth",0,20),new("Insight",0,20),new("Survival",0,20),new("Craft",0,20)];

    public string SelectedTile { get; set; } = "";
    public bool TileBrowserOpen { get; private set; }
    public string PieceKind { get; set; } = "mini";
    public string Role { get; set; } = "GM";
    public bool IsLoggedIn { get; private set; } = true;
    public bool CanManageCurrentMap => IsLoggedIn;
    public bool SaveMenuOpen { get; private set; }
    public bool LoadMenuOpen { get; private set; }
    public bool HeaderPinDragging { get; private set; }
    public string GridStyle { get; set; } = "square";
    public string DistanceUnit { get; private set; } = "mi";
    public const int GridColumns = 20;
    public const int GridRows = 13;
    public int GridDiameter { get; set; } = 48;
    public double GridDistance { get; set; } = 5;
    public double GridCalibrationZoom { get; set; } = 1;
    public double ViewZoom { get; set; } = 1;
    public double GridCellWidthPercent => 100.0 / GridColumns;
    public double GridCellHeightPercent => 100.0 / GridRows;
    public double EffectiveGridDistance => GridDistance * GridCalibrationZoom / Math.Max(ViewZoom, 0.01);
    public string EffectiveGridUnit => DistanceUnit;
    public string Mode { get; set; } = "piece";
    public CardItem? OpenCard { get; set; }
    public int Total => Rolls.Sum(x => x.Key == "d10-inverse" ? x.Value * 10 : x.Value) + Gems.Sum(x => x.Value);
    public void Notify() => Changed?.Invoke();
    public void ToggleTileBrowser(){TileBrowserOpen=!TileBrowserOpen;Notify();}
    public void ToggleLogin(){IsLoggedIn=!IsLoggedIn;if(!IsLoggedIn)Role="PC";CloseHeaderMenus();Notify();}
    public void ToggleSaveMenu(){SaveMenuOpen=!SaveMenuOpen;LoadMenuOpen=false;Notify();}
    public void ToggleLoadMenu(){LoadMenuOpen=!LoadMenuOpen;SaveMenuOpen=false;Notify();}
    public void CloseHeaderMenus(){SaveMenuOpen=false;LoadMenuOpen=false;}
    public void BeginHeaderPinDrag(){HeaderPinDragging=true;}
    public void EndHeaderPinDrag(){HeaderPinDragging=false;}
    public void PlaceHeaderPin(double x,double y){if(!HeaderPinDragging)return;Pieces.Add(new("pin",Math.Clamp(x,0,1),Math.Clamp(y,0,1),Math.Max(ViewZoom,.01)));HeaderPinDragging=false;Notify();}
    public void CalibrateGrid(){GridDistance=Math.Max(.01,GridDistance);GridCalibrationZoom=Math.Max(.01,ViewZoom);Notify();}

    public void OpenMixer(){MixerOpen=true;Notify();}
    public void CloseMixer(){MixerOpen=false;EditingHandCard=null;DraggedDieKey=null;Notify();}
    public void EditCharacter(){CharacterEditMode=true;Notify();}
    public void OpenCharacterEditMode()=>EditCharacter();
    public void SaveCharacter(){CharacterEditMode=false;EditingHandCard=null;DraggedDieKey=null;Notify();}
    public void SetCharacterTab(string tab){CharacterTab=tab;Notify();}
    public void SetFieldSearch(string value){FieldSearch=value;Notify();}
    public void AddCharacterField(CharacterFieldOption option){if(CharacterFields.Any(x=>x.Name.Equals(option.Name,StringComparison.OrdinalIgnoreCase)))return;CharacterFields.Add(new(option.Name,option.Kind,option.Group));FieldSearch="";Notify();}
    public void AddCustomCharacterField(){var name=FieldSearch.Trim();if(name.Length==0||CharacterFields.Any(x=>x.Name.Equals(name,StringComparison.OrdinalIgnoreCase)))return;var kind=CharacterTab=="Pools"?"POOL":CharacterTab=="Skills"?"VALUE":"ABILITY";CharacterFields.Add(new(name,kind,CharacterTab));FieldSearch="";Notify();}
    public void AddBlankCharacterField(string group){if(!CharacterEditMode)return;var kind=group=="Pools"?"POOL":group=="Skills"?"VALUE":"ABILITY";var prefix=group=="Pools"?"Pool":group=="Skills"?"Skill":"Feat";var n=1;var name=$"{prefix} {n}";while(CharacterFields.Any(x=>x.Name.Equals(name,StringComparison.OrdinalIgnoreCase)))name=$"{prefix} {++n}";CharacterFields.Add(new(name,kind,group));Notify();}
    public void RenameCharacterField(CharacterField field,string name){if(!CharacterEditMode)return;name=name.Trim();if(name.Length==0)return;field.Name=name;Notify();}
    public void SetCharacterFieldColor(CharacterField field,string color){if(!CharacterEditMode)return;field.Color=color switch{"red" or "orange" or "gold" or "green" or "teal" or "blue" or "purple"=>color,_=>"gold"};Notify();}
    public void SetFieldColor(CharacterField field,string color){if(!CharacterEditMode)return;field.Color=color;Notify();}
    public void RemoveCharacterField(CharacterField field){if(!CharacterEditMode)return;CharacterFields.Remove(field);HandCards.RemoveAll(x=>ReferenceEquals(x.Field,field));if(EditingHandCard is not null&&ReferenceEquals(EditingHandCard.Field,field))EditingHandCard=null;Notify();}
    public void DeleteCharacterControl(CharacterField field)=>RemoveCharacterField(field);
    public void SetCharacterField(CharacterField field,int current,int? max=null){if(!CharacterEditMode)return;field.Max=Math.Clamp(max??field.Max,0,999);field.Current=Math.Clamp(current,0,field.Kind=="POOL"?Math.Max(field.Max,0):999);Notify();}
    public void TurnCharacterDial(CharacterField field,int delta){if(!CharacterEditMode)return;var max=Math.Max(field.Max,0);var next=Math.Clamp(field.Current+delta,0,field.Kind=="POOL"?max:999);field.Current=next;Notify();}
    public void SetMixerChannel(string name,int current,int max){var channel=MixerChannels.FirstOrDefault(x=>x.Name==name);if(channel is null)return;max=Math.Clamp(max,0,999);current=Math.Clamp(current,0,max);channel.Current=current;channel.Max=max;Notify();}

    public void ShowHand(CharacterField field){if(field.Kind is not("VALUE" or "ABILITY")||HandCards.Any(x=>ReferenceEquals(x.Field,field)))return;HandCards.Add(new HandCard(field){ApprovalStatus=Role=="GM"?HandCard.Approved:HandCard.Pending});Notify();}
    public void HideHand(HandCard card){HandCards.Remove(card);if(ReferenceEquals(EditingHandCard,card))EditingHandCard=null;Notify();}
    public void MoveHandCard(HandCard card,int delta){var from=HandCards.IndexOf(card);if(from<0)return;var to=Math.Clamp(from+delta,0,HandCards.Count-1);if(to==from)return;HandCards.RemoveAt(from);HandCards.Insert(to,card);Notify();}
    public void EditDiceBag(HandCard card){if(MixerOpen&&!CharacterEditMode)return;EditingHandCard=card;Notify();}
    public void CloseDiceBag(){EditingHandCard=null;DraggedDieKey=null;Notify();}
    public void AddDiceBagEntry(string dieKey){if(EditingHandCard is null||Dice(dieKey) is null)return;EditingHandCard.DiceBag.Add(new(dieKey));Notify();}
    public void RemoveDiceBagEntry(DiceBagEntry entry){EditingHandCard?.DiceBag.Remove(entry);Notify();}
    public void SetDiceBagCount(DiceBagEntry entry,int count){entry.Count=Math.Clamp(count,1,20);Notify();}
    public void SetDiceBagMagnitude(DiceBagEntry entry,int magnitude){entry.SelectedMagnitude=Math.Clamp(magnitude,1,5);Notify();}
    public void BeginDiceDrag(string dieKey){DraggedDieKey=Dice(dieKey) is null?null:dieKey;Notify();}
    public void DropDraggedDieIntoBag(){if(DraggedDieKey is null||EditingHandCard is null)return;AddDiceBagEntry(DraggedDieKey);DraggedDieKey=null;Notify();}
    public void DropBagEntryOutside(DiceBagEntry entry){if(EditingHandCard is null)return;EditingHandCard.DiceBag.Remove(entry);Notify();}
    public async Task RollHandCardAsync(HandCard card){if(Role=="PC"&&!CanPlay(card))return;if(MixerOpen&&CharacterEditMode){EditDiceBag(card);return;}if(card.DiceBag.Count==0){EditDiceBag(card);return;}var tasks=new List<Task>();foreach(var entry in card.DiceBag){for(var i=0;i<entry.Count;i++){var selected=entry.DieKey is "d5-bonus" or "d5-penalty"?entry.SelectedMagnitude:(int?)null;tasks.Add(RollAsync(entry.DieKey,selected));}}await Task.WhenAll(tasks);}

    public void SetDistanceUnit(string unit){if(EncounterActive)return;unit=unit switch{"mi" or "km" or "m" or "yd" or "ft"=>unit,_=>DistanceUnit};if(unit==DistanceUnit)return;var meters=GridDistance*MetersPerUnit(DistanceUnit);GridDistance=meters/MetersPerUnit(unit);DistanceUnit=unit;Notify();}
    static double MetersPerUnit(string unit)=>unit switch{"mi"=>1609.344,"km"=>1000.0,"m"=>1.0,"yd"=>.9144,"ft"=>.3048,_=>1.0};
    public async Task InitializeAsync(){await LoadAtlasAsync();if(!await TryLoadSavedMapAsync())BuildShaelvienPangaea();await LoadCardsAsync();Notify();}
    void BuildShaelvienPangaea()
    {
        if(PlacedTiles.Count>0)return;

        // The World remains a 20x13 navigation grid, but the default terrain is
        // authored as though it were placed at 4x zoom. Each world square can
        // therefore contain sixteen independently editable detail tiles.
        const int detailZoom=4;
        string[] pangea=
        [
            "....CCCCCCCCCC......",
            "..CCIIIMMMDDDDCC....",
            ".CIIIIVMMMHHDDDDCC..",
            "CIIIIVVMMMMHHDDDDCC.",
            "CJJJFFMMMMHPPPDDDDDC",
            "CJJJJFFFFRRPPPPDDDDC",
            "CJJJJFFFRRPPPPHHHHCC",
            ".CJJJSSFFRRPPPPHHHHC",
            "..CJJSSFFRRPPHHHHICC",
            "...CJJSSFFWPPHHIIIIC",
            "....CFFFWWHPPHIIIIC.",
            ".....CCPPWHHHIIICC..",
            ".......CCCCC.CC....."
        ];

        for(var baseRow=0;baseRow<pangea.Length;baseRow++)
        {
            for(var baseColumn=0;baseColumn<pangea[baseRow].Length;baseColumn++)
            {
                var baseCode=pangea[baseRow][baseColumn];
                if(baseCode=='.')continue;

                for(var subRow=0;subRow<detailZoom;subRow++)
                {
                    for(var subColumn=0;subColumn<detailZoom;subColumn++)
                    {
                        if(IsRoundedOceanCorner(pangea,baseColumn,baseRow,subColumn,subRow,detailZoom))continue;

                        var fineColumn=baseColumn*detailZoom+subColumn;
                        var fineRow=baseRow*detailZoom+subRow;
                        var code=DetailedPangeaTerrain(pangea,baseColumn,baseRow,subColumn,subRow,detailZoom);
                        var terrain=PangeaTerrain(code);
                        var atlasNumber=PangeaAtlasNumber(code,fineColumn,fineRow);
                        var sourceRow=(fineRow*2+fineColumn)%6+1;
                        var sourceColumn=(fineColumn*3+fineRow)%6+1;
                        var id=$"aws-{terrain}-{atlasNumber}-{sourceRow:00}-{sourceColumn:00}";
                        var tile=AtlasTiles.FirstOrDefault(x=>x.Id==id);
                        if(tile is null)continue;

                        var region=PangeaRegion(baseColumn,baseRow);
                        PlacedTiles.Add(new(tile.Id,$"Shaelvien · {region} · {terrain}",tile.Image,
                            fineColumn/(double)(GridColumns*detailZoom),
                            fineRow/(double)(GridRows*detailZoom),
                            tile.SourceWidth,tile.SourceHeight,tile.CropX,tile.CropY,tile.CropWidth,tile.CropHeight,
                            detailZoom));
                    }
                }
            }
        }
    }

    static bool IsRoundedOceanCorner(string[] map,int column,int row,int subColumn,int subRow,int detailZoom)
    {
        var left=column==0||map[row][column-1]=='.';
        var right=column==map[row].Length-1||map[row][column+1]=='.';
        var up=row==0||map[row-1][column]=='.';
        var down=row==map.Length-1||map[row+1][column]=='.';
        return (subColumn==0&&subRow==0&&left&&up)
            || (subColumn==detailZoom-1&&subRow==0&&right&&up)
            || (subColumn==0&&subRow==detailZoom-1&&left&&down)
            || (subColumn==detailZoom-1&&subRow==detailZoom-1&&right&&down);
    }

    static char DetailedPangeaTerrain(string[] map,int column,int row,int subColumn,int subRow,int detailZoom)
    {
        var code=map[row][column];
        if(code=='C')return 'C';

        // Pull coast detail one micro-cell into exposed land edges.
        if(subColumn==0&&(column==0||map[row][column-1]=='.'))return 'C';
        if(subColumn==detailZoom-1&&(column==map[row].Length-1||map[row][column+1]=='.'))return 'C';
        if(subRow==0&&(row==0||map[row-1][column]=='.'))return 'C';
        if(subRow==detailZoom-1&&(row==map.Length-1||map[row+1][column]=='.'))return 'C';

        // Small deterministic transition details break up large biome blocks
        // while keeping the approved continental geography readable at 1x.
        var seed=column*31+row*17+subColumn*7+subRow*13;
        if(code=='P'&&seed%11==0)return 'H';
        if(code=='F'&&seed%13==0)return 'P';
        if(code=='J'&&seed%17==0)return 'S';
        if(code=='D'&&seed%19==0)return 'H';
        if(code=='M'&&seed%13==0)return 'V';
        if(code=='H'&&seed%17==0)return 'P';
        return code;
    }

    static string PangeaTerrain(char code)=>code switch
    {
        'C'=>"coast",'I'=>"ice",'V'=>"volcano",'M'=>"mountains",
        'D'=>"desert",'J'=>"jungle",'F'=>"forest",'H'=>"hills",
        'P'=>"plains",'R'=>"rivers",'S'=>"swamp",'W'=>"vent-fields",
        _=>"plains"
    };

    static string PangeaAtlasNumber(char code,int column,int row)=>code switch
    {
        'C'=>"066",'I'=>"021",'V'=>"020",'M'=>"022",'D'=>"024",
        'J'=>(column+row)%2==0?"026":"027",
        'F'=>"028",'H'=>"023",'R'=>"017",'S'=>"025",
        'W'=>(1+(column+row)%11).ToString("000"),
        'P'=>(29+(column+row*2)%32).ToString("000"),
        _=>"029"
    };

    static string PangeaRegion(int column,int row)
    {
        if(row<=3&&column<=6)return "Ice Crown";
        if(row<=4&&column is >=6 and <=12)return "Crownspine";
        if(row<=6&&column>=13)return "Sunward Expanse";
        if(row>=4&&column<=5)return "Amazon Crown";
        if(row>=8&&column>=14)return "Southeastern Ice";
        if(row>=8&&column is >=8 and <=12)return "Emberfall";
        if(column is >=7 and <=12&&row is >=4 and <=8)return "Endemar";
        return "Pangean Interior";
    }

    async Task LoadAtlasAsync()
    {
        var builtIn=await http.GetFromJsonAsync<List<AtlasTile>>("data/atlas-public.json");
        if(builtIn is not null)AtlasTiles.AddRange(builtIn);
        var drive=await http.GetFromJsonAsync<List<AtlasTile>>("assets/drive-tiles/catalog.json");
        if(drive is not null)AtlasTiles.AddRange(drive.Where(x=>AtlasTiles.All(existing=>existing.Id!=x.Id)));
    }
    async Task LoadCardsAsync(){var rows=await http.GetFromJsonAsync<List<CardItem>>("data/cards-public.json");if(rows is not null)Cards.AddRange(rows);}
    public DiceSpec? Dice(string key)=>DiceSet.FirstOrDefault(x=>x.Key==key);
    public Task RollAsync(string key)=>RollAsync(key,null);
    private (double X,double Y) OpenRollPosition(){const double min=.16,max=.84,clearanceX=.10,clearanceY=.16;var best=(X:.5,Y:.5);var bestScore=-1.0;for(var attempt=0;attempt<160;attempt++){var x=min+Random.Shared.NextDouble()*(max-min);var y=min+Random.Shared.NextDouble()*(max-min);var score=Rolls.Count==0?double.MaxValue:Rolls.Min(roll=>{var dx=(x-roll.X)/clearanceX;var dy=(y-roll.Y)/clearanceY;return dx*dx+dy*dy;});if(score>=1)return(x,y);if(score>bestScore){bestScore=score;best=(x,y);}}return best;}
    private static int FinalFrameForValue(DiceSpec die,int value)
    {
        var magnitude=Math.Abs(value);
        if(die.Key=="d4")return magnitude switch{1=>0,2=>6,3=>2,4=>4,_=>0};
        var frameValue=die.ValueOffset==0?magnitude:magnitude-1;
        return Math.Clamp(frameValue*2,0,die.FrameCount-1);
    }
    private static int ValueForFrame(DiceSpec die,int frame)
    {
        if(die.Key=="d4")return (frame/2) switch{0=>1,1=>3,2=>4,3=>2,_=>1};
        return (frame/2+die.ValueOffset)*die.Sign;
    }
    public async Task RollAsync(string key,int? selectedMagnitude){var die=Dice(key);if(die is null)return;var (x,y)=OpenRollPosition();var initialFrame=Random.Shared.Next(die.FrameCount);var item=new RollItem(die.Key,die.Label,ValueForFrame(die,initialFrame),initialFrame,x,y);Rolls.Add(item);Notify();var steps=Random.Shared.Next(13,23);for(var n=0;n<steps;n++){var i=Rolls.IndexOf(item);if(i<0)return;var frame=(item.Frame+1)%die.FrameCount;item=item with{Value=ValueForFrame(die,frame),Frame=frame};Rolls[i]=item;Notify();await Task.Delay(52+Math.Min(n*3,34));}var magnitude=selectedMagnitude.HasValue&&(die.Key is "d5-bonus" or "d5-penalty")?Math.Clamp(selectedMagnitude.Value,1,5):(die.ValueOffset==0?Random.Shared.Next(die.Sides):Random.Shared.Next(1,die.Sides+1));var value=magnitude*die.Sign;var finalFrame=FinalFrameForValue(die,value);var finalIndex=Rolls.IndexOf(item);if(finalIndex>=0)Rolls[finalIndex]=item with{Value=value,Frame=finalFrame};Notify();}
    public void StagePiece(string kind){if(kind is not("mini" or "rolling-stock" or "pawn" or "pin" or "terrain" or "bit"))return;var name=kind switch{"mini"=>"Miniature","rolling-stock"=>"Rolling Stock","pawn"=>"Pawn / Meeple","pin"=>"Token / Chit","terrain"=>"Scenery / Terrain","bit"=>"Bit",_=>"Asset"};var key=$"piece:{kind}";if(StagedAssets.All(x=>x.Key!=key))StagedAssets.Add(new(key,kind,name,ApprovalStatus:Role=="GM"?HandCard.Approved:HandCard.Pending));Notify();}
    public void StageSelectedTile(){if(Role!="GM"||string.IsNullOrWhiteSpace(SelectedTile))return;var tile=AtlasTiles.FirstOrDefault(t=>t.Id==SelectedTile);if(tile is null)return;StageTile(tile);}
    public void StageTile(AtlasTile tile){var key=$"tile:{tile.Id}";if(StagedAssets.All(x=>x.Key!=key))StagedAssets.Add(new(key,"tile",tile.Name,tile.Image,tile.SourceWidth,tile.SourceHeight,tile.CropX,tile.CropY,tile.CropWidth,tile.CropHeight,Role=="GM"?HandCard.Approved:HandCard.Pending));Notify();}
    public int ImportTileset(string folder,IEnumerable<string> images)
    {
        var list=images.Where(x=>!string.IsNullOrWhiteSpace(x)).Take(256).ToList();
        var batch=Guid.NewGuid().ToString("N")[..8];
        for(var i=0;i<list.Count;i++)AtlasTiles.Add(new($"user-{batch}-{i+1}",$"{folder} {i+1:000}",list[i],"UNIVERSAL","Imported",folder,"User upload"));
        Notify();return list.Count;
    }
    public void RemoveStaged(string key){StagedAssets.RemoveAll(x=>x.Key==key);Notify();}
    public void ApproveStaged(string key){if(Role!="GM")return;var i=StagedAssets.FindIndex(x=>x.Key==key);if(i>=0)StagedAssets[i]=StagedAssets[i] with{ApprovalStatus=HandCard.Approved};Notify();}
    public void DenyStaged(string key){if(Role!="GM")return;RemoveStaged(key);}
    public void PlaceStaged(StagedAsset staged,double x,double y,double placementZoom){if(Role=="PC"&&staged.ApprovalStatus!=HandCard.Approved)return;x=Math.Clamp(x,0,1);y=Math.Clamp(y,0,1);if(staged.Kind=="tile")PlacedTiles.Add(new(staged.Key[5..],staged.Name,staged.Image,x,y,staged.SourceWidth,staged.SourceHeight,staged.CropX,staged.CropY,staged.CropWidth,staged.CropHeight,Math.Max(placementZoom,.01)));else Pieces.Add(new(staged.Kind,x,y,staged.Kind=="pin"?Math.Max(placementZoom,.01):1));Notify();}
    public void MovePiece(PieceItem piece,double x,double y){var i=Pieces.IndexOf(piece);if(i<0)return;Pieces[i]=piece with{X=Math.Clamp(x,0,1),Y=Math.Clamp(y,0,1)};Notify();}
    public void RemovePiece(PieceItem piece){Pieces.Remove(piece);Notify();}
    public void MoveTile(TileItem tile,double x,double y){if(!CanEditTiles||tile.Locked)return;var i=PlacedTiles.IndexOf(tile);if(i<0)return;PlacedTiles[i]=tile with{X=Math.Clamp(x,0,1),Y=Math.Clamp(y,0,1)};Notify();}
    public void RemoveTile(TileItem tile){if(!CanEditTiles||tile.Locked)return;PlacedTiles.Remove(tile);Notify();}
    public void MapTap(double x,double y){}
    public void PlacePin(double x,double y,double placementZoom)=>Pieces.Add(new("pin",Math.Clamp(x,0,1),Math.Clamp(y,0,1),Math.Max(placementZoom,.01)));
    public void AddGem(int value){Gems.Add(new(value,.20+Random.Shared.NextDouble()*.60,.20+Random.Shared.NextDouble()*.60));Notify();}
    public void ClearRolls(){Rolls.Clear();Gems.Clear();Notify();}
}
