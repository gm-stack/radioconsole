unbanded_interval_size = 500_000
bands = {
    "160m": [1_800_000, 1_875_000],
    "80m": [3_500_000, 3_700_000],
    "75m": [3_776_000, 3_800_000],
    "40m": [7_000_000, 7_300_000],
    "30m": [10_100_000, 10_150_000],
    "20m": [14_000_000, 14_350_000],
    "17m": [18_068_000, 18_168_000],
    "15m": [21_000_000, 21_450_000],
    "12m": [24_890_000, 24_990_000],
    "10m_low": [28_000_000, 28_300_000],
    "10m_mid": [28_300_000, 28_700_000],
    "10m_upper": [28_700_000, 29_300_000],
    "10m_high": [29_300_000, 29_700_000]
}
bands_list = list(bands.values())

def band_edges_for_frequency(freq):
    for lower, upper in bands_list:
        if lower <= freq <= upper:
            return (lower, upper)

    freq_unbanded = freq // unbanded_interval_size * unbanded_interval_size
    return (freq_unbanded, freq_unbanded + unbanded_interval_size)