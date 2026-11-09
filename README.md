# Nuvio badge packs

Stream badge packs for Nuvio's **Fusion badge URLs** (Profile → Layout → Streams). Every pack has the same 49 filters and patterns; only the look changes. Paste one link, restart Nuvio to switch.

| Pack | Look | Link |
|---|---|---|
| Tiered | Filled mono text chips, quiet suffix (`4K │ UHD`), greyscale tiers, visual right after resolution | `https://savantguarded-nuvio-badges.vercel.app/badges-tiered.json` |
| Filled | Filled mono text chips, one fill | `https://savantguarded-nuvio-badges.vercel.app/badges-filled.json` |
| Main | Logo badges, outlined | `https://savantguarded-nuvio-badges.vercel.app/badges.json` |
| Solid | kingsizew solid logos, colour tiers | `https://savantguarded-nuvio-badges.vercel.app/badges-solid.json` |
| Mono | kingsizew logos on white | `https://savantguarded-nuvio-badges.vercel.app/badges-mono.json` |

## How it works

- Images are 80 px tall PNGs in `public/img/`, served with a one-year immutable cache, so a changed image always gets a **new file name** (e.g. `tiered-v2-…` → `tiered-v3-…`).
- Nuvio draws the chip (20 dp tall, 6 dp corners, image slot 34–92 dp wide). The filled packs bake only the text into the image and set the chip fill per filter. Keep every image at or under 92 dp wide (460 px) or Nuvio shrinks it.
- Badge order in the sources list follows filter order in the JSON.

## Rebuilding the text packs

```
mkdir -p .work && cd .work
npm pack geist && mkdir g && tar -xzf geist-*.tgz -C g
npm pack @tabler/icons && mkdir tabler && tar -xzf tabler-icons-*.tgz -C tabler
cd .. && python3 -I scripts/build-tiered-pack.py && python3 -I scripts/build-filled-pack.py
```

`scripts/lib/variants.py` holds the tiered layout rules (labels, suffixes, tiers, spacing). The logo packs (main, solid, mono) are built by the other scripts from their source repos; see each script's header.
