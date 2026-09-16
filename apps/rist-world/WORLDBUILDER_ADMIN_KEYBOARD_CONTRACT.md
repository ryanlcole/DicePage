# World Builder Admin Keyboard Contract

The Admin keyboard is a privileged World Builder control surface. It does not merge cartographic appearance with authorization.

## Separation of truth

1. **Region geometry** identifies the selected world area.
2. **Administrative cartography** describes region name, fill, opacity, and boundaries.
3. **Recursive Authority** decides who may View, Edit, receive Public view, or is explicitly Denied.

A color or border never grants permission. A permission never requires a visible color or border.

## Selection

The persistent World Builder D-pad remains available on the Admin keyboard. Admin selection supports an anchor-to-cursor rectangle, add/remove current square, all visible squares, and clear. The selection is an editing target and must be translated to canonical world geometry before durable server persistence; presentation density is not world truth.

## Boundaries

Administrative borders are shared edge/perimeter objects, not duplicated paint on both neighboring regions. A boundary may identify semantic type (continent, country, state, province, county, district, realm, zone), visual style, color, and width. Later rule mechanics such as crossings, tolls, jurisdiction, or visibility may reference the boundary without changing its geometric identity.

## Permissions

Permission requests use the existing `RecursiveAuthorityService` vocabulary and evaluator: `View`, `Edit`, `Public`, and `Deny`, with optional `StopsInheritance`. The Admin keyboard must not create a second browser-only permission authority. Until durable server persistence is exposed for recursive resource policies, the keyboard emits an explicit authority request rather than claiming that permission changes were saved.

## Accessibility

Every Admin control has a semantic label. Region selection must announce square count and position. Color is never the sole identifier; region name and border semantic type remain available to assistive presentation. D-pad navigation provides a non-drag selection path.
