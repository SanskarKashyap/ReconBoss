# ReconBoss
python3 -m venv reconboss
source reconboss/bin/activate
pip install -r requirements.txt

# Recommended (For Maximum Wayback/Subdomain Results)
go install github.com/lc/gau/v2/cmd/gau@latest

chmod +x reconboss.py
./reconboss.py -h
./reconboss.py --headers https://xyz.ac.in
