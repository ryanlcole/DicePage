namespace RistWorld;
public sealed partial class WorldSession
{
 public static readonly string[] TableLayers = ["WORLD","ZONE","CONTINENT","REGION","LOCAL","AREA"];
 public string Layer { get; private set; } = "WORLD";
 public bool EncounterActive { get; private set; }
 public string? RecurseTarget { get; private set; }
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
 public void ReturnToWorld(){Layer="WORLD";RecurseTarget=null;SelectedPin=null;EncounterActive=false;Notify();}
}
