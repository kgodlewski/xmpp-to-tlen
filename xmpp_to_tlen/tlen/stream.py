import logging, sha, urllib
import gevent, gevent.socket

from pyxmpp2.xmppparser import StreamReader, XMLStreamHandler
from pyxmpp2.jid import JID
from pyxmpp2.stanza import Stanza
from pyxmpp2.stanzaprocessor import stanza_factory
from pyxmpp2 import constants

from xmpp_to_tlen.blocklist import BlockList

logger = logging.getLogger('xmpp_to_tlen.tlen.stream')

class TlenError(Exception):
	pass

import adapt, avatar

class TlenAuthError(TlenError):
	pass

class TlenTransport(object):
	def connect(self, callback):
		pass

	def send(self, data):
		pass

	def recv(self):
		pass

	def close(self):
		pass


class GeventTransport(TlenTransport):
	def __init__(self):
		super(GeventTransport, self).__init__()

		self.sock = None

	def connect(self, callback):
		for x in xrange(3):
			# Try connecting a few times. Helps when the machine wakes
			# up from sleep/hibernation.
			try:
				self.sock = gevent.socket.create_connection(('193.17.41.53', 80))
			except Exception as e:
				gevent.sleep(x + 1)
				continue

			callback()
			return True
		return False

	def send(self, data):
		if isinstance(data, Stanza):
			data = adapt.outgoing_stanza(data)
			data = data.serialize()

		self.sock.send(data)
	
	def recv(self):
		try:
			return self.sock.recv(4096)
		except Exception as e:
			logger.error('recv error: %s', e)
			return None

class TlenStream(XMLStreamHandler):
	def __init__(self, jid, password, resource, avatars=None):
		super(TlenStream, self).__init__()

		self.authenticated = False
		self.session_id = None
		self.uplink = None

		# Set by adapt.incoming_avatar
		self.avatar_token = None

		self.jid = jid
		self.resource = resource
		self._password = password
		self._transport = GeventTransport()
		self._stream_reader = StreamReader(self)
		self._avatars = avatars

		self._closed = False

		self.blocklist = BlockList(self.jid.as_string())

	def wait_for_auth(self):
		# FIXME, ugly
		while not self.authenticated:
			if self._closed:
				return False

			gevent.sleep(0.5)

		gevent.spawn(self._pinger)

		return True

	def start(self):
		gevent.spawn(self.connect)

	def connect(self):
		if not self._transport.connect(self._connected):
			self._closed = True
			self._transport.close()

	def close(self):
		self._transport.send('</s>')
		self._closed = True
		self._transport.close()

	def send(self, data):
		if isinstance(data, Stanza):
			data = adapt.outgoing_stanza(data)
			data = data.serialize()

		logger.debug('client send %s', data)
		self._transport.send(data)

	def _pinger(self):
		# XXX: Race condition? Dunno how gevent handles this internally
		while True:
			gevent.sleep(30)

			if self._closed:
				break
			try:
				self._transport.send(' ')
			except Exception as e:
				logger.error('Tlen transport error: %s', e)
				self.close()
				break

	def _loop(self):
		logger.debug('loop')
		while not self._closed:
			data = self._transport.recv()
			logger.debug('data=%s', data)
			if not data:
				break
			self._stream_reader.feed(data)
		logger.debug('tlen loop done')

	def _connected(self):
		logger.debug('connected')
		self._transport.send('<s v="9" t="7">')
		self._loop()

	def _auth_digest(self):
		magic1 = 0x50305735
		magic2 = 0x12345671
		s = 7;

		for c in self._password:
			if c in (' ', '\t'):
				continue
			magic1 ^= (((magic1 & 0x3f) + s) * ord(c)) + (magic1 << 8)
			magic2 += (magic2 << 8) ^ magic1
			s += ord(c)

		magic1 &= 0x7fffffff
		magic2 &= 0x7fffffff

		code = '%08x%08x' % (magic1, magic2)

		sha1 = sha.new(self.session_id + code)
		return sha1.hexdigest()

	#
	# XMLStreamHandler API
	#
	def stream_start(self, element):
		self.session_id = element.get('i')
		
		# Authorize with the Tlen server; this is tlen-specific,
		# and can't be handled the usual XMPP way.
		xml = '<iq type="set" id="%s"><query xmlns="jabber:iq:auth">'
		xml += '<username>%s</username><digest>%s</digest><resource>%s</resource>'
		xml += '<host>tlen.pl</host></query></iq>'

		xml = xml % (self.session_id, self.jid.local, self._auth_digest(), self.resource)
		self._transport.send(xml)

	def stream_element(self, element):
		if self.authenticated:
			element = adapt.incoming_element(self, element)
			self._uplink_element(element)
		else:
			if element.tag != 'iq':
				raise TlenAuthError('Unexpected server response: ' + stanza.serialize())
			typ = element.get('type')
			if typ == 'result':
				self.authenticated = True
			else:
				logger.warning('Tlen server denied authentication (account: %s)', self.jid.as_string())
				self.close()

	def stream_end(self):
		self._closed = True
		self._transport.close()

	def _uplink_element(self, element):
		# logger.debug('uplink %s', element)
		# The element processing might be deferred
		if element is None:
			return

		element = self._add_namespaces(element)
		self.uplink.send(stanza_factory(element))

	def _add_namespaces(self, element):
		if element.tag[0] != '{':
			element.tag = constants.STANZA_CLIENT_QNP + element.tag

		for sub in element:
			logging.debug('fixing %s', sub)
			if not sub.tag:
				continue
			if sub.tag[0] != '{':
				sub.tag = constants.STANZA_CLIENT_QNP + sub.tag
		return element

	def get_avatar(self, jid, callback=None, *args):
		jid = jid.as_string()
		if not callback:
			return self._avatars.get(self.avatar_token, jid)
		else:
			gevent.spawn(self._get_avatar_async, jid, callback, *args)

	def _get_avatar_async(self, jid, callback, *args):
		try:
			logger.debug('async avatar get, jid=%s', jid)
			avatar = self._avatars.get(self.avatar_token, jid)
		except TlenError as e:
			logger.error('Error while downloading avatar: %s', e)
			avatar = None

		callback(avatar, *args)
