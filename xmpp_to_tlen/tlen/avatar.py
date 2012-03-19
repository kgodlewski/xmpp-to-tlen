import gevent, urllib2, collections, logging
import sha, md5

from stream import TlenError

logger = logging.getLogger('xmpp_to_tlen.avatar')

"""
Avatar data container.

 :Ivariables:
	- `data`: Base64-encoded file data
	- `sha1`
	- `md5`
	- `content_type`: Content-Type returned by the avatar server
"""
AvatarData = collections.namedtuple('AvatarData', 'data sha1 md5 content_type')

class Avatars(object):
	def __init__(self):
		super(Avatars, self).__init__()

		self.cache = {}
		self._downloads = {}
		
	def get(self, token, jid, md5=None):
		try:
			data = self.cache[jid]
			if md5 is None or data.md5 == md5:
				return data
		except KeyError:
			pass

		if jid not in self._downloads:
			self._downloads[jid] = gevent.spawn(self._do_download, token, jid)
		return self._downloads[jid].get()

	def _do_download(self, token, jid):
		logger.debug('do download: %s', jid)
		assert '@' in jid

		local, domain = jid.split('@')
		try:
			url = 'http://mini10.tlen.pl/avatar/%s/0?t=%s' % (local, token)
			logger.debug('url=%s', url)
			reply = urllib2.urlopen(url)
			img = reply.read()
			data = AvatarData(img.encode('base64'), sha.new(img).hexdigest(),
				md5.new(img).hexdigest(), reply.info().typeheader)

			self.cache[jid] = data
			return data
		except Exception as e:
			logger.error('Error: %s', e)
			raise TlenError('Error downloading avatar for %s', jid)
