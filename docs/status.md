# Collection status

--8<-- "freshness.md"

## Blind spots

A gap that is not declared reads as a zero, so:

- Container pulls come from Docker Hub, which is the only registry that publishes a
  count. An image pushed only to GitHub's registry or another one has no usage figure
  here, and none of them offer an API that would give one.
- GitHub page views and clones are not collected. They need push access to every
  repository, which means storing a token, and this runs without secrets. The window
  is 14 days anyway.
- PyPI download history cannot be backfilled. The public API keeps about 180 days.
- The Research Software Directory only knows registered tools. Software nobody
  registered shows no mentions, which is a good argument for registering it.
- Only the projects listed in `config/projects.csv` are counted. A missing tool means
  nobody has added it yet, and adding one is a row in a table.
- Citations are counted for the papers a project declares. A tool with no paper of its
  own therefore shows none, however much it is used.

## When something breaks

Sources are collected independently, so one broken API degrades one section and the
page still builds with that section marked stale rather than showing last week's
number as if it were current.

[Open an issue](https://github.com/TGX-UM/tgx-outputs/issues/new). Every figure links
to its data, and the run manifests record what each source returned and what failed.
