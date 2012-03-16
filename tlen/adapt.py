import urllib, functools, logging

from pyxmpp2.stanza import Stanza
from pyxmpp2.message import Message
from pyxmpp2.presence import Presence
from pyxmpp2.jid import JID

logger = logging.getLogger('tlen')

def tlen_decode(fun):
	@functools.wraps(fun)
	def wrapper(element):
		for e in element:
			if e.text:
				text = urllib.unquote(e.text.replace('+', ' '))
				e.text = text.decode('iso8859-2')
		return fun(element)

	return wrapper

def tlen_encode(text):
	text = urllib.quote(text.encode('iso8859-2', 'ignore'))
	return text

@tlen_decode
def incoming_element(element):
	return element

def outgoing_stanza(stanza):
	if isinstance(stanza, Message):
		return outgoing_message(stanza)
	elif isinstance(stanza, Presence):
		return outgoing_presence(stanza)
	else:
		return stanza

def outgoing_message(stanza):
	if stanza.body:
		body = tlen_encode(stanza.body)
		stanza = Message(stanza_type = stanza.stanza_type,
				from_jid = stanza.from_jid, to_jid = stanza.to_jid,
				subject = stanza.subject, body = body,
				thread = stanza.thread)
		logger.debug('====== body: %r', stanza.body)
	return stanza

def outgoing_presence(stanza):
	# Tlen needs a <show> tag. If not present, use 'available'
	if not stanza.show:
		stanza.show = 'available'
	if stanza.status:
		stanza.status = tlen_encode(stanza.status)
	return stanza

