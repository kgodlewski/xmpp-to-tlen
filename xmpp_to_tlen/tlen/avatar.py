import gevent, urllib2, collections, logging, sys, os, pickle, errno
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

		self._local_cache = _LocalCache()
		self.cache = self._local_cache.cache
		self._downloads = {}
		
	def get(self, token, jid, match_md5=None):
		"""
		Fetch AvatarData. If already downloaded, returns data from cache.
		If downloading, will block the caller until the download completes.

		If `match_md5` is not None, the avatar will be returned only if its
		md5 sum matches. A new avatar will be downloaded otherwise.
		"""
		
		try:
			data = self.cache[jid]
			logger.debug('Avatar for %s in cache', jid)
			if match_md5 is None or data.md5 == match_md5:
				logger.debug('md5 matches')
				return data
		except KeyError:
			pass

		# Allow one concurrent download for the jid.
		if jid not in self._downloads:
			self._downloads[jid] = gevent.spawn(self._do_download, token, jid)

		logger.debug('++ Concurrent downloads now: %i', len(self._downloads))

		return self._downloads[jid].get()

	def _do_download(self, token, jid):
		logger.debug('do download: %s', jid)
		assert '@' in jid

		local, domain = jid.split('@')
		try:
			url = 'http://mini10.tlen.pl/avatar/%s/0?t=%s' % (local, token)
			reply = urllib2.urlopen(url)
			img = reply.read()
			data = AvatarData(img.encode('base64'), sha.new(img).hexdigest(),
				md5.new(img).hexdigest(), reply.info().typeheader)

			self.cache[jid] = data
			self._local_cache.save()

			del self._downloads[jid]
			logger.debug('-- Concurrent downloads now: %i', len(self._downloads))

			return data
		except Exception as e:
			del self._downloads[jid]
			logger.debug('-- Concurrent downloads now: %i', len(self._downloads))

			logger.error('Error: %s', e)
			raise TlenError('Error downloading avatar for ' + jid)

class _LocalCache(object):
	def __init__(self):
		super(_LocalCache, self).__init__()

		home = os.getenv('HOME')
		if sys.platform == 'darwin':
			self._base_dir = os.path.join(home, 'Library', 'Caches', 'xmpp-to-tlen')
		else:
			self._base_dir = os.path.join(home, '.xmpp-to-tlen', 'cache')

		try:
			os.makedirs(self._base_dir)
		except OSError as e:
			if e.errno == errno.EEXIST:
				pass

		self._path = os.path.join(self._base_dir, 'avatars')

		try:
			self.cache = pickle.load(open(self._path))
		except Exception:
			self.cache = {}

	def save(self):
		pickle.dump(self.cache, open(self._path, 'w'))

