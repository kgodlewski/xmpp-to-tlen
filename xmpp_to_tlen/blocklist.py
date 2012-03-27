import os, errno

import const

class BlockList(object):
	def __init__(self, jid):
		super(BlockList, self).__init__()

		assert isinstance(jid, basestring)

		self._path = os.path.join(const.SETTINGS_DIR, 'blocklist-' + jid)
		try:
			self._blocked = set([x.strip() for x in open(self._path).readlines()])
		except IOError as e:
			if e.errno != errno.ENOENT:
				raise

			self._blocked = set()
			self._save()

		self._blocked.add('b73@tlen.pl')

	def is_blocked(self, jid):
		return self._adapt_jid(jid) in self._blocked

	def block(self, jid):
		self._blocked.add(self._adapt_jid(jid))
		self._save()

	def unblock(self, jid):
		self._blocked.remove(self._adapt_jid(jid))
		self._save()

	def _save(self):
		open(self._path, 'w').write('\n'.join(self._blocked))

	def _adapt_jid(self, jid):
		p = jid.rsplit('/', 1)
		return str(p[0])
