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

class VCard(Job):
	def perform(self, *args, **kwargs):
		# XXX: This will include tuba exchange too
		iq, = args

		resp = iq.make_result_response()

		if not iq.to_jid:
			# XXX: My own v-card
			return resp

		logger.debug('to_jid: local: %s, domain: %s, full: %s', iq.to_jid.local,
			iq.to_jid.domain, iq.to_jid.as_string())

		if iq.to_jid.local and iq.to_jid.domain:
			gevent.spawn(self._get_avatar, iq.to_jid.as_string(), resp)
			return None

		return resp

	def _get_avatar(self, sjid, response):
		try:
			avdata = self.xmpp.avatars.get(self.xmpp.avatar_token, sjid)
		except Exception as e:
			logger.error('Error while fetching avatar:', exc_info=sys.exc_info())
			return

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

		self.xmpp.stream.send(resp)

