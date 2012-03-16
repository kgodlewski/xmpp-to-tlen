import urllib, functools, logging
from xml.etree import ElementTree

from pyxmpp2.stanza import Stanza
from pyxmpp2.message import Message
from pyxmpp2.presence import Presence
from pyxmpp2.jid import JID

from xmpp_to_tlen import const

logger = logging.getLogger('xmpp_to_tlen.tlen.adapt')

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

	logger.debug('element tag=%s', element.tag)

	if element.tag == 'message':
		return incoming_message(element)
	elif element.tag == 'm':
		return incoming_chatstate(element)
	elif element.tag == 'iq':
		return incoming_iq_element(element)

	tlen_decode_element(element)
	return element

def incoming_chatstate(element):
	"""
	Transform an <m /> tag to a proper XMPP chat notification.

	`element` is one of:
		<m tp='t' f='from-jid' /> -- equivalent to <composing />
		<m tp='u' f='from-jid' /> -- equivalent to <paused /> XXX: really?
	"""

	logger.debug('chatstate')

	msg = ElementTree.Element('message')
	msg.set('from', element.get('f'))

	if element.get('tp') == 't':
		child = 'composing'
	else:
		child = 'paused'

	child = ElementTree.Element(const.CHATSTATES_NS_QNP + child)
	msg.append(child)

	return msg

def incoming_message(message):
	tlen_decode_element(message)
	active = ElementTree.Element(const.CHATSTATES_NS_QNP + 'active')
	message.append(active)
	return message

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
	"""
	Adapt an outgoint Message stanza. Either properly encode the
	message contents, or convert it to a typing notification,
	if no body is included.
	"""

	logger.debug('outgoing message, body=%r', stanza.body)

	if stanza.body:
		body = tlen_encode(stanza.body)
		# This strips all additional XML tags, like html part etc.
		stanza = Message(stanza_type = stanza.stanza_type,
				from_jid = stanza.from_jid, to_jid = stanza.to_jid,
				subject = stanza.subject, body = body,
				thread = stanza.thread)
		return stanza

	# If the message had no body, assume it's a typing notification.

	xml = stanza.as_xml()

	for chatstate in xml:
		if chatstate.tag.startswith(const.CHATSTATES_NS_QNP):
			break
	# If no chatstate found, give up and send unmodified stanza
	else:
		return stanza

	logger.debug('chatstate=%s', chatstate)

	# Need to add a namespace to keep Stanza happy
	# For XML format, see docstring for incoming_chatstate()
	m = ElementTree.Element('{jabber:client}m')
	m.set('to', stanza.to_jid.as_unicode())

	if chatstate.tag.endswith('composing'):
		m.set('tp', 't')
	else:
		m.set('tp', 'u')

	return Stanza(m)

def outgoing_presence(stanza):
	# Tlen needs a <show> tag. If not present, use 'available'
	if not stanza.show:
		stanza.show = 'available'
	if stanza.status:
		stanza.status = tlen_encode(stanza.status)
	return stanza
