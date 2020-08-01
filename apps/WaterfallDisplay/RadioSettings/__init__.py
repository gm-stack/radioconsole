from . import civ

class RadioSettings(object):
    SettingsProviders = {
        'ci-v': civ.civ
    }

    def __init__(self, provider, config):
        if not provider in self.SettingsProviders:
            raise ValueError(
                f"unknown frequency source {provider}, "
                f"supported providers are {self.SettingsProviders.keys()}"
            )

        self.provider = self.SettingsProviders[provider](config)
    
    def freq(self):
        return self.provider.freq()