import os

from . import civ

class RadioSettings(object):
    SettingsProviders = {
        'ci-v': civ.civ
    }

    settings = {
        'freq': None
    }

    def __init__(self, provider, config):
        if not provider in self.SettingsProviders:
            raise ValueError(
                f"unknown frequency source {provider}, "
                f"supported providers are {self.SettingsProviders.keys()}"
            )
        
        self.output_path = os.path.join(config.output_path, 'radio/')
        print(f"settings output path {self.output_path}")
        try:
            os.mkdir(self.output_path)
        except FileExistsError:
            pass

        self.provider = self.SettingsProviders[provider](config, self.callback)
    
    def callback(self, settings):
        if self.settings['freq'] != settings['freq']:
            self.writeout()
        self.settings.update(settings)

    def freq(self):
        return self.settings['freq']
    
    def write_setting(self, setting):
        f = open(os.path.join(self.output_path, setting),'w')
        f.write(f"{self.settings[setting]}")
        f.close()

    def writeout(self):
        self.write_setting('freq')