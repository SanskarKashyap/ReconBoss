#!/usr/bin/env python3

import time
import requests
from modules.export import export
from modules.write_log import log_writer

R = '\033[31m'  # red
G = '\033[32m'  # green
C = '\033[36m'  # cyan
W = '\033[0m'   # white
Y = '\033[33m'  # yellow

def ssllabs_audit(domain, output, data):
    result = {}
    print(f'\n{Y}[!] SSL Labs Audit Information ({domain}) : {W}\n')

    api_url = 'https://api.ssllabs.com/api/v3/analyze'

    try:
        print(f'{G}[+] {C}Requesting SSL Labs analysis...{W}', end='', flush=True)
        
        while True:
            params = {
                'host': domain,
                'publish': 'off',
                'all': 'done'
            }
            response = requests.get(api_url, params=params, timeout=30)
            if response.status_code != 200:
                print(f'\n{R}[-] {C}API Error: {response.status_code}{W}')
                result.update({'Error': f'API Error {response.status_code}'})
                break
            
            res_json = response.json()
            status = res_json.get('status')
            
            if status in ('IN_PROGRESS', 'DNS'):
                print(f'\x1b[K\r{Y}[!] {C}Analysis is {status}... Waiting...{W}', end='', flush=True)
                time.sleep(10)
                continue
            elif status == 'READY':
                print(f'\x1b[K\r{G}[+] {C}Analysis Complete!{W}')
                
                endpoints = res_json.get('endpoints', [])
                if not endpoints:
                    print(f'{R}[-] {C}No endpoints found.{W}')
                    result.update({'Error': 'No endpoints found.'})
                    break

                for i, ep in enumerate(endpoints):
                    ep_ip = ep.get('ipAddress', 'Unknown')
                    grade = ep.get('grade', 'Unknown')
                    print(f'{G}[+] {C}Endpoint: {W}{ep_ip}')
                    print(f'\t{G}└╴{C}Grade: {W}{grade}')
                    
                    result.update({f'Endpoint-{i}-IP': ep_ip})
                    result.update({f'Endpoint-{i}-Grade': grade})
                    
                    details = ep.get('details', {})
                    if details:
                        # Extract protocols
                        protocols = details.get('protocols', [])
                        if protocols:
                            proto_list = [f"{p.get('name')} {p.get('version')}" for p in protocols]
                            print(f'\t{G}└╴{C}Protocols: {W}{", ".join(proto_list)}')
                            result.update({f'Endpoint-{i}-Protocols': ", ".join(proto_list)})

                        # Extract vulnerability tags
                        vuln_tags = []
                        if details.get('heartbleed'): vuln_tags.append('Heartbleed')
                        if details.get('poodle'): vuln_tags.append('POODLE')
                        if details.get('freak'): vuln_tags.append('FREAK')
                        if details.get('logjam'): vuln_tags.append('LOGJAM')
                        if details.get('robot'): vuln_tags.append('ROBOT')
                        if details.get('ticketbleed') == 2: vuln_tags.append('Ticketbleed')
                        
                        if vuln_tags:
                            print(f'\t{G}└╴{C}Vulnerabilities: {R}{", ".join(vuln_tags)}{W}')
                            result.update({f'Endpoint-{i}-Vulns': ", ".join(vuln_tags)})
                        else:
                            print(f'\t{G}└╴{C}Vulnerabilities: {G}None detected{W}')
                            result.update({f'Endpoint-{i}-Vulns': "None detected"})

                        print(f'\t{G}└╴{C}Forward Secrecy: {W}{details.get("forwardSecrecy", "Unknown")}')
                        result.update({f'Endpoint-{i}-ForwardSecrecy': details.get("forwardSecrecy", "Unknown")})
                        
                break
            elif status == 'ERROR':
                print(f'\n{R}[-] {C}Error in analysis: {res_json.get("statusMessage")}{W}')
                result.update({'Error': res_json.get('statusMessage', 'Unknown')})
                break
            else:
                print(f'\n{R}[-] {C}Unknown status: {status}{W}')
                result.update({'Error': f'Unknown status: {status}'})
                break

    except Exception as exc:
        print(f'\n{R}[-] {C}Exception : {W}{exc}\n')
        if output != 'None':
            result.update({'Exception': str(exc)})
        log_writer(f'[sslaudit] Exception = {exc}')

    result.update({'exported': False})

    if output != 'None':
        fname = f'{output["directory"]}/sslaudit.{output["format"]}'
        output['file'] = fname
        data['module-sslaudit'] = result
        export(output, data)
    log_writer('[sslaudit] Completed')
