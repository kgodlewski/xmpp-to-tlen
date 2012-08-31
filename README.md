xmpp-to-tlen -- a XMPP <=> Tlen.pl proxy server
===============================================

## Summary
The goal of this project is to provide basic connectivity to the Tlen.pl
IM network using an XMPP client of choice.

## How it works
When you run *xmpp-to-tlen*, a local XMPP server is started on your machine.
When you connect to the server, using your favourite XMPP client configured
to use a Tlen.pl account (see *Usage* below), it makes a connection to the
Tlen.pl network on your behalf, passing messages between your client, and
the Tlen.pl server, translating them between protocols.

In other words: you can use your Tlen.pl account with any XMPP client
without installing additional plugins. It's just like a server-side
transport being run on your machine.

Here's some fancy ASCII-art to picture this:

```
Your XMPP client <=> xmpp-to-tlen <=> Tlen.pl
```

## Requirements
 * Python 2.7+
 * PyXMPP2 (this is installed automatically by `pip`)

## Installation
Some external modules are required, gevent being the one that causes most trouble.
You need XCode with Command Line Tools installed (see Preferences -> Downloads in XCode). XCode can be downloaded for free using the App Store.
You also need libevent. The easiest way to install it is using the excellent [Homebrew](https://github.com/mxcl/homebrew).

After installing all the above stuff, all that's left to do is running one of these command in your terminal:

 * stable version (recommended):

   ```
   sudo pip install https://github.com/downloads/kgodlewski/xmpp-to-tlen/xmpp-to-tlen-0.1.tar.gz
   ```
 * latest development version:

   ```
   sudo pip install -U https://github.com/kgodlewski/xmpp-to-tlen/tarball/master
   ```

## Usage
Start the server:

```
$ xmpp-to-tlen
````

Configure your client:

 * add an XMPP account using your Tlen.pl account credentials
   * remember to use full jid, ie. *username@tlen.pl*
 * edit "Advanced settings", "Server settings" or similar for the account
   using these values:
   * "server host": *127.0.0.1*
   * "server port": *5222*
   * disable TLS/SSL
   * if there is a setting stating "Allow plain authentication", or similar,
     be sure to enable it. Disable checkboxes that say something along "warn me if the password is not being sent in a secure way".
 * enjoy!
 
Your client might warn you about sending credentials in plain text. You can
safely ignore this warning. If in doubt, see the _Security_ section below.

## Supported features
 * messaging, obviously (no font colors and other fancy stuff, this is not
   supported by Tlen.pl)
 * presence handling
 * typing notifications
 * roster (buddy list) operations
 * handling multiple proxy connections -- that means you can use multiple
   Tlen.pl accounts simultaneously
 * buddy icons

## Unsupported features
A list of features I think might be possible to implement:

 * "invisible" presence
 * user profile info

The following stuff is mostly Tlen.pl specific. Making it work with any
XMPP client is either impossible, or requires a tremendous ammount of effort.
Consider this a "will never be implemented" list.

 * encryption -- See the *Security* section
 * p2p (file transfers, audio/video conversations)
 * "send image"
 * multi-user chat

## Security
As far as security goes, there are a few things to note.

First of all, *xmpp-to-tlen* sends data to the Tlen.pl server in an unecrypted
form. Encryption algorithms used in the official Tlen.pl client are proprietary,
so there isn't much we can do.

Note that all the other unofficial Tlen protocol implementations behave
exactly the same way. So, if you've been using any IM client plugin
(Adium, pidgin), server-side transport, or anything other than the
official Tlen.pl client, you've already been sending the data in an unecrypted form.

The other thing is a requirement for using PLAIN authentication. This might be
regarded as a security issue, but in fact is not *that* bad. The password is sent
in plain text locally, that is: **it never leaves your machine in plain form**.
*xmpp-to-tlen* needs it in plain text to authenticate with the Tlen.pl server
on your behalf, then discards it. If you're paranoid about it, just check the code.

## Disclaimer
My XMPP knowledge is pretty basic (if there is a level below basic, I'm there!).
I can't guarantee this will work for all XMPP clients out there. 

In fact, I guarantee nothing. *xmpp-to-tlen* does its best to provide a smooth
experience, but if there are messages lost, contacts accidentaly removed or
your computer suddenly explodes -- don't blame me.

Having that out of the way, these clients are known to work:

 * Adium
 * iChat

## Honor & Glory
[pyxmpp2](https://github.com/Jajcus/pyxmpp2)
	-- great project that did almost all the work for me  
[pidgin-tlen](https://github.com/pelotasplus/pidgin-tlen)
	-- useful reference  
[Unofficial Tlen proto docs](http://docs.malcom.pl/tlen/proto/index.xhtml)
	-- more reference (in Polish)

