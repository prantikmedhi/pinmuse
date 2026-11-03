# pinmuse for Gemini CLI / Antigravity

You have the `pinmuse` MCP server. It explores Pinterest and makes aesthetic designs. Follow the loop
in [skills/pinmuse/SKILL.md](skills/pinmuse/SKILL.md):

1. `pinterest_suggest`: find the words Pinterest uses for the idea.
2. `pinterest_moodboard`: read the palette and aesthetic, and **look at the returned contact sheet image**.
3. `create_design`, or `build_prompt` → `generate_image` → `compose_design`.
4. Look at the output, fix it at most twice, then give the user the file paths, the caption and the pin credits.

If `GEMINI_API_KEY` is set, `generate_image` uses Gemini's image model and accepts pin images as style
references. Make original work. Never copy a pin.
