# Legal and ethics

Read this before filing an issue asking for a feature that crosses these lines.

## What this tool is for

* Keeping an offline copy of material **you were given access to** — course readings,
  papers handed to you as view-only, your own documents shared without download rights.
* Accessibility: reading on an e-ink device, a screen reader, or a machine that cannot run
  the Drive viewer.
* Personal archival of study material that disappears when a link expires.

That is a real, ordinary need, and it is why this project exists.

## What it is not for

* Redistributing anyone else's work.
* Building a mirrored library of third-party material.
* Anything you would be uncomfortable explaining to the author.

## Your responsibilities

A "view only" flag is a **technical access control**. Reading pages you were already
granted access to, in a viewer that renders them to your own machine, is different in kind
from crossing an authentication boundary — this tool never does the latter. It does not
forge credentials, reuse your profile, solve CAPTCHAs, or attempt to defeat rate limits.

But the distinction only holds if you keep it:

> **You are responsible for** complying with copyright law in your jurisdiction, with the
> terms under which the material was shared, and with
> [Google's Terms of Service](https://policies.google.com/terms).

The MIT license covers *this software*. It grants you no rights whatsoever in the documents
you point it at.

## Practical safeguards built in

* `.gitignore` excludes `downloads/`, `*.pdf` and profile directories — a careless `git add`
  cannot publish other people's documents.
* No cookies, no Google profile, no account: the tool has no way to reach anything except
  links that are already public or that you explicitly pass in.
* Bounded concurrency (default 2) and a deliberate per-page scroll delay: the tool is slow
  on purpose, to stay within normal human browsing behaviour rather than to hammer Drive.

## If you are a rights holder

If you believe a repository using this tool is redistributing your work, that constitutes
misuse of the tool and a copyright issue independent of this project. The maintainers have
no control over downstream copies; please direct takedown requests to wherever the
material is hosted.

## Reporting misuse

If you find a repository that uses this code to redistribute protected material, open an
issue or email the maintainer, and we will say so publicly in the README's
"known misuse" section if it is serious and verifiable.
