import random
from . import rooter_webif

class TestBackend(object):
    # pylint: disable=line-too-long, too-few-public
    responses = [
        """{"cidn":"  (16)","cops":"Telstra Mobile Telstra","host":"1","rscp":"-80 (RSRP) dBm","cell":"2","rncn":" (533940)","cid":"10","netmode":"UP (+) (using Ping Test)","proto":"MBIM","up":"-","rnc":"825B4","mnc":" 01","imei":"x","imsi":"y","per":"100%","rssi":">= -51 dBm","modtype":"2","port":"/dev/ttyUSB2","mode":"LTE","phonen":"*","iccid":"z","modid":"1199 : 9071","lac":"3002","mcc":"505","ecio1":" ","phone":"","crate":"Fast (updated every 10 seconds)","lband":"B7 (Bandwidth 20 MHz)","modem":" Sierra Wireless, Incorporated MC7430","lacn":"  (12290)","rscp1":" ","csq":"31","channel":"3148","conntype":"Modem #1","tempur":"32.00°C","down":"-","ecio":"-10.2 (RSRQ) dB"}""",
        """{"cidn":"  (16)","cops":"Telstra Mobile Telstra","host":"1","rscp":"-74 (RSRP) dBm","cell":"2","rncn":" (533940)","cid":"10","netmode":"UP (-) (using Ping Test)","proto":"MBIM","up":"-","rnc":"825B4","mnc":" 01","imei":"x","imsi":"y","per":"100%","rssi":">= -51 dBm","modtype":"2","port":"/dev/ttyUSB2","mode":"LTE","phonen":"*","iccid":"z","modid":"1199 : 9071","lac":"3002","mcc":"505","ecio1":" ","phone":"","crate":"Fast (updated every 10 seconds)","lband":"B7 (Bandwidth 20 MHz)","modem":" Sierra Wireless, Incorporated MC7430","lacn":"  (12290)","rscp1":" ","csq":"31","channel":"3148","conntype":"Modem #1","tempur":"32.00°C","down":"-","ecio":"-9.1 (RSRQ) dB"}""",
        """{"cidn":"  (14)","cops":"Telstra Mobile Telstra","host":"1","rscp":"-80 (RSRP) dBm","cell":"2","rncn":" (533915)","cid":"0E","netmode":"UP (+) (using Ping Test)","proto":"MBIM","up":"-","rnc":"8259B","mnc":" 01","imei":"x","imsi":"y","per":"100%","rssi":">= -51 dBm","modtype":"2","port":"/dev/ttyUSB2","mode":"LTE","phonen":"*","iccid":"z","modid":"1199 : 9071","lac":"3000","mcc":"505","ecio1":" ","phone":"","crate":"Fast (updated every 10 seconds)","lband":"B7 (Bandwidth 20 MHz) aggregated with:<br />B7 (Bandwidth 20 MHz)","modem":" Sierra Wireless, Incorporated MC7430","lacn":"  (12288)","rscp1":" ","csq":"31","channel":"3148, 2950","conntype":"Modem #1","tempur":"34.00°C","down":"-","ecio":"-9.8 (RSRQ) dB"}""",
        """{"cidn":"  (14)","cops":"Telstra Mobile Telstra","host":"1","rscp":"-80 (RSRP) dBm","cell":"2","rncn":" (533915)","cid":"0E","netmode":"UP (+) (using Ping Test)","proto":"MBIM","up":"-","rnc":"8259B","mnc":" 01","imei":"x","imsi":"y","per":"100%","rssi":">= -51 dBm","modtype":"2","port":"/dev/ttyUSB2","mode":"LTE","phonen":"*","iccid":"z","modid":"1199 : 9071","lac":"3000","mcc":"505","ecio1":" ","phone":"","crate":"Fast (updated every 10 seconds)","lband":"B28 (Bandwidth 20 MHz)","modem":" Sierra Wireless, Incorporated MC7430","lacn":"  (12288)","rscp1":" ","csq":"31","channel":"9410","conntype":"Modem #1","tempur":"34.00°C","down":"-","ecio":"-9.8 (RSRQ) dB"}""",
        """{"cidn":"  (14)","cops":"Telstra Mobile Telstra","host":"1","rscp":"-80 (RSRP) dBm","cell":"2","rncn":" (533915)","cid":"0E","netmode":"UP (+) (using Ping Test)","proto":"MBIM","up":"-","rnc":"8259B","mnc":" 01","imei":"x","imsi":"y","per":"100%","rssi":">= -51 dBm","modtype":"2","port":"/dev/ttyUSB2","mode":"LTE","phonen":"*","iccid":"z","modid":"1199 : 9071","lac":"3000","mcc":"505","ecio1":" ","phone":"","crate":"Fast (updated every 10 seconds)","lband":"B3 (Bandwidth 15 MHz)","modem":" Sierra Wireless, Incorporated MC7430","lacn":"  (12288)","rscp1":" ","csq":"31","channel":"1275","conntype":"Modem #1","tempur":"34.00°C","down":"-","ecio":"-9.8 (RSRQ) dB"}"""
    ]

    def __init__(self, cfg):
        pass

    def fetch_stats(self):
        response = random.choice(self.responses)
        return rooter_webif.RooterBackend.parse(response)
