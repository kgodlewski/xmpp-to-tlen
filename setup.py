from setuptools import setup

setup(
	name='xmpp-to-tlen',
	version='0.1',
	description='XMPP to Tlen.pl proxy',
	author='Krzysztof Godlewski',
	author_email='krzysiek@dajerade.pl',
	url='https://github.com/kgodlewski/xmpp-to-tlen',

	packages=['xmpp_to_tlen', 'xmpp_to_tlen.tlen'],
	scripts=['xmpp-to-tlen'],

	install_requires=['gevent', 'pyxmpp2']
)

