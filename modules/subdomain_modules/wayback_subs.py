#!/usr/bin/env python3

R = '\033[31m'  # red
G = '\033[32m'  # green
C = '\033[36m'  # cyan
W = '\033[0m'   # white
Y = '\033[33m'  # yellow

import os
import shutil
import asyncio
from urllib.parse import urlparse
import modules.subdom as parent
from modules.write_log import log_writer

async def machine(hostname, session):
    print(f'{Y}[!] {C}Requesting {G}Wayback (via GAU){W}')
    tmp_list = set()
    
    # Check for gau available
    gau_path = shutil.which("gau")
    if not gau_path:
        home = os.path.expanduser("~")
        go_gau = os.path.join(home, "go", "bin", "gau")
        if os.path.exists(go_gau):
            gau_path = go_gau

    if gau_path:
        try:
            # Run gau asynchronously to prevent blocking the event loop
            proc = await asyncio.create_subprocess_exec(
                gau_path, "--subs", hostname,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0 and stdout:
                raw_data = stdout.decode().split('\n')
                for line in raw_data:
                    line = line.strip()
                    if not line:
                        continue
                    # Parse domain out of the URL
                    if not line.startswith('http'):
                        line = 'http://' + line
                    try:
                        parsed = urlparse(line)
                        subdomain = parsed.netloc.split(':')[0]
                        if subdomain and subdomain.endswith(hostname):
                            tmp_list.add(subdomain)
                    except:
                        pass
                
                print(f'{G}[+] {Y}Wayback {W}found {C}{len(tmp_list)} {W}subdomains! (powered by GAU)')
                parent.found.extend(list(tmp_list))
            else:
                print(f'{R}[-] {C}Wayback (GAU) returned no results.{W}')
        except Exception as exc:
            print(f'{R}[-] {C}Wayback Exception (GAU) : {W}{exc}')
            log_writer(f'[wayback_subs] GAU Exception = {exc}')
            
    else:
        # Fallback to pure Wayback API if GAU is missing
        print(f'{R}[-] {C}GAU not found, falling back to basic Wayback API.{W}')
        url = f'http://web.archive.org/cdx/search/cdx?url=*.{hostname}/*&output=txt&fl=original&collapse=urlkey'
        try:
            async with session.get(url, timeout=30) as resp:
                status = resp.status
                if status == 200:
                    raw_data = await resp.text()
                    lines = raw_data.split('\n')
                    for line in lines:
                        if not line:
                            continue
                        subdomain = line.replace('http://', '').replace('https://', '').split('/')[0].split(':')[0]
                        if len(subdomain) >= len(hostname):
                            tmp_list.add(subdomain)
                    print(f'{G}[+] {Y}Wayback {W}found {C}{len(tmp_list)} {W}subdomains!')
                    parent.found.extend(list(tmp_list))
                else:
                    print(f'{R}[-] {C}Wayback Status : {W}{status}')
                    log_writer(f'[wayback_subs] Status = {status}, expected 200')
        except Exception as exc:
            # We silently log instead of throwing massive errors to the terminal
            print(f'{R}[-] {C}Wayback Exception : {W}{exc}')
            log_writer(f'[wayback_subs] Exception = {exc}')
            
    log_writer('[wayback_subs] Completed')
