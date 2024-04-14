import os

from ..bands import band_edges_for_frequency

from . import civ
from . import dummy

class RadioSettings(object):
    SettingsProviders = {
        'ci-v': civ.civ,
        'dummy': dummy.dummy
    }

    settings = {
        'freq': None,
        'bands': None
    }

    def __init__(self, provider, config):
        if not provider in self.SettingsProviders:
            raise ValueError(
                f"unknown frequency source {provider}, "
                f"supported providers are {self.SettingsProviders.keys()}"
            )
        self.provider = self.SettingsProviders[provider](config, self.callback)

    def callback(self, settings):
        if self.settings['freq'] != settings['freq']:
            self.settings['band'] = band_edges_for_frequency(settings['freq'])
        self.settings.update(settings)