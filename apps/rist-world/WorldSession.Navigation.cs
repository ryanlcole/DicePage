namespace RistWorld;
public sealed partial class WorldSession
{
 public static readonly string[] TableLayers = ["WORLD","ZONE","CONTINENT","REGION","LOCAL","AREA"];
 public string Layer { get; private set; } = "WORLD";
 public bool EncounterActive { get; private set; }
 public string? RecurseTarget { get; private set; }
 public string TableMode { get; private set; } = "worldbuilder";
 public string TableModeLabel=>TableMode switch{"forge"=>"Forge","test"=>"Test","encounter"=>"Encounter","play"=>"Let's Roll!",_=>"Worldbuilder"};
 public bool PlayActive=>TableMode=="play";
 public bool TileLockMode { get; private set; }
 public bool CanEditTiles=>Role=="GM"&&TableMode=="worldbuilder";
 public void ToggleTileLockMode(){if(!CanEditTiles)return;TileLockMode=!TileLockMode;Notify();}
 public void ToggleTileLock(TileItem tile){if(!CanEditTiles||!TileLockMode)return;var index=PlacedTiles.IndexOf(tile);if(index>=0)PlacedTiles[index]=tile with{Locked=!tile.Locked};Notify();}
 public bool ChatComposerOpen { get; private set; }
 public bool DialogueOpen { get; private set; }
 public string ChatDraft { get; set; } = "";
 public string DialogueText { get; private set; } = "";
 public string DialogueSpeaker=>string.IsNullOrWhiteSpace(CharacterName)?"Player":CharacterName;

 public PieceItem? SelectedPin { get; private set; }
 readonly System.Diagnostics.Stopwatch encounterClock=new();
 System.Threading.Timer? encounterTimer;
 public bool EncounterTimerRunning=>encounterClock.IsRunning;
 public TimeSpan EncounterElapsed=>encounterClock.Elapsed;
 public string EncounterElapsedText=>$"{(int)EncounterElapsed.TotalHours:00}:{EncounterElapsed.Minutes:00}:{EncounterElapsed.Seconds:00}";
 public string EncounterElapsedIso=>$"PT{(int)EncounterElapsed.TotalHours}H{EncounterElapsed.Minutes}M{EncounterElapsed.Seconds}S";

 string preEncounterGridStyle = "square";
 string preEncounterUnit = "mi";
 double preEncounterDistance = 5;
 double preEncounterCalibrationZoom = 1;

 public void SetTableMode(string mode)
 {
  mode=mode switch{"worldbuilder" or "forge" or "test" or "encounter" or "play"=>mode,_=>"worldbuilder"};
  if(mode is "encounter" or "play"){if(!EncounterActive)EnterEncounter();}
  else if(EncounterActive)ExitEncounter();
  TableMode=mode;
  if(mode!="worldbuilder")TileLockMode=false;
  if(mode!="play"){encounterClock.Stop();encounterTimer?.Dispose();encounterTimer=null;}
  Notify();
 }
 public void ToggleChatComposer(){ChatComposerOpen=!ChatComposerOpen;if(ChatComposerOpen)DialogueOpen=false;Notify();}
 public void CloseChat(){ChatComposerOpen=false;DialogueOpen=false;Notify();}
 public void SendChat()
 {
  var message=ChatDraft.Trim();
  if(message.Length==0)return;
  DialogueText=message;ChatDraft="";ChatComposerOpen=false;DialogueOpen=true;Notify();
 }
 public void AdvanceDialogue(){DialogueOpen=false;Notify();}

 public void SetLayer(string layer)
 {
  if(EncounterActive)return;
  if(TableLayers.Contains(layer))Layer=layer;
  Notify();
 }

 public void EnterEncounter()
 {
  if(EncounterActive)return;
  preEncounterGridStyle=GridStyle;
  preEncounterUnit=DistanceUnit;
  preEncounterDistance=GridDistance;
  preEncounterCalibrationZoom=GridCalibrationZoom;
  EncounterActive=true;
  GridStyle="hex";
  DistanceUnit="ft";
  GridDistance=5;
  GridCalibrationZoom=Math.Max(ViewZoom,.01);
  Notify();
 }

 public void ExitEncounter()
 {
  if(!EncounterActive)return;
  encounterClock.Stop();
  encounterTimer?.Dispose();
  encounterTimer=null;
  EncounterActive=false;
  if(TableMode is "encounter" or "play")TableMode="worldbuilder";
  GridStyle=preEncounterGridStyle;
  DistanceUnit=preEncounterUnit;
  GridDistance=preEncounterDistance;
  GridCalibrationZoom=preEncounterCalibrationZoom;
  Notify();
 }

 public void ToggleEncounterTimer()
 {
  if(encounterClock.IsRunning)
  {
   encounterClock.Stop();
   encounterTimer?.Dispose();
   encounterTimer=null;
  }
  else
  {
   encounterClock.Start();
   encounterTimer=new System.Threading.Timer(_=>Notify(),null,TimeSpan.Zero,TimeSpan.FromSeconds(1));
  }
  Notify();
 }
 public void ResetEncounterTimer()
 {
  encounterClock.Reset();
  Notify();
 }
 public void PinTap(PieceItem piece)
 {
  if(piece.Kind!="pin")return;
  if(SelectedPin is not null && ReferenceEquals(SelectedPin,piece))
  {
   Layer="REGION";
   RecurseTarget=$"pin:{piece.X:0.####},{piece.Y:0.####}";
   SelectedPin=null;
  }
  else SelectedPin=piece;
  Notify();
 }
 public void DismissPin(){SelectedPin=null;Notify();}
 public void ReturnToWorld(){Layer="WORLD";RecurseTarget=null;SelectedPin=null;EncounterActive=false;TableMode="worldbuilder";Notify();}
}
