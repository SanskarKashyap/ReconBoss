#!/usr/bin/env python3

R = '\033[31m'  # red
G = '\033[32m'  # green
C = '\033[36m'  # cyan
W = '\033[0m'   # white
Y = '\033[33m'  # yellow

from json import loads, dumps
import modules.subdom as parent
from modules.write_log import log_writer

async def sslmate(hostname, conf_path, session):
	with open(f'{conf_path}/keys.json', 'r') as keyfile:
		json_read = keyfile.read()

	json_load = loads(json_read)
	try:
		sslmate_key = json_load['sslmate']
	except KeyError:
		log_writer('[sslmate_subs] key missing in keys.json')
		with open(f'{conf_path}/keys.json', 'w') as outfile:
			json_load['sslmate'] = None
			sslmate_key = None
			outfile.write(dumps(json_load, sort_keys=True, indent=4))

	print(f'{Y}[!] {C}Requesting {G}SSLMate Search API{W}')
	url = 'https://api.certspotter.com/v1/issuances'
	cs_params = {
		'domain': hostname,
		'expand': 'dns_names',
		'include_subdomains': 'true',
		'match_wildcards': 'true'
	}
	
	headers = {}
	if sslmate_key:
		headers['Authorization'] = f'Bearer {sslmate_key}'

	try:
		total_subdomains = []
		while True:
			async with session.get(url, params=cs_params, headers=headers) as resp:
				status = resp.status
				if status == 200:
					json_data = await resp.text()
					json_read = loads(json_data)
					
					if not json_read:
						break
					
					for entry in json_read:
						domains = entry.get('dns_names', [])
						total_subdomains.extend(domains)
					
					cs_params['after'] = json_read[-1]['id']
					
					# Without an API key, pagination is severely rate limited. Keep to 1 page if free.
					if not sslmate_key:
						break
				elif status == 429:
					print(f'{R}[-] {C}SSLMate Rate Limited! Add an API Key to conf/keys.json to bypass.{W}')
					log_writer('[sslmate_subs] Rate Limited (429)')
					break
				else:
					print(f'{R}[-] {C}SSLMate Status : {W}{status}')
					log_writer(f'[sslmate_subs] Status = {status}, expected 200')
					break

		if total_subdomains:
			unique_domains = list(set(total_subdomains))
			parent.found.extend(unique_domains)
			print(f'{G}[+] {Y}SSLMate {W}found {C}{len(unique_domains)} {W}subdomains!')
	except Exception as exc:
		print(f'{R}[-] {C}SSLMate Exception : {W}{exc}')
		log_writer(f'[sslmate_subs] Exception = {exc}')
	log_writer('[sslmate_subs] Completed')
