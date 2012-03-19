import logging, gevent
from xml.etree import ElementTree

from pyxmpp2.mainloop.interfaces import EventHandler, event_handler, QUIT
from pyxmpp2.session import SessionHandler
from pyxmpp2.binding import ResourceBindingHandler
from pyxmpp2.jid import JID
from pyxmpp2.message import Message

from pyxmpp2.streamevents import DisconnectedEvent, AuthenticatedEvent, StreamRestartedEvent
from pyxmpp2.streamevents import AuthorizedEvent

from pyxmpp2.interfaces import (TimeoutHandler, timeout_handler,
	iq_get_stanza_handler, iq_set_stanza_handler, XMPPFeatureHandler,
	presence_stanza_handler, message_stanza_handler)

from pyxmpp2.stanzapayload import XMLPayload
from pyxmpp2.stanzaprocessor import StanzaProcessor

from pyxmpp2.streambase import StreamBase
from pyxmpp2.streamsasl import StreamSASLHandler

from pyxmpp2.settings import XMPPSettings

from tlen.stream import TlenStream

logger = logging.getLogger('xmpp_to_tlen.proxy')

from const import DISCO_INFO_NS_QNP, CHATSTATES_NS

class Server(StanzaProcessor, EventHandler, TimeoutHandler, XMPPFeatureHandler):
	"""
	The XMPP end of the proxy.

	Handles local XMPP client connections. Forwards stanzas from the 
	client to the Tlen server, and the other way around. Stanzas are 
	adapted to achieve maximum satisfaction on both sides ;)
	"""

	def __init__(self, transport):
		StanzaProcessor.__init__(self)

		logger.debug('-- New connection')

		self.settings = XMPPSettings()

		self.handlers = [self, ResourceBindingHandler(self.settings)]
		self.stream = StreamBase(u"jabber:client", self, self.handlers, self.settings)
		self.stream.set_authenticated(JID(domain='tlen.pl'))

		self.tlen = None
		self.transport = transport
		self.stream.receive(self.transport, 'tlen.pl')

		self.uplink = self.stream
		self.stream.set_authenticated(JID(domain='tlen.pl'))

		# self.clear_response_handlers()
		# self.setup_stanza_handlers(self.handlers, "pre-auth")

	@event_handler(AuthenticatedEvent)
	def authenticated(self, event):
		self.setup_stanza_handlers(self.handlers, 'post-auth')

	@event_handler(DisconnectedEvent)
	def disconnected(self, event):
		logger.debug('Client disconnected')
		if self.tlen:
			self.tlen.close()
		return QUIT

	# Stanza handlers. Except for authorization stuff, they
	# push everything to the TlenClient. Anything that needs
	# fixing up before being sent to the server is performed
	# in TlenClient.send()

	@iq_get_stanza_handler(XMLPayload, '{jabber:iq:auth}query')
	def handle_auth_get(self, stanza):
		logger.debug('auth get %s', stanza.serialize())
		resp = stanza.make_result_response()

		query = ElementTree.Element('{jabber:iq:auth}query')
		for x in ('username', 'password', 'resource'):
			query.append(ElementTree.Element('{jabber:iq:auth}' + x))

		resp.add_payload(query)

		return resp
		
	@iq_set_stanza_handler(XMLPayload, '{jabber:iq:auth}query')
	def handle_auth_set(self, stanza):
		"""
		This is the part that actually starts the Tlen end
		of the proxy.

		We're expecting PLAIN XMPP authentication here, so we
		can grab the auth data and log in to Tlen.pl, on behalf
		of the user.
		"""

		logger.debug('auth set %s', stanza.serialize())

		query = stanza.get_payload(None, 'query').as_xml()
		logger.debug('query=%s, %s', query, list(query))

		# XXX: Assuming the client will use legacy auth
		username = query.findtext('{jabber:iq:auth}username')
		password = query.findtext('{jabber:iq:auth}password')
		resource = query.findtext('{jabber:iq:auth}resource')

		if not username or not password:
			# XXX
			return stanza.make_error_response('bad-request')

		self.tlen = TlenStream(JID(username, 'tlen.pl'), password, resource)
		self.tlen.uplink = self.stream
		self.tlen.start()

		if self.tlen.wait_for_auth():
			return stanza.make_result_response()
		else:
			# XXX: is this code ok?
			return stanza.make_error_response('not-authorized')

	@iq_get_stanza_handler(XMLPayload, '{jabber:iq:roster}query')
	def handle_roster_get(self, stanza):
		self.tlen.send(stanza)

	@iq_set_stanza_handler(XMLPayload, '{jabber:iq:roster}query')
	def handle_roster_set(self, stanza):
		self.tlen.send(stanza)

	@iq_get_stanza_handler(XMLPayload, DISCO_INFO_NS_QNP + 'query')
	def handle_disco_get(self, stanza):
		"""
		Handle feature discovery on behalf of a @tlen.pl user.
		"""

		logger.debug('DISCO INFO get, jid=%s', stanza.to_jid)

		resp = stanza.make_result_response()

		# Target is client entity
		if stanza.to_jid.domain:
			logger.debug('disco to client')
			query = ElementTree.Element(DISCO_INFO_NS_QNP + 'query')
			query.append(ElementTree.Element(DISCO_INFO_NS_QNP + 'feature', var=CHATSTATES_NS))

			resp.add_payload(query)

		return resp

	@iq_get_stanza_handler(XMLPayload, '{vcard-temp}vCard')
	def handle_vcard_get(self, iq):
		logger.debug('vCard: %s', iq)

		resp = iq.make_result_response()

		if not iq.to_jid:
			return resp

		if iq.to_jid.local and iq.to_jid.domain:
			avatar = self.tlen.get_avatar(iq.to_jid)
			vcard = ElementTree.Element('{vcard-temp}vCard')
			photo = ElementTree.Element('{vcard-temp}PHOTO')
			typ = ElementTree.Element('{vcard-temp}TYPE')
			typ.text = avatar.content_type
			photo.append(typ)

			binval = ElementTree.Element('{vcard-temp}BINVAL')
			binval.text = avatar.data
			photo.append(binval)

			vcard.append(photo)
			resp.add_payload(vcard)

		return resp


	@presence_stanza_handler()
	def handle_presence(self, stanza):
		logger.debug('handle presence=%s', stanza.serialize())
		self.tlen.send(stanza)

	@presence_stanza_handler('subscribed')
	def handle_presence_subscribed(self, stanza):
		logger.debug('handle presence subscr=%s', stanza.serialize())
		self.tlen.send(stanza)

	@presence_stanza_handler('subscribe')
	def handle_presence_subscribe(self, stanza):
		logger.debug('handle presence subscr=%s', stanza.serialize())
		self.tlen.send(stanza)

	@presence_stanza_handler('unsubscribe')
	def handle_presence_unsubscribe(self, stanza):
		logger.debug('handle presence subscr=%s', stanza.serialize())
		self.tlen.send(stanza)

	@presence_stanza_handler('unsubscribed')
	def handle_presence_unsubscribed(self, stanza):
		logger.debug('handle presence subscr=%s', stanza.serialize())
		self.tlen.send(stanza)

	@message_stanza_handler()
	def handle_message(self, stanza):
		self.tlen.send(stanza)

