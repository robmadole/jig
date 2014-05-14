def green_bold(payload):
    """
    Format payload as green.
    """
    return u'\x1b[32;1m{0}\x1b[39;22m'.format(payload)


def yellow_bold(payload):
    """
    Format payload as yellow.
    """
    return u'\x1b[33;1m{0}\x1b[39;22m'.format(payload)


def red_bold(payload):
    """
    Format payload as red.
    """
    return u'\x1b[31;1m{0}\x1b[39;22m'.format(payload)
