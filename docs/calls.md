# Every call this page makes

One section per source: the shape of what it asks for, every individual request from
the last run, and the metrics that came out. Generated from the run manifest, so it
describes what actually happened rather than what the code is supposed to do.

If a number on this site looks wrong, this is where to start. Every URL below can be
pasted into a browser — they are all public, none of them needs a key — and the answer
you get is the answer this page got.

--8<-- "freshness.md"

## How to read a diagram

Requests on the left, the collector in the middle, the metrics it produced on the
right. A box marked `×19` is one endpoint asked nineteen times, once per repository or
package; the table underneath it lists all nineteen in the order they were made.

An endpoint pattern with `…` in it means that segment varied between calls. The literal
URLs are in the tables, never abbreviated.

## The sources

--8<-- "calls.md"

## What is not here

The response bodies. They are large, they are somebody else's data, and republishing
them wholesale is a different act from publishing what we derived. What each call
returned in summary is in the right-hand column; the derived numbers are in
[the CSVs](downloads.md); and the raw run manifests on the `data` branch record every
call, every error and every quarantined record for every run, not just the last one.
