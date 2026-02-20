#!/usr/bin/env python3

R = '\033[31m'  # red
G = '\033[32m'  # green
C = '\033[36m'  # cyan
W = '\033[0m'   # white
Y = '\033[33m'  # yellow

import json
import requests
import subprocess
import shutil
import os
from datetime import date
from modules.export import export
from modules.write_log import log_writer

def timetravel(target, data, output):
    wayback_total = set()
    result = {}
    
    print(f'\n{Y}[!] Starting URL Fetching (Wayback & GAU)...{W}\n')

    # Try to find gau in PATH or default go bin path
    gau_path = shutil.which("gau")
    if not gau_path:
        home = os.path.expanduser("~")
        go_gau = os.path.join(home, "go", "bin", "gau")
        if os.path.exists(go_gau):
            gau_path = go_gau

    if gau_path:
        print(f'{Y}[!] {C}Using GAU (getallurls) via {gau_path}{W}', end='', flush=True)
        try:
            # Run gau to fetch URLs
            proc = subprocess.run([gau_path, "--subs", target], capture_output=True, text=True)
            if proc.returncode == 0 and proc.stdout:
                urls = proc.stdout.strip().split('\n')
                wayback_total.update(urls)
                print(f'\r\x1b[K{G}[+] {C}GAU fetched {len(wayback_total)} URLs from multiple sources!{W}')
            else:
                print(f'\r\x1b[K{R}[-] {C}GAU returned no results or failed.{W}')
        except Exception as e:
            print(f'\r\x1b[K{R}[-] {C}GAU Execution Failed: {e}{W}')
            log_writer(f'[wayback] GAU Exception = {e}')
    else:
        print(f'{R}[-] {C}GAU not found! Falling back to basic Wayback API.{W}')
        
        curr_yr = date.today().year
        last_yr = curr_yr - 5
        domain_query = f'{target}/*'

        print(f'{Y}[!] {C}Checking Availability on Wayback Machine{W}', end='', flush=True)
        wm_avail = 'http://archive.org/wayback/available'
        avail_data = {'url': target}

        try:
            check_rqst = requests.get(wm_avail, params=avail_data, timeout=10)
            check_sc = check_rqst.status_code
            if check_sc == 200:
                check_data = check_rqst.text
                json_chk_data = json.loads(check_data)
                avail_data = json_chk_data['archived_snapshots']
                if avail_data:
                    print(f'{G}{"[".rjust(5, ".")} Available ]{W}')
                else:
                    print(f'{R}{"[".rjust(5, ".")} N/A ]{W}')
            else:
                print(f'\n{R}[-] Status : {C}{check_sc}{W}')
                log_writer(f'[wayback] Status = {check_sc}')

            if avail_data:
                print(f'{Y}[!] {C}Fetching URLs{W}', end='', flush=True)
                wm_url = 'http://web.archive.org/cdx/search/cdx'
                payload = {
                    'url': domain_query,
                    'fl': 'original',
                    'fastLatest': 'true',
                    'from': str(last_yr),
                    'to': str(curr_yr)
                }
                rqst = requests.get(wm_url, params=payload, timeout=10)
                if rqst.status_code == 200:
                    r_data = rqst.text
                    if r_data:
                        r_data_lines = r_data.split('\n')
                        wayback_total.update(r_data_lines)
                        print(f'{G}{"[".rjust(5, ".")} {len(wayback_total)} ]{W}')
                    else:
                        print(f'{R}{"[".rjust(5, ".")} Not Found ]{W}')
                else:
                    print(f'{R}{"[".rjust(5, ".")} {rqst.status_code} ]{W}')
        except Exception as exc:
            print(f'\n{R}[-] Exception : {C}{exc}{W}')
            log_writer(f'[wayback] Exception = {exc}')

    # Output processing
    if wayback_total and output != 'None':
        # Remove any empty strings from set
        wayback_total.discard('')
        result.update({'links': list(wayback_total)})
        result.update({'exported': False})
        data['module-wayback_urls'] = result
        fname = f'{output["directory"]}/wayback_urls.{output["format"]}'
        output['file'] = fname
        export(output, data)
        print(f'{G}[+] {C}Exported {len(wayback_total)} URLs!{W}')
        
    log_writer('[wayback] Completed')
