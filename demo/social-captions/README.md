# TBS Caption Studio

A one-page demo of the `social-captions` skill: pick a topic and a tone, get 3 Instagram captions.

| File | Use |
|---|---|
| `tbs-caption-studio.html` | Standalone. Double-click to open in any browser. No install. |
| `app.html` | Source of the published claude.ai artifact (same page without the HTML wrapper). |

## Three ways it runs

1. **On claude.ai (no setup):** open the shared artifact link while signed in. Generation uses the viewer's own Claude account; the first click asks permission.
2. **Standalone with a key:** open `tbs-caption-studio.html`, expand "API key", paste an Anthropic API key, press Save. Calls go straight from the browser to `api.anthropic.com` (model `claude-opus-5-5`). The key stays in that browser only.
3. **Offline / no key:** the page still works and shows built-in example captions for all 8 preset topics, clearly labeled as examples.
