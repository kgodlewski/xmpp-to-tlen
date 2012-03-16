import urllib, functools, logging

from pyxmpp2.stanza import Stanza
from pyxmpp2.message import Message
from pyxmpp2.presence import Presence
from pyxmpp2.jid import JID

logger = logging.getLogger('tlen')

def tlen_decode(text):
	text = urllib.unquote(text.replace('+', ' '))
	text = text.decode('iso8859-2')
	return text

def tlen_decode_element(element):
	if element.text:
		element.text = tlen_decode(element.text)

	for child in element:
		tlen_decode_element(child)

def incoming_element(element):
	"""
	Adapt an incoming XML element. Return the element.
	"""

	if element.tag.endswith('iq'):
		return incoming_iq_element(element)

	tlen_decode_element(element)
	return element

def incoming_iq_element(iq):
	query = iq.find('{jabber:iq:roster}query')
	if query is not None:
		return incoming_roster(iq, query)

	return element

def incoming_roster(iq, query):
	for item in query.findall('{jabber:iq:roster}item'):
		name = item.get('name')
		if name:
			name = item.set('name', tlen_decode(name))
	return iq

"""
def tlen_decoded(fun):
	@functools.wraps(fun)
	def wrapper(element):
		tlen_decode_element(element)
		return fun(element)

	return wrapper
"""

def tlen_encode(text):
	"""
	Return a new string containing `text` encoded to meet
	the Tlen client/server requirements.
	"""

	text = urllib.quote(text.encode('iso8859-2', 'ignore'))
	return text

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
	return stanza

def outgoing_presence(stanza):
	# Tlen needs a <show> tag. If not present, use 'available'
	if not stanza.show:
		stanza.show = 'available'
	if stanza.status:
		stanza.status = tlen_encode(stanza.status)
	return stanza

