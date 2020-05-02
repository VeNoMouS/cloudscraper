import logging
import re

# ------------------------------------------------------------------------------- #


def template(body, domain):
    BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

    try:
        js = re.search(
            r'setTimeout\(function\(\){\s+(.*?a\.value = \S+)',
            body,
            re.M | re.S
        ).group(1)
    except Exception:
        raise ValueError('Unable to identify Cloudflare IUAM Javascript on website. {}'.format(BUG_REPORT))

    jsEnv = '''
        String.prototype.italics=function(str) {{return "<i>" + this + "</i>";}};
        var document = {{
            createElement: function () {{
                return {{ firstChild: {{ href: "https://{domain}/" }} }}
            }},
            getElementById: function () {{
                return {{"innerHTML": "{innerHTML}"}};
            }}
        }};
    '''

    try:
        innerHTML = re.search(
            r'<div(?: [^<>]*)? id="([^<>]*?)">([^<>]*?)</div>',
            body,
            re.MULTILINE | re.DOTALL
        )
        innerHTML = innerHTML.group(2) if innerHTML else ''

    except:  # noqa
        logging.error('Error extracting Cloudflare IUAM Javascript. {}'.format(BUG_REPORT))
        raise

    return '{}{}'.format(
        re.sub(
            r'\s{2,}',
            ' ',
            jsEnv.format(
                domain=domain,
                innerHTML=innerHTML
            ),
            re.MULTILINE | re.DOTALL
        ),
        js
    )

# ------------------------------------------------------------------------------- #
