import os, sys

DISCO_NS = "http://jabber.org/protocol/disco"
DISCO_ITEMS_NS = DISCO_NS+"#items"
DISCO_INFO_NS = DISCO_NS+"#info"

DISCO_ITEMS_NS_QNP = '{{{0}}}'.format(DISCO_ITEMS_NS)
DISCO_INFO_NS_QNP = '{{{0}}}'.format(DISCO_INFO_NS)

CHATSTATES_NS = 'http://jabber.org/protocol/chatstates'
CHATSTATES_NS_QNP = '{{{0}}}'.format(CHATSTATES_NS)

HOME = os.getenv('HOME')
if sys.platform == 'darwin':
	SETTINGS_DIR = os.path.join(HOME, 'Library', 'Application Support', 'xmpp-to-tlen')
else:
	SETTINGS_DIR = os.path.join(HOME, '.xmpp-to-tlen')

