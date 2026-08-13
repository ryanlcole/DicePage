namespace RistWorld;
public sealed partial class WorldSession
{
 public string Layer { get; private set; } = "WORLD";
 public string? RecurseTarget { get; private set; }
 public void Recurse(PieceItem piece){if(piece.Kind!="pin")return;Layer="REGION";RecurseTarget=$"pin:{piece.X:0.####},{piece.Y:0.####}";Notify();}
 public void ReturnToWorld(){Layer="WORLD";RecurseTarget=null;Notify();}
}
