import json
import requests

from .. import channel_info

class RooterBackend(object):
    def __init__(self, cfg):
        print("logging in...")
        r = requests.post('http://172.17.0.254/cgi-bin/luci/admin/login')
        #login_cookie = r.cookies
        #login_cookie =

    def fetch_stats(self):
        cookies = {
            'sysauth': '694549bc88370c5ac37726c4e46c555d'
        }
        r = requests.get('http://172.17.0.254/cgi-bin/luci/admin/modem/get_csq', cookies=cookies)
        r.raise_for_status()
        return self.parse(r.text)

    @classmethod
    def parse_band(cls, band):
        band = band.split(" ")
        return band[0], int(band[2])

    @classmethod
    def parse_bands_ch(cls, bands, earfcns):
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
    def parse(cls, lte_stats):
        d = {k: v.strip() for k, v in json.loads(lte_stats).items()}
        earfcns = [int(x) for x in d['channel'].split(", ")]

        return channel_info.add_channel_info({
            'bands': cls.parse_bands_ch(d['lband'], earfcns),
            'mode': d['mode'],
            'modem': d['modem'],
            'down': d['down'],
            'ecio': d['ecio'],
            'lac': d['lac'],
            'lacn': d['lacn'],
            'per': d['per'],
            'rnc': d['rnc'],
            'rncn': d['rncn'],
            'rscp': d['rscp'],
            'temp': d['tempur'],
        })
