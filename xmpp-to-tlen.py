#!/usr/bin/env python
import gevent.monkey
gevent.monkey.patch_all()

import socket, logging, urllib

level = logging.DEBUG
level = None
logging.basicConfig(level=level)
logging.getLogger('pyxmpp2.IN').setLevel(logging.DEBUG)
logging.getLogger('pyxmpp2.OUT').setLevel(logging.DEBUG)

logger = logging.getLogger('tlen')
logger.setLevel(logging.DEBUG)

from pyxmpp2.settings import XMPPSettings
from pyxmpp2.transport import TCPTransport
from pyxmpp2.mainloop.select import SelectMainLoop

from gevent.server import StreamServer

import proxy

class Listener(object):
	"""
	For each incoming connection launch a greenlet with
	a separate pyxmpp2 main loop. Attach the loop to proxy.Server
	and start serving the client.
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
			logger.error('%s', e)
			if serv.tlen:
				serv.tlen.close()
			serv.transport.close()

if __name__ == '__main__':
	listener = Listener()
	listener.serve()
