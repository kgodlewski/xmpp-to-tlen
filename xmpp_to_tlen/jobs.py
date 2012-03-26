import logging, gevent, sys
from xml.etree import ElementTree

from tlen import avatar

logger = logging.getLogger('xmpp_to_tlen.jobs')

class Job(object):
	def __init__(self, xmpp):
		super(Job, self).__init__()

		self.xmpp = xmpp
		self.tlen = xmpp.tlen

	def perform(self, *args, **kwargs):
		raise NotImplementedError()

class VCardGet(Job):
	def perform(self, *args, **kwargs):
		# XXX: This will include tuba exchange too
		iq, = args

		# If no jid was specified, the client requests its own VCard
		jid = iq.to_jid or self.tlen.jid

		logger.debug('to_jid: local: %s, domain: %s, full: %s', jid.local,
			jid.domain, jid.as_string())

		response = iq.make_result_response()

		if jid.local and jid.domain:
			gevent.spawn(self._get_avatar, jid.as_string(), response)
			return None

		return response

	def _get_avatar(self, sjid, response):
		try:
			avdata = self.xmpp.avatars.get(self.tlen.avatar_token, sjid)
		except Exception as e:
			logger.error('Error while fetching avatar:', exc_info=sys.exc_info())
			return

		vcard = ElementTree.Element('{vcard-temp}vCard')
		photo = ElementTree.Element('{vcard-temp}PHOTO')
		typ = ElementTree.Element('{vcard-temp}TYPE')
		typ.text = avdata.content_type
		photo.append(typ)

		binval = ElementTree.Element('{vcard-temp}BINVAL')
		binval.text = avdata.data
		photo.append(binval)

		vcard.append(photo)
		response.add_payload(vcard)

		self.xmpp.stream.send(response)

