# Pinterest sources

| Source | Needs | Gives | Notes |
|---|---|---|---|
| `web` | nothing | search, pin, related pins, public boards, typeahead suggestions | The JSON resources pinterest.com's frontend calls, signed out. Throttled and cached. |
| `api-anything` | Node 22+ and `api-anything` | `pinterest.searchSuggestions` from the shared catalog, plus any op you learn | [goodnight000/api-anything](https://github.com/goodnight000/api-anything). Learn pin search once with `api-anything learn "https://www.pinterest.com/search/pins/?q=ceramics"` and name the op `searchPins`. After that, `--source api-anything` uses it, and so does everyone who installs it. |
| `browser` | `pip install "pinmuse[browser]"` and `playwright install chromium` | whatever the grid shows | Slowest and most robust. Use it when the JSON resources change. |
| `official` | `PINTEREST_ACCESS_TOKEN` (scopes `boards:read`, `pins:read`, and `pins:write` to publish) | the user's own boards and pins, plus publishing | The stable, ToS-friendly path for private boards. `pinmuse boards`, `pinmuse boards --board <id>`. |
| `local:<dir>` | a folder | the images in it | Exports, downloaded boards, brand photography. |

The query can be:
- a phrase: `"dark academia desk"`
- a pin URL: `https://www.pinterest.com/pin/123…/` returns that pin and its "more like this" pins
- a board URL: `https://www.pinterest.com/<user>/<board>/`
- a folder path

## When it fails
Every result has a `log` with one line per source tried. Common cases:
- `web: failed (HTTPFailure: HTTP 403…)`: Pinterest is rate-limiting or blocking this network. Wait, or use `browser` / `official`.
- `0 pins`: the query is too specific. Run `suggest` and use one of its phrases.
- Image downloads fail: palette analysis falls back to Pinterest's `dominant_color` per pin, so you can still go ahead.
