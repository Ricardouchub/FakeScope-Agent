from pathlib import Path
path = Path('config/settings.toml')
raw = path.read_bytes()
print(raw[:4])
print(path.read_text())
