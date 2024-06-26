import json
import requests
import re

from .. import channel_info

class RooterBackend(object):
    TOKEN_REGEX = re.compile('token: \'(.*)\'')

    sysauth = None
    def __init__(self, cfg):
        self.config = cfg

    def login(self):
        r = requests.post(
            f"http://{self.config.host}:{self.config.port}/cgi-bin/luci",
            data={
                'luci_username': self.config.username,
                'luci_password': self.config.password
            },
            allow_redirects=False,
            timeout=5
        )
        if r.status_code == 302:
            self.sysauth = r.cookies['sysauth']
            print("login to ROOTer success")
        else:
            self.sysauth = None
            print("login to ROOTer failed - check password")
            # FIXME: report error

    def fetch_stats(self):
        if not self.sysauth:
            self.login()
        if self.sysauth:
            r = requests.get(
                f'http://{self.config.host}:{self.config.port}/cgi-bin/luci/admin/modem/get_csq',
                cookies={'sysauth': self.sysauth},
                timeout=5
            )
            if r.status_code != 200:
                self.sysauth = None
                return {}

            return self.parse(r.text)
        else:
            return {'mode': 'Login failed, retrying...'}
            self.login()

    def reboot_modem(self):
        if not self.sysauth:
            self.login()
        else:
            r = requests.get(
                f'http://{self.config.host}:{self.config.port}/cgi-bin/luci/admin/system/reboot',
                cookies={'sysauth': self.sysauth},
                timeout=5
            )
            token = self.TOKEN_REGEX.search(r.text).groups()[0]

            r = requests.post(
                f'http://{self.config.host}:{self.config.port}/cgi-bin/luci/admin/system/reboot/call',
                cookies={'sysauth': self.sysauth},
                data={'token': token},
                timeout=5
            )
            if r.status_code != 200:
                print(r.text)

    @classmethod
    def parse_band(cls, band):
        if band == '-':
            return '', 0
        band = band.split(" ")
        return band[0], int(band[2])

    @classmethod
    def parse_bands_ch(cls, bands, earfcns):
        if not earfcns:
            return [{
                'band': '',
                'bandwidth': '',
                'earfcn': ''
            }]
        bandlist = bands.split(" aggregated with:<br />")

        res = []
        for i, band in enumerate(bandlist):
            bandname, bandwidth = cls.parse_band(band)
            res.append({
                'band': bandname,
                'bandwidth': bandwidth,
                'earfcn': earfcns[i]
            })

        return res

    @classmethod
    def csq_to_dbm(cls, csq):
        try:
            return str(-113 + (int(csq) * 2))
        except ValueError:
            return ''

    @classmethod
    def parse_earfcns(cls, channel):
        try:
            return [int(x) for x in channel.split(", ")]
        except ValueError:
            return []

    @classmethod
    def parse(cls, lte_stats):
        d = {k: v.strip() for k, v in json.loads(lte_stats).items()}
        earfcns = cls.parse_earfcns(d['channel'])

        return channel_info.add_channel_info({
            'bands': cls.parse_bands_ch(d['lband'], earfcns),
            'mode': d['mode'],
            'modem': d['modem'],
            'netmode': d['netmode'],
            'rsrq': d['ecio'].rstrip(' (RSRQ)dB'),
            'lac': d['lac'] + ' ' + d['lacn'].strip(),
            'rssi': cls.csq_to_dbm(d['csq']),
            'rnc': d['rnc'],
            'rncn': d['rncn'],
            'rsrp': d['rscp'].rstrip(' (RSRP)dBm'),
            'temp': d['tempur'].rstrip('Â°C'),
        })
