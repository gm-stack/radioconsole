from . import band_table

bt = {b['band']: b for b in band_table.bands}

def add_band_info(band):
    return {
        **band,
        'band_name': band_name(band['band']),
        'freq': f"{earfcn_to_freq(band['earfcn'])}Mhz" if band['band'] else '',
        'bandwidth': f"{band['bandwidth']}Mhz" if band['band'] else '',
    }

def add_channel_info(conn_info):
    band_info = [add_band_info(band) for band in conn_info['bands']]
    return {
        **conn_info,
        'bands': band_info
    }

def band_name(band):
    if not band: return ''
    bandnum = int(band[1:]) # drop the initial 'B'
    return "{} {}".format(band, bt[bandnum]['name'])

def earfcn_to_freq(earfcn):
    if 18000 <= earfcn <= 35999:
        for b in band_table.bands:
            if b['NUL_Min'] <= earfcn <= b['NUL_Max']:
                base_earfcn = earfcn - b['NUL_Min']
                return b['FUL_Low'] + (0.1 * base_earfcn)
    else:
        for b in band_table.bands:
            if b['NDL_Min'] <= earfcn <= b['NDL_Max']:
                base_earfcn = earfcn - b['NDL_Min']
                return b['FDL_Low'] + (0.1 * base_earfcn)
