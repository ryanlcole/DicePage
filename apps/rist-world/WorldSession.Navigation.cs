namespace RistWorld;
public sealed partial class WorldSession
{
 public string Layer { get; private set; } = "WORLD";
 public string? RecurseTarget { get; private set; }
 public PieceItem? SelectedPin { get; private set; }
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
 public void ReturnToWorld(){Layer="WORLD";RecurseTarget=null;SelectedPin=null;Notify();}
}
