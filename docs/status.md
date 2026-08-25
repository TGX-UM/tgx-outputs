# Collection status

--8<-- "freshness.md"

## Blind spots

A gap that is not declared reads as a zero, so:

- GHCR publishes no pull count for containers, and no API offers one. Docker Hub
  does, so GHCR images are counted by tags published instead. Private images are
  skipped rather than listed.
- GitHub page views and clones are not collected. They need push access to every
  repository, which means storing a token, and this runs without secrets. The window
  is 14 days anyway.
- PyPI download history cannot be backfilled. The public API keeps about 180 days.
- The Research Software Directory only knows registered tools. Software that was never
  registered shows no mentions, which is an argument for registering it.
- Only the projects listed in `config/projects.yml` are counted. A tool nobody has
  added is absent, and absence here means nobody added it, not that it does not exist.
- Citations are counted for the papers a project declares. A tool with no paper shows
  no citations, which is a property of the tool, not of its use.

## When something breaks

Sources are collected independently, so one broken API degrades one section and the
page still builds with that section marked stale rather than showing last week's
number as if it were current.

[Open an issue](https://github.com/TGX-UM/tgx-outputs/issues/new). Every figure links
to its data, and the run manifests record what each source returned and what failed.
