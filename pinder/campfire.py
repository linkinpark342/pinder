import json
import urllib
import urlparse

import httplib2

from exc import HTTPUnauthorizedException, HTTPNotFoundException

__version__ = 'X.Y.Z'

class Campfire(object):
    "Initialize a Campfire client with the given subdomain and token."
    def __init__(self, subdomain, token):
        # The Campfire's subdomain.
        self.subdomain = subdomain
        self._token = token
        # The U{urlparsed<http://docs.python.org/library/urlparse.html#urlparse.urlparse>} URI of the Campfire account.
        self.uri = urlparse.urlparse("http://%s.campfirenow.com" % self.subdomain)
        self._c = httplib2.Http(timeout=5)
        self._c.force_exception_to_status_code = True
        self._c.add_credentials(token, 'X')

    def rooms(self):
        """Returns the rooms available in the Campfire account.

        Returns a list of the names of the rooms."""
        return self._get('rooms.json')['rooms']        

    def _uri_for(self, path=''):
        return "%s/%s" % (urlparse.urlunparse(self.uri), path)
        
    def _request(self, method, path, data={}, **options):
        headers = {}
        headers['User-Agent'] = 'Pinder/%s' % __version__

        if method == 'GET':
            location = self._uri_for(path)
        else:
            raise Exception('Unsupported HTTP method: %s' % method)

        response, body = self._c.request(
            location, method, urllib.urlencode(data), headers)

        if response.status == 401:
            raise HTTPUnauthorizedException(
                "You are not authorized to access the resource: '%s'" % path)
        elif response.status == 404:
            raise HTTPNotFoundException(
                "The resource you are looking for does not exist (%s)" % path)

        if body:
            return json.loads(body)
        else:
            return ''

    def _post(self, path, data={}, **options):
        return self._request('POST', path, data, **options)

    def _get(self, path=''):
        return self._request('GET', path)
