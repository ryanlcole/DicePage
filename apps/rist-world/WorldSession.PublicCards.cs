namespace RistWorld;

public sealed partial class WorldSession
{
    public List<HandCard> PublicCards { get; } = [];
    public string? DraggedHandCardId { get; private set; }
    public bool HandOpen { get; private set; }

    public void ToggleHand()
    {
        HandOpen = !HandOpen;
        Notify();
    }

    public void OpenHand()
    {
        if (HandOpen) return;
        HandOpen = true;
        Notify();
    }

    public void CloseHand()
    {
        if (!HandOpen) return;
        HandOpen = false;
        Notify();
    }

    public void BeginHandCardDrag(HandCard card)
    {
        DraggedHandCardId = card.Id;
        Notify();
    }

    public void CancelHandCardDrag()
    {
        DraggedHandCardId = null;
        Notify();
    }

    public void PublishHandCard(HandCard card)
    {
        if (PublicCards.All(x => x.Field.Id != card.Field.Id)) PublicCards.Add(card);
        DraggedHandCardId = null;
        Notify();
    }

    public void PublishDraggedHandCard()
    {
        if (DraggedHandCardId is null) return;
        var card = HandCards.FirstOrDefault(x => x.Id == DraggedHandCardId);
        if (card is not null) PublishHandCard(card);
        else CancelHandCardDrag();
    }

    public void RemovePublicCard(HandCard card)
    {
        PublicCards.RemoveAll(x => x.Field.Id == card.Field.Id);
        Notify();
    }

    public bool IsPublicCard(CharacterField field) => PublicCards.Any(x => x.Field.Id == field.Id);
}
