# ReLiC External Asset Discovery Doctrine

Status: LOCKED product doctrine

## Purpose

ReLiC may help a user continue searching independent asset sources when the ReLiC library does not contain what they need. These links are navigation and discovery, not behavioral advertising.

## Neutral ordering

1. External providers are eligible because they are useful sources of game-development assets, including tilesets, sprites, animated assets, terrain, maps, models, props, UI, icons, VFX, textures, audio, music, palettes, and game-design resources.
2. External providers are ordered alphabetically using deterministic rules.
3. Commission rate, sponsorship, popularity, previous purchases, browsing behavior, search history, and user identity MUST NOT influence provider order.
4. Affiliate, free, open-license, and donation-supported providers have equal eligibility.
5. The library may show the last three asset-sized cards as external discovery destinations appropriate to the current asset category. Selection must be contextual to the category, never behavioral to the person.

## Search privacy

- ReLiC MUST NOT retain external-discovery search history.
- ReLiC MUST NOT attach a ReLiC user ID, Discord ID, customer ID, advertising ID, or other personal identifier to an outbound search query.
- The text currently present in the search field MAY be passed to the chosen provider's search URL when the user explicitly activates an external search card.
- Passing the query is a user-requested navigation action, not permission to create a behavioral profile.
- External cards must clearly indicate that the user is leaving ReLiC and that the destination provider's privacy/cookie policies then apply.

## Affiliates and support

- ReLiC MAY use an official affiliate/referral identifier offered by a provider.
- Affiliate status MUST NOT affect ranking, eligibility, prominence, or frequency.
- Affiliate destinations should disclose that ReLiC may receive a commission at no additional cost to the user.
- ReLiC MAY link to free and donation-supported resources without compensation. Sending relevant users to those resources is considered ecosystem support.
- ReLiC MUST NOT fabricate affiliate relationships or referral identifiers.

## Initial provider set

Alphabetically:

- GameDev Market
- itch.io
- Kenney
- Lospec
- OpenGameArt
- Poly Haven
- Quaternius

Provider URLs, capabilities, licenses, affiliate status, and query templates are configuration data and may change without changing this doctrine.

## Governing principle

**Monetize the referral relationship when available; never monetize or profile the user's behavior.**
