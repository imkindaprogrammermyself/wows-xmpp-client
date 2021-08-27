import asyncio
import slixmpp
import logging
import os

from slixmpp.stanza.message import Message

logging.basicConfig(level='DEBUG')

# host: xmpp-wows-na.wargaming.net port: 5222
# host: xmpp-wows-eu.wargaming.net port: 5222

HOST = "xmpp-wows-asia.wargaming.net"
PORT = 5222

# Check World_of_Warships\profile\chat_pref_*.loc.xml for JID_SUFFIX and CLAN_JID *: MATCHING YOUR ACCOUNT ID.
# wowsna.loc? wowseu.loc?
JID_SUFFIX = "wowsasia.loc"
CLAN_JID = os.getenv("CLAN_JID")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ACCOUNT_TOKEN = 16849194  # (ALREADY USED) IT'S ONE TIME PASSWORD/TOKEN


class XmppClient(slixmpp.ClientXMPP):
    def __init__(self, account_id, password, **kwargs):
        self._jid = f"{account_id}@{JID_SUFFIX}"
        super().__init__(self._jid, str(password), sasl_mech='PLAIN', **kwargs)
        self['feature_mechanisms'].unencrypted_plain = True
        self.register_plugin('xep_0199')  # PING PLUGIN, KEEPS THE CLIENT CONNECTED.
        self.register_plugin('xep_0045')  # GROUP PLUGIN, SO YOU CAN JOIN ROOMS.
        self.use_aiodns = False
        self.add_event_handler("session_start", self.on_session_start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("failed_all_auth", self.on_failed_all_auth)

    def connect(self, **kwargs):
        return super().connect((HOST, PORT))

    def on_session_start(self, evt):
        self.send_presence(pfrom=self._jid, ppriority=0, pstatus='away')
        self.get_roster(callback=self.on_roster_received)
        self.plugin['xep_0045'].join_muc(room=CLAN_JID, nick="2016494874", pstatus='away')

    def on_failed_all_auth(self, *args, **kwargs):
        self.disconnect()
        asyncio.get_event_loop().stop()

    def on_roster_received(self, *args, **kwargs):
        for jid in self.client_roster:
            if self.client_roster[jid]['subscription'] in ['from', 'to']:
                name = self.client_roster[jid]['name']
                subc = self.client_roster[jid]['subscription']
                print(f"{jid} : {name} : {subc}")

    def message(self, msg: Message):
        if msg['type'] in ('normal', 'chat'):
            msg.reply(f"echo: {msg['body']}").send()


if __name__ == '__main__':
    client = XmppClient(ACCOUNT_ID, ACCOUNT_TOKEN)
    client.connect()
    client.get_roster(callback=lambda *args, **kwargs: print(args, kwargs))
    loop = asyncio.get_event_loop()
    loop.run_forever()
