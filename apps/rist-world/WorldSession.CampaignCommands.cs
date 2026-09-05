namespace RistWorld;

public sealed partial class WorldSession
{
    public void BeginNewCampaign()
    {
        ResetToCanonicalOrigin();
        PrivateStorageStatus = "New campaign ready at the canonical Shaelvien origin.";
        Notify();
    }
}
