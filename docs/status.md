# Collection status

--8<-- "freshness.md"

## Known blind spots

Stated plainly, because a gap that is not declared reads as a zero.

- **Container pulls from GHCR are unknowable.** GitHub publishes no pull count for
  container packages at all. Docker Hub does, so images published there are countable
  and images on GHCR are not. Releases and tags are counted instead.
- **GitHub traffic — page views and clones — is not collected.** It requires push
  access to every repository, which means storing a personal access token, and this
  project keeps the property that it runs with no secrets. Its window is only fourteen
  days in any case, so a single missed run would lose data permanently.
- **PyPI download history cannot be backfilled.** The public statistics API retains
  roughly 180 days. Any series that starts today starts today.
- **The Research Software Directory only knows about registered tools.** Department
  software that has never been registered there shows no literature mentions. That is
  an argument for registering it, not for building a second harvester.
- **OpenAlex author disambiguation is imperfect.** It occasionally merges a namesake,
  which shows up as a step change in the "what changed" panel. Its author *entity* is
  unreliable for this department — one departmental ORCID resolves to a profile
  claiming six works while a query for the same ORCID returns well over a hundred — so
  the corpus is always built from the works endpoint, never from author summaries.
- **Zenodo download counts are not shown.** The search API reports statistics against
  whichever version record it returns, and that varies run to run: the monotonic guard
  caught one deposition reporting 567 unique downloads in one week and 53 the next.
  Deposition counts are stable and are what the page uses instead.
- **Pure lags, and only knows what people entered.** It is authoritative for
  articles and theses and largely blind to software and data.

## When something breaks

Every source is collected independently and a failure is isolated: one broken API
degrades one section, and the page still builds with that section visibly marked stale
rather than quietly showing last week's number as if it were today's.

If a figure looks wrong, it may well be.
[Open an issue](https://github.com/TGX-UM/tgx-outputs/issues/new) — every figure links
to the CSV behind it, and the run manifests in the repository record what each source
returned, what failed, and what was quarantined.
