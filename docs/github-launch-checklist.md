# GitHub launch checklist (owner settings)

These cannot be changed from the CI token used by cloud agents. Flip them in
the GitHub UI (or with a PAT that has `admin:repo`):

1. **Visibility** — Settings → General → Danger Zone → Change visibility → **Public**.
2. **Topics** — repo header → ⚙️ gear next to About → add:
   `agents`, `local-llm`, `ollama`, `sandbox`, `tdd`, `world-model`.
3. **Homepage URL** — same About panel → set to
   `https://github.com/jeremy-jaeger/loop-engineering-lite/blob/main/docs/getting-started.md`
   (or a landing page when you have one).
4. **Description** — prefer the product line over the north-star sentence, e.g.
   `Verify agents before they touch your disk — local VFS sandbox + Ollama + TDD commits.`

In-repo messaging, SECURITY, roadmap, CLI, CI, and issue templates are already
updated on this branch.
