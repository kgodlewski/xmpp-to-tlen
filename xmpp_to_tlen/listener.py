import logging, gevent
from gevent.server import StreamServer

from pyxmpp2.settings import XMPPSettings
from pyxmpp2.transport import TCPTransport
from pyxmpp2.mainloop.select import SelectMainLoop

import proxy

logger = logging.getLogger('xmpp_to_tlen.listener')

class Listener(object):
	"""
	For each incoming connection launch a greenlet with
	a separate pyxmpp2 main loop. Attach the loop to proxy.Server
	and start serving the client.

	The loop we're using is pyxmpp2.mainloop.select.SelectMainLoop.
	Because it's based on select(), it works nicely with gevent's
	monkey patching.
	"""

	def __init__(self):
		super(Listener, self).__init__()

		self._server = StreamServer(('127.0.0.1', 5222), self._handle_connection)

	def serve(self):
		self._server.serve_forever()

	def _handle_connection(self, sock, addr):
		transport = TCPTransport(sock = sock)
		serv = proxy.Server(transport)
		loop = SelectMainLoop(XMPPSettings({'poll_interval' : 10000}), serv.handlers + [transport])

		gevent.spawn(self._supervise_loop, serv, loop)

	def _supervise_loop(self, serv, loop):
		try:
			loop.loop()
		except Exception as e:
			logger.error('Error: %s', e)
			if serv.tlen:
				serv.tlen.close()
			serv.transport.close()
			raise
