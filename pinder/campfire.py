"Campfire client"
import httplib2
try:
    import json
except ImportError:
    import simplejson as json
import urlparse

from pinder.exc import HTTPUnauthorizedException, HTTPNotFoundException
from pinder.room import Room

VERSION = "0.8b"


class Campfire(object):
    """Initialize a Campfire client with the given subdomain and token.
     Accepts a third boolean parameter to enable SSL (defaults to false)."""
    def __init__(self, subdomain, token, ssl=False):
        # The Campfire's subdomain.
        self.subdomain = subdomain
        self._token = token
        schema = ('http', 'https')[ssl==True]
        # The URI object of the Campfire account.
        self.uri = urlparse.urlparse(
            "%s://%s.campfirenow.com" % (schema, self.subdomain))
        self._http = httplib2.Http(timeout=5)
        self._http.force_exception_to_status_code = True
        self._http.add_credentials(token, 'X')

    def rooms(self):
        "Returns the rooms available in the Campfire account"
        return self._get('rooms')['rooms']

    def rooms_names(self):
        "Returns the rooms names available in the Campfire account"
        rooms = self._get('rooms')['rooms']
        return sorted([room['name'] for room in rooms])
        
    def room(self, room_id):
        "Returns the room info for the room with the given id."
        data = self._get("room/%s" % room_id)['room']
        return Room(self, room_id, data)

    def find_room_by_name(self, name):
        """Finds a Campfire room with the given name.
        
        Returns a Room instance if found, None otherwise."""
        rooms = self.rooms()
        for room in rooms:
            if room['name'] == name:
                return Room(self, room['id'], data=room)

    def users(self, *rooms_ids):
        "Returns info about users in any room or in the given room(s)."
        rooms = self.rooms()
        users = []
        for room in rooms:
            if not rooms_ids or room['id'] in rooms_ids:
                if room.get('users'):
                    users.append(room.get('users'))
        return users
        
    def user(self, user_id):
        "Returns info about the user with the given user_id."
        return self._get("users/%s" % user_id)
        
    def me(self):
        "Returns info about the authenticated user."
        return self._get("users/me")['user']
        
    def search(self, term):
        "Returns all the messages containing the given term."
        return self._get("search/%s" % term)['messages']

    def _uri_for(self, path=''):
        return "%s/%s.json" % (urlparse.urlunparse(self.uri), path)
        
    def _request(self, method, path, data=None, additional_headers=None):
        additional_headers = additional_headers or dict()
        data = json.dumps(data or dict())
        
        headers = {}
        headers['user-agent'] = 'Pinder/%s' % VERSION
        headers['content-type'] = 'application/json'
        headers['content-length'] = str(len(data))
        headers.update(additional_headers)

        if method in ('GET', 'POST', 'PUT', 'DELETE'):
            location = self._uri_for(path)
        else:
            raise Exception('Unsupported HTTP method: %s' % method)

        response, body = self._http.request(location, method, data, headers)
            
        if response.status == 401:
            raise HTTPUnauthorizedException(
                "You are not authorized to access the resource: '%s'" % path)
        elif response.status == 404:
            raise HTTPNotFoundException(
                "The resource you are looking for does not exist (%s)" % path)

        try:
            return json.loads(body)
        except ValueError, e:
            if response.status != 200:
                raise Exception("Something did not work fine: %s - %s" % (
                    str(e), body))

    def _get(self, path='', data=None, headers=None):
        return self._request('GET', path, data, headers)

    def _post(self, path, data=None, headers=None):
        return self._request('POST', path, data, headers)

    def _put(self, path, data=None, headers=None):
        return self._request('PUT', path, data, headers)
