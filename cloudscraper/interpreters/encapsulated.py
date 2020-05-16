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

    jsEnv = '''String.prototype.italics=function(str) {{return "<i>" + this + "</i>";}};
        var subVars= {{{subVars}}};
        var document = {{
            createElement: function () {{
                return {{ firstChild: {{ href: "https://{domain}/" }} }}
            }},
            getElementById: function (str) {{
                return {{"innerHTML": subVars[str]}};
            }}
        }};
    '''

    try:
        k = re.search(r" k\s*=\s*'(?P<k>\S+)';", body).group('k')
        r = re.compile(r'<div id="{}(?P<id>\d+)">\s*(?P<jsfuck>[^<>]*)</div>'.format(k))

        subVars = ''
        for m in r.finditer(body):
            subVars = '{}\n\t\t{}{}: {},\n'.format(subVars, k, m.group('id'), m.group('jsfuck'))
        subVars = subVars[:-2]

    except:  # noqa
        logging.error('Error extracting Cloudflare IUAM Javascript. {}'.format(BUG_REPORT))
        raise

    return '{}{}'.format(
        re.sub(
            r'\s{2,}',
            ' ',
            jsEnv.format(
                domain=domain,
                subVars=subVars
            ),
            re.MULTILINE | re.DOTALL
        ),
        js
    )

# ------------------------------------------------------------------------------- #
