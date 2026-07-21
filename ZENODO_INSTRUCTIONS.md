# Publishing to Zenodo — what's done, what needs you

I can't complete this one myself — it needs your Zenodo account. Here's exactly what to do
(~10 minutes), and everything I could prepare in advance.

## What's already prepared

- **`.zenodo.json`** — full deposit metadata (title, description, creators, keywords, licence).
  If you use the GitHub integration (recommended, see below), Zenodo reads this file automatically.
- **`CHANGELOG.md`** — the version history the deposit description references.
- **Git tag `v2.0.0`** — created locally, annotated, matching the changelog. **Not yet pushed**
  (tags aren't pushed by a normal `git push`) — push it yourself when ready: `git push origin v2.0.0`.
- **`/tmp/aief-ontology-v2.0.0.tar.gz`** — a standalone archive (ontology, KG export, SHACL shapes,
  README, CHANGELOG) if you'd rather do a manual upload instead of the GitHub integration.

## Recommended path: GitHub → Zenodo integration (does the archiving for you, forever)

1. Go to [zenodo.org](https://zenodo.org), log in (GitHub OAuth is easiest), go to
   **Settings → GitHub**.
2. Find `navinaamuthan/ai-ethics-framework-tool` in the repo list and flip it **on**.
3. Push the tag: `git push origin v2.0.0`, then go to the GitHub repo → **Releases** →
   **Draft a new release**, pick tag `v2.0.0`, publish it.
4. Zenodo automatically archives that release and mints a DOI within a few minutes. Check
   **zenodo.org/account/settings/github** for the badge/DOI once it appears.
5. Add the DOI badge markdown Zenodo gives you to the top of `README.md`.

Every future GitHub release (v2.1.0, etc.) will auto-archive the same way — no repeated manual work.

## Alternative: manual upload (if you don't want the GitHub integration)

1. [zenodo.org/deposit/new](https://zenodo.org/deposit/new)
2. Upload `/tmp/aief-ontology-v2.0.0.tar.gz`
3. Zenodo will mostly pre-fill from `.zenodo.json` if you paste its contents into the form fields
   (title, description, creators, keywords, licence — all already written for you above)
4. Click **Publish** — this step is irreversible (Zenodo DOIs cannot be deleted, only new versions
   added), so double-check the metadata before confirming.

## One honest caveat before you publish

`.zenodo.json`'s `contributors` field lists Delaram Golpayegani by name as an ontology contributor.
That's accurate (her seven-point review is documented in this repo), but it's
still attributing a named real person on a public, permanent record — worth a quick "I'm archiving
this on Zenodo and crediting your review, let me know if you'd like the wording changed" message to
her before you click publish, not because it's wrong, but because it's the kind of thing you'd want
to be asked about too.
