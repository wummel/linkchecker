import re,StringUtil

imgtag_re = re.compile("(?i)\s+alt\s*=\s*(?P<name>(\".*?\"|'.*?'|[^\s>]+))", re.DOTALL)
img_re = re.compile("(?i)<\s*img\s+.*>", re.DOTALL)
href_re = re.compile("(?i)(?P<name>.*?)</a\s*>", re.DOTALL)

def image_name(txt):
    name = ""
    mo = imgtag_re.search(txt)
    if mo:
        #print "DEBUG:", `mo.group(0)`
        name = StringUtil.stripQuotes(mo.group('name').strip())
        name = StringUtil.remove_markup(name)
        name = StringUtil.unhtmlify(name)
    #print "NAME:", `name`
    return name


def href_name(txt):
    name = ""
    mo = href_re.search(txt)
    if mo:
        #print "DEBUG:", `mo.group(0)`
        name = mo.group('name').strip()
        if img_re.search(name):
            name = image_name(name)
        name = StringUtil.remove_markup(name)
        name = StringUtil.unhtmlify(name)
    #print "NAME:", `name`
    return name
