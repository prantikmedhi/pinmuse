# Craft: making posts people save

## Copy
- **Title: 2–5 words.** A title is something you read in a second. "Neon Nights" beats "A guide to neon nights in Tokyo".
- **Subtitle: one line that gives the reason to care.** Benefit, date, or a feeling.
- **Kicker: a tiny label above the title** ("Vol. 03", "New drop", "5 tiny changes"). It makes a post look like a series.
- **CTA:** "Save for later" for carousels and tips (saves drive reach on IG and Pinterest), "Link in bio" for stories, nothing at all for mood posts.
- Use title case or sentence case. Avoid ALL CAPS except in `swiss`, `magazine` mastheads and kickers.

## Layout
- **Stories:** the top 12% and bottom 18% sit under platform UI. The `story` template keeps type out of those bands.
- **Prompt for negative space** where the type goes (the prompt builder adds this per template). If the subject still sits under the title, regenerate. Don't shrink the type.
- **One focal point per image.** A busy image needs `minimal`, `polaroid` or `collage`, not `poster`.
- **Contrast:** the composer picks ink colour from the image's luminance. If the result is still weak, pass a `--palette` whose darkest and lightest entries are far apart.

## Carousel recipe (best for reach)
1. Cover: a promise ("Make your room feel like a dream") plus a kicker with the count ("5 tiny changes").
2. 3–7 slides: a short title and one or two sentences each. Write them as `[{"title": "…", "body": "…"}]`.
3. End slide: CTA "Save this for …" and the handle.

## Pinterest pins
- 2:3 (`pin`) or long (`pin-long`). Put the text overlay in the top third. Pin titles become search queries, so use words people actually search (take them from `pinmuse suggest`).

## Captions
`caption.txt` is a starting point. Rewrite it in the user's voice: a hook line, 1–2 lines of value, a question to prompt comments, then 8–15 hashtags. Mix broad tags (#aesthetic) with niche ones (#darkacademiadesk).
