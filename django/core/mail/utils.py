"""
Email message and email sending related helper functions.
"""

import socket
from email.utils import formataddr


# Cache the hostname, but do it lazily: socket.getfqdn() can take a couple of
# seconds, which slows down the restart of the server.
class CachedDnsName(object):
    def __str__(self):
        return self.get_fqdn()

    def get_fqdn(self):
        if not hasattr(self, '_fqdn'):
            self._fqdn = socket.getfqdn()
        return self._fqdn


def soft_formataddr(value):
    """
    Attempts to format the value as if it was a 2-tuple of the form
    ``(realname, email_address)`` as a string value suitable for a To or Cc
    header.

    If the value was not a list-like object with a length of 2, the value will
    be returned unaltered.
    """
    try:
        name, email = value
    except (TypeError, ValueError):
        return value
    return formataddr((name, email))


DNS_NAME = CachedDnsName()
