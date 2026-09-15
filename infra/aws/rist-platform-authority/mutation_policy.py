from decimal import Decimal, InvalidOperation

MAX_INDEX = 1_000_000
MAX_LABEL = 256
MAX_KIND = 80


def _safe_id(value, label):
    value = str(value or "").strip()
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
    if not value or len(value) > 160 or any(c not in allowed for c in value):
        raise ValueError(f"Invalid {label}")
    return value


def _text(value, label, maximum, required=False):
    text = str(value or "").strip()
    if required and not text:
        raise ValueError(f"{label} is required")
    if len(text) > maximum:
        raise ValueError(f"{label} is too long")
    return text


def _decimal(value, label, minimum=None, maximum=None):
    if isinstance(value, bool):
        raise ValueError(f"Invalid {label}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid {label}")
    if not number.is_finite():
        raise ValueError(f"Invalid {label}")
    if minimum is not None and number < Decimal(str(minimum)):
        raise ValueError(f"{label} is below its minimum")
    if maximum is not None and number > Decimal(str(maximum)):
        raise ValueError(f"{label} is above its maximum")
    return number


def _integer(value, label, minimum=-MAX_INDEX, maximum=MAX_INDEX):
    number = _decimal(value, label, minimum, maximum)
    if number != number.to_integral_value():
        raise ValueError(f"{label} must be an integer")
    return int(number)


def _piece_identity(payload, entity_id):
    if not isinstance(payload, dict):
        raise ValueError("Piece payload must be an object")
    if payload.get("entityType") != "piece":
        raise ValueError("Piece payload entityType must be piece")
    piece_id = _safe_id(payload.get("pieceId"), "pieceId")
    if entity_id != f"piece-{piece_id}":
        raise ValueError("Piece identity does not match entityId")
    return piece_id


def _existing_piece_state(current_state, piece_id):
    if not isinstance(current_state, dict):
        raise ValueError("Stored piece state is invalid")
    if current_state.get("entityType") != "piece":
        raise ValueError("Stored entity is not a piece")
    if str(current_state.get("pieceId") or "") != piece_id:
        raise ValueError("Stored piece identity does not match entityId")
    return dict(current_state)


def canonical_piece_state(action, entity_id, payload, current_state, manager=False):
    piece_id = _piece_identity(payload, entity_id)

    if action == "piece.move":
        if current_state is None:
            if not manager:
                raise PermissionError("Only world management authority may create a piece")
            state = {
                "entityType": "piece",
                "pieceId": piece_id,
                "kind": _text(payload.get("kind"), "kind", MAX_KIND, required=True),
                "label": _text(payload.get("label"), "label", MAX_LABEL),
            }
        else:
            state = _existing_piece_state(current_state, piece_id)
            if bool(state.get("removed")):
                raise ValueError("Removed piece cannot be moved")

        state.update(
            {
                "entityType": "piece",
                "pieceId": piece_id,
                "x": _decimal(payload.get("x"), "x", 0, 1),
                "y": _decimal(payload.get("y"), "y", 0, 1),
                "placementZoom": _decimal(payload.get("placementZoom"), "placementZoom", "0.000001", 1000),
                "cubeX": _integer(payload.get("cubeX", 0), "cubeX"),
                "cubeY": _integer(payload.get("cubeY", 0), "cubeY"),
                "cubeZ": _integer(payload.get("cubeZ", 0), "cubeZ"),
                "planeIndex": _integer(payload.get("planeIndex", 0), "planeIndex"),
                "tierIndex": _integer(payload.get("tierIndex", 0), "tierIndex"),
                "layerOffset": _integer(payload.get("layerOffset", 0), "layerOffset"),
                "removed": False,
            }
        )
        return state

    if action == "piece.remove":
        if current_state is None:
            raise ValueError("Piece does not exist")
        state = _existing_piece_state(current_state, piece_id)
        state["removed"] = True
        return state

    raise ValueError("Unknown piece mutation action")


def protects_piece(action, entity_id, current_state):
    return (
        str(action or "").startswith("piece.")
        or str(entity_id or "").startswith("piece-")
        or (isinstance(current_state, dict) and current_state.get("entityType") == "piece")
    )


def dynamo_safe(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {str(key): dynamo_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [dynamo_safe(item) for item in value]
    return value
