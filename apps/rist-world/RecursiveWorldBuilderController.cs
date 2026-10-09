namespace RistWorld;

/// <summary>
/// Device-independent WorldBuilder controller bus.
/// Hardware adapters emit only X, Y, Left, and Right. The active context
/// interprets those inputs; adapters never mutate viewer/world state directly.
/// </summary>
public sealed class RecursiveWorldBuilderController
{
    public RecursiveWorldBuilderControlContext Context { get; private set; } =
        RecursiveWorldBuilderControlContext.Navigate;

    public event Action<RecursiveWorldBuilderIntent>? Intent;

    public void SetContext(RecursiveWorldBuilderControlContext context) => Context = context;

    public void X(double value) => DispatchAxis(RecursiveWorldBuilderInput.X, value);
    public void Y(double value) => DispatchAxis(RecursiveWorldBuilderInput.Y, value);
    public void Left() => DispatchButton(RecursiveWorldBuilderInput.Left);
    public void Right() => DispatchButton(RecursiveWorldBuilderInput.Right);

    void DispatchAxis(RecursiveWorldBuilderInput input, double value)
    {
        if (Math.Abs(value) < 0.0001) return;
        Intent?.Invoke(Resolve(Context, input, value));
    }

    void DispatchButton(RecursiveWorldBuilderInput input) =>
        Intent?.Invoke(Resolve(Context, input, 1));

    public static RecursiveWorldBuilderIntent Resolve(
        RecursiveWorldBuilderControlContext context,
        RecursiveWorldBuilderInput input,
        double value)
    {
        var action = (context, input) switch
        {
            (RecursiveWorldBuilderControlContext.Navigate, RecursiveWorldBuilderInput.X) => RecursiveWorldBuilderAction.NavigateX,
            (RecursiveWorldBuilderControlContext.Navigate, RecursiveWorldBuilderInput.Y) => RecursiveWorldBuilderAction.NavigateY,
            (RecursiveWorldBuilderControlContext.Navigate, RecursiveWorldBuilderInput.Left) => RecursiveWorldBuilderAction.Ascend,
            (RecursiveWorldBuilderControlContext.Navigate, RecursiveWorldBuilderInput.Right) => RecursiveWorldBuilderAction.Descend,

            (RecursiveWorldBuilderControlContext.Place, RecursiveWorldBuilderInput.X) => RecursiveWorldBuilderAction.MoveX,
            (RecursiveWorldBuilderControlContext.Place, RecursiveWorldBuilderInput.Y) => RecursiveWorldBuilderAction.MoveY,
            (RecursiveWorldBuilderControlContext.Place, RecursiveWorldBuilderInput.Left) => RecursiveWorldBuilderAction.Cancel,
            (RecursiveWorldBuilderControlContext.Place, RecursiveWorldBuilderInput.Right) => RecursiveWorldBuilderAction.Confirm,

            (RecursiveWorldBuilderControlContext.Layer, RecursiveWorldBuilderInput.X) => RecursiveWorldBuilderAction.MoveTier,
            (RecursiveWorldBuilderControlContext.Layer, RecursiveWorldBuilderInput.Y) => RecursiveWorldBuilderAction.MoveLayer,
            (RecursiveWorldBuilderControlContext.Layer, RecursiveWorldBuilderInput.Left) => RecursiveWorldBuilderAction.Cancel,
            (RecursiveWorldBuilderControlContext.Layer, RecursiveWorldBuilderInput.Right) => RecursiveWorldBuilderAction.Confirm,

            (RecursiveWorldBuilderControlContext.Camera, RecursiveWorldBuilderInput.X) => RecursiveWorldBuilderAction.CameraPanX,
            (RecursiveWorldBuilderControlContext.Camera, RecursiveWorldBuilderInput.Y) => RecursiveWorldBuilderAction.CameraPanY,
            (RecursiveWorldBuilderControlContext.Camera, RecursiveWorldBuilderInput.Left) => RecursiveWorldBuilderAction.CameraReduce,
            (RecursiveWorldBuilderControlContext.Camera, RecursiveWorldBuilderInput.Right) => RecursiveWorldBuilderAction.CameraEnlarge,

            _ => RecursiveWorldBuilderAction.None
        };

        return new RecursiveWorldBuilderIntent(context, input, action, value);
    }
}

public enum RecursiveWorldBuilderInput { X, Y, Left, Right }
public enum RecursiveWorldBuilderControlContext { Navigate, Place, Layer, Camera }
public enum RecursiveWorldBuilderAction
{
    None,
    NavigateX,
    NavigateY,
    Ascend,
    Descend,
    MoveX,
    MoveY,
    MoveTier,
    MoveLayer,
    Cancel,
    Confirm,
    CameraPanX,
    CameraPanY,
    CameraReduce,
    CameraEnlarge
}

public sealed record RecursiveWorldBuilderIntent(
    RecursiveWorldBuilderControlContext Context,
    RecursiveWorldBuilderInput Input,
    RecursiveWorldBuilderAction Action,
    double Value);
