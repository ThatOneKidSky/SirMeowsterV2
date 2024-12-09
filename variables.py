import json

class Data():
    def __init__(self, file):
        self.file = file
        self.data = self.load()

    def load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to read {self.file}: {e}")
    
    def save(self):
        try:
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            self.reload()
        except Exception as e:
            raise Exception(f"Failed to write {self.file}: {e}")
    
    def reload(self):
        self.data = self.load()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __contains__(self, key):
        return key in self.data

    def __repr__(self):
        return repr(self.data)
    
    def get(self, key, default=None):
        """Returns a value from (key) unless there is no value else returns (default) or None if not set."""
        return self.data.get(key, default)


playerData = Data("data/users.json")
horseData  = Data("data/horse.json")
shoopData  = Data("shoop/variables.json")
shoopPages = Data("shoop/pages.json")

constants = Data("constants.json")