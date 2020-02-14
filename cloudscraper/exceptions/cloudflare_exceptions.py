# ------------------------------------------------------------------------------- #


class Cloudflare_Loop_Protection(Exception):
    """
    Raise error for recursive depth protection
    """


class Cloudflare_Block(Exception):
    """
    Raise error for Cloudflare 1020 block
    """


class Cloudflare_Error_IUAM(Exception):
    """
    Raise error for problem extracting IUAM paramters from Cloudflare payload
    """


class Cloudflare_Error_reCaptcha(Exception):
    """
    Raise error for problem extracting reCaptcha paramters from Cloudflare payload
    """


class Cloudflare_reCaptcha_Provider(Exception):
    """
    Raise error for reCaptcha from Cloudflare, no provider loaded.
    """
