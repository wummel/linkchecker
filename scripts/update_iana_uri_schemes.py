import sys
import re
import csv
import requests

iana_uri_schemes = "https://www.iana.org/assignments/uri-schemes/uri-schemes.xhtml"
# CSV format: URI Scheme,Template,Description,Reference
csv_iana_uri_schemes_permanent = 'https://www.iana.org/assignments/uri-schemes/uri-schemes-1.csv'
csv_iana_uri_schemes_provisional = 'https://www.iana.org/assignments/uri-schemes/uri-schemes-2.csv'
csv_iana_uri_schemes_historical = 'https://www.iana.org/assignments/uri-schemes/uri-schemes-3.csv'

iana_uri_schemes_permanent = {}
iana_uri_schemes_provisional = {}
iana_uri_schemes_historical = {}
iana_uri_schemes_other = {
    "clsid":      "Microsoft specific",
    "find" :      "Mozilla specific",
    "isbn" :      "ISBN (int. book numbers)",
    "javascript": "JavaScript",
}

filter_uri_schemes_permanent = (
    "file",
    "ftp",
    "http",
    "https",
    "mailto",
    "news",
    "nntp",
)

template = '''
# from %(uri)s
ignored_schemes_permanent = r"""
%(permanent)s
"""

ignored_schemes_provisional = r"""
%(provisional)s
"""

ignored_schemes_historical = r"""
%(historical)s
"""

ignored_schemes_other = r"""
%(other)s
"""

ignored_schemes = "^(%%s%%s%%s%%s)$" %% (
    ignored_schemes_permanent,
    ignored_schemes_provisional,
    ignored_schemes_historical,
    ignored_schemes_other,
)
ignored_schemes_re = re.compile(ignored_schemes, re.VERBOSE)

is_unknown_scheme = ignored_schemes_re.match
'''

def main(args):
    parse_csv_file(csv_iana_uri_schemes_permanent, iana_uri_schemes_permanent)
    parse_csv_file(csv_iana_uri_schemes_provisional, iana_uri_schemes_provisional)
    parse_csv_file(csv_iana_uri_schemes_historical, iana_uri_schemes_historical)
    for scheme in iana_uri_schemes_other:
        if (scheme in iana_uri_schemes_permanent or
            scheme in iana_uri_schemes_provisional or
            scheme in iana_uri_schemes_historical):
            raise ValueError(scheme)
    for scheme in filter_uri_schemes_permanent:
        if scheme in iana_uri_schemes_permanent:
            del iana_uri_schemes_permanent[scheme]
    args = dict(
        uri = iana_uri_schemes,
        permanent = get_regex(iana_uri_schemes_permanent),
        provisional = get_regex(iana_uri_schemes_provisional),
        historical = get_regex(iana_uri_schemes_historical), 
        other = get_regex(iana_uri_schemes_other),
    )
    res = template % args
    print res
    return 0


def get_regex(schemes):
    expr = ["|%s # %s" % (re.escape(scheme).ljust(10), description)
            for scheme, description in sorted(schemes.items())]
    return "\n".join(expr)


def parse_csv_file(url, res):
    """Parse given URL and write res with {scheme -> description}"""
    response = requests.get(url, stream=True)
    reader = csv.reader(response.iter_lines())
    first_row = True
    for row in reader:
        if first_row:
            # skip first row
            first_row = False
        else:
            scheme, template, description, reference = row
            res[scheme] = description


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
