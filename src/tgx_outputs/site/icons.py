"""Icons for the overview tiles, vendored rather than fetched.

Same reasoning as the Vega bundle in ``docs/assets/js``: a page that pulls its icons
from a CDN at render time stops rendering when the CDN moves and cannot be archived
intact. What is stored here is path data only, taken from the icon sets MkDocs Material
already ships, so the build needs no icon font, no network and no new dependency.

Provenance and licence, both of which permit this use:

* Simple Icons (https://simpleicons.org) -- CC0-1.0. The brand marks themselves remain
  the property of their owners and appear here only to identify the registry a number
  comes from.
* GitHub Octicons (https://primer.style/octicons) -- MIT.

Two of these are not the obvious mark, and the reason is legibility: they render at
about 15px, and a logo made of fine dots or stacked cubes is a grey smudge at that
size. Each entry carries its own note below.

Every glyph is a 24x24 viewBox drawn in ``currentColor``, so one rule in ``extra.css``
colours all of them correctly in both themes.

The literals are split on character count rather than at spaces: SVG path data is
whitespace-sensitive, and rewrapping it at word boundaries silently draws a different
shape.
"""

from __future__ import annotations

_ICONS: dict[str, str] = {
    # Octicons, octicons/repo-24.svg -- a tracked project is a repository.
    'repo': (
        '<path d="M3 2.75A2.75 2.75 0 0 1 5.75 0h14.5a.75.75 0 0 1 .75.75v20.5a.75.75 0 0 1-.75.7'
        '5h-6a.75.75 0 0 1 0-1.5h5.25v-4H6A1.5 1.5 0 0 0 4.5 18v.75c0 .716.43 1.334 1.05 1.605a.7'
        '5.75 0 0 1-.6 1.374A3.25 3.25 0 0 1 3 18.75ZM19.5 1.5H5.75c-.69 0-1.25.56-1.25 1.25v12.6'
        '51A3 3 0 0 1 6 15h13.5Z"/><path d="M7 18.25a.25.25 0 0 1 .25-.25h5a.25.25 0 0 1 .25.25v5'
        '.01a.25.25 0 0 1-.397.201l-2.206-1.604a.25.25 0 0 0-.294 0L7.397 23.46a.25.25 0 0 1-.397'
        '-.2z"/>'
    ),
    # Octicons, octicons/tag-24.svg -- releases are tags.
    'tag': (
        '<path d="M7.75 6.5a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5"/><path d="M2.5 1h8.44a1.'
        '5 1.5 0 0 1 1.06.44l10.25 10.25a1.5 1.5 0 0 1 0 2.12l-8.44 8.44a1.5 1.5 0 0 1-2.12 0L1.4'
        '4 12A1.5 1.5 0 0 1 1 10.94V2.5A1.5 1.5 0 0 1 2.5 1m0 1.5v8.44l10.25 10.25 8.44-8.44L10.9'
        '4 2.5Z"/>'
    ),
    # Simple Icons, simple/python.svg -- PyPI's own cube-cluster mark is unreadable at tile size;
    #   the language mark is not.
    'python': (
        '<path d="m14.25.18.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05'
        '.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.'
        '05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-'
        '.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05'
        '-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24'
        '-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.'
        '2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98-.23.33-.08.41.08.41'
        '.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm1'
        '3.09 3.95.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23'
        '-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8'
        '.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.1'
        '3-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25'
        '-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24'
        '.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.2'
        '7-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25-.23.33-.08.4'
        '1.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.4'
        '1.08z"/>'
    ),
    # Simple Icons, simple/bioconductor.svg -- the registry's own mark, cropped. The full
    #   artwork is a note beneath a dotted helix arc; at 15px the dots dissolve into grey
    #   haze and the note thins to a hairline. Bioconductor solved this the same way --
    #   their favicon is the note alone -- so this crops to the bowl and foot of the stem.
    'bioconductor': (
        '<path d="M15.103 0a.649.649 0 1 0 .001 1.298.649.649 0 0 0 0-1.298m7.473.031a.69.69 0 1 '
        '0 .001 1.38.69.69 0 0 0 0-1.38M7.757.727a.663.663 0 1 0 .001 1.325.663.663 0 0 0 0-1.325'
        'm5.87.053a.495.495 0 1 0 0 .99.495.495 0 0 0 0-.99m3.256.07a.663.663 0 1 0 0 1.325.662.6'
        '62 0 0 0 0-1.324m-7.275.596a.755.755 0 0 0-.756.758.755.755 0 1 0 1.51 0 .755.755 0 0 0-'
        '.754-.758m-3.373.395a.59.59 0 0 0-.596.588c0 .325.267.59.596.59.33 0 .597-.265.596-.59a.'
        '59.59 0 0 0-.596-.588m6.397.1a.347.347 0 1 0-.002.693.347.347 0 0 0 .002-.694m8.941.034a'
        '.455.455 0 1 0 0 .91.455.455 0 0 0 0-.91m-3.065.108a.808.808 0 1 0-.002 1.615.808.808 0 '
        '0 0 .002-1.615m-7.183.607a.935.935 0 1 0 0 1.87.935.935 0 0 0 0-1.87m-5.978.541a.39.39 0'
        ' 1 0 0 .78.39.39 0 0 0 0-.78m15.203.217a.865.865 0 1 0 .003 1.73.865.865 0 0 0-.003-1.73'
        'm-7.52.857a.736.736 0 1 0 .004 1.472.736.736 0 0 0-.003-1.472m-3.63.12a.579.579 0 1 0 .0'
        '02 1.158.579.579 0 0 0-.002-1.158M22 4.762a.499.499 0 1 0 .002.998.499.499 0 0 0-.002-.9'
        '98m-17.05.094c-.01 4.734.082 13.81-.009 14.286-.39-.202-1.113-.406-2.135-.012-1.13.435-2'
        '.007 1.386-2.216 2.404a4 4 0 0 0-.004 1.24c.13.688.554 1.116 1.193 1.204a3.8 3.8 0 0 0 1'
        '.182-.059c1.006-.262 1.94-1.01 2.38-1.91.291-.597.266.227.264-8.703L5.604 5.37c-.22-.167'
        '-.435-.342-.652-.514m2.477.137a.792.792 0 1 0 .001 1.583.792.792 0 0 0 0-1.583m11.858.06'
        'a.295.295 0 1 0 .001.59.295.295 0 0 0 0-.59m-4.245.516a.639.639 0 1 0 0 1.277.639.639 0 '
        '0 0 0-1.277m8.068.078a.347.347 0 1 0 0 .694.347.347 0 0 0 0-.694m-4.82.08a.387.387 0 1 0'
        ' 0 .774.387.387 0 0 0 0-.774m-1.294.58a.488.488 0 1 0 0 .975.488.488 0 0 0 0-.976"/>'
    ),
    # Octicons, octicons/package-24.svg -- a stand-in for Maven Central. Its own mark, the
    #   Apache feather, is 5.7kB of path describing detail that is entirely lost at the 15px
    #   these render at, and unlike Bioconductor's there is no part of it that survives
    #   cropping -- the whole mark is the feather.
    'package': (
        '<path d="M12.876.64V.639l8.25 4.763c.541.313.875.89.875 1.515v9.525a1.75 1.75 0 0 1-.875'
        ' 1.516l-8.25 4.762a1.748 1.748 0 0 1-1.75 0l-8.25-4.763a1.75 1.75 0 0 1-.875-1.515V6.917'
        'c0-.625.334-1.202.875-1.515L11.126.64a1.748 1.748 0 0 1 1.75 0Zm-1 1.298L4.251 6.34l7.75'
        ' 4.474 7.75-4.474-7.625-4.402a.248.248 0 0 0-.25 0Zm.875 19.123 7.625-4.402a.25.25 0 0 0'
        ' .125-.216V7.639l-7.75 4.474ZM3.501 7.64v8.803c0 .09.048.172.125.216l7.625 4.402v-8.947Z'
        '"/>'
    ),
    # Simple Icons, simple/npm.svg -- the registry's own mark.
    'npm': (
        '<path d="M1.763 0C.786 0 0 .786 0 1.763v20.474C0 23.214.786 24 1.763 24h20.474c.977 0 1.'
        '763-.786 1.763-1.763V1.763C24 .786 23.214 0 22.237 0zM5.13 5.323l13.837.019-.009 13.836h'
        '-3.464l.01-10.382h-3.456L12.04 19.17H5.113z"/>'
    ),
    # Simple Icons, simple/docker.svg -- the registry's own mark.
    'docker': (
        '<path d="M13.983 11.078h2.119a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2'
        '.119a.185.185 0 0 0-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 0'
        ' 0 .186-.186V3.574a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.'
        '082.185.185.185m0 2.716h2.118a.187.187 0 0 0 .186-.186V6.29a.186.186 0 0 0-.186-.185h-2.'
        '118a.185.185 0 0 0-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 0 0 .18'
        '4-.186V6.29a.185.185 0 0 0-.185-.185H8.1a.185.185 0 0 0-.185.185v1.887c0 .102.083.185.18'
        '5.186m-2.964 0h2.119a.186.186 0 0 0 .185-.186V6.29a.185.185 0 0 0-.185-.185H5.136a.186.1'
        '86 0 0 0-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 0 0 .186-.18'
        '5V9.006a.186.186 0 0 0-.186-.186h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185'
        '.185m-2.93 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185'
        ' 0 0 0-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 0 0 .185-.185V9.0'
        '06a.185.185 0 0 0-.184-.186h-2.12a.186.186 0 0 0-.186.186v1.887c0 .102.084.185.186.185m-'
        '2.92 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0'
        '-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51q-.508.0'
        '01-1.01.087c-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 '
        '1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.75.75 0 0 0-.75.748 11.'
        '4 11.4 0 0 0 .692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137a'
        '15.7 15.7 0 0 0 2.93-.266 12.3 12.3 0 0 0 3.823-1.389 10.5 10.5 0 0 0 2.61-2.136c1.252-1'
        '.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l'
        '.098-.288Z"/>'
    ),
    # Octicons, octicons/book-24.svg -- citations are of papers.
    'book': (
        '<path d="M0 3.75A.75.75 0 0 1 .75 3h7.497c1.566 0 2.945.8 3.751 2.014A4.5 4.5 0 0 1 15.7'
        '5 3h7.5a.75.75 0 0 1 .75.75v15.063a.75.75 0 0 1-.755.75l-7.682-.052a3 3 0 0 0-2.142.878l'
        '-.89.891a.75.75 0 0 1-1.061 0l-.902-.901a3 3 0 0 0-2.121-.879H.75a.75.75 0 0 1-.75-.75Zm'
        '12.75 15.232a4.5 4.5 0 0 1 2.823-.971l6.927.047V4.5h-6.75a3 3 0 0 0-3 3ZM11.247 7.497a3 '
        '3 0 0 0-3-2.997H1.5V18h6.947c1.018 0 2.006.346 2.803.98Z"/>'
    ),
}

# Every mark above fills a 24x24 box except Bioconductor's, which is cropped out of the
# full logo and so carries the window to crop to. Kept beside the paths rather than
# inside them, so the common case stays a plain string.
_VIEWBOX = {"bioconductor": "0 16 8 8"}
_DEFAULT_VIEWBOX = "0 0 24 24"


def svg(name: str, cls: str = "tgx-icon") -> str:
    """One inline SVG, or nothing at all if the name is not registered.

    A missing icon must never break a card. The number is the point and the glyph is
    decoration, so an unknown name renders as absent rather than as a broken image, and
    a test asserts that every card in fact carries one.
    """
    body = _ICONS.get(name)
    if not body:
        return ""
    return (
        f'<svg class="{cls}" viewBox="{_VIEWBOX.get(name, _DEFAULT_VIEWBOX)}" '
        f'fill="currentColor" '
        f'aria-hidden="true" focusable="false">{body}</svg>'
    )
