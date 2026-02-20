# ReconBoss Installation

```bash
python3 -m venv reconboss
source reconboss/bin/activate
pip install -r requirements.txt
go install github.com/lc/gau/v2/cmd/gau@latest
```

# ReconBoss Usage
```bash
chmod +x reconboss.py
./reconboss.py -h
./reconboss.py --full https://xyz.com
```

# Future Update
1. subdomain takeover detection
2. parameter discovery