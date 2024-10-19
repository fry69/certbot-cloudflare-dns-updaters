#!/usr/bin/env python3

import argparse
from cloudflare import Cloudflare
import datetime
import configparser
import sys
from typing import Optional

def read_cloudflare_api_token(config_path: str = '/etc/letsencrypt/cloudflare.ini') -> str:
    with open(config_path, 'r') as f:
        content = f.read().strip()
    
    if content.startswith('['):
        config = configparser.ConfigParser()
        config.read(config_path)
        return config.get('cloudflare', 'dns_cloudflare_api_token', fallback=None)
    else:
        for line in content.split('\n'):
            if line.strip().startswith('dns_cloudflare_api_token'):
                return line.split('=')[1].strip()
    
    return None

def get_zone_id(cf: Cloudflare, zone_name: str) -> str:
    zones = cf.zones.get(params={'name': zone_name})
    if not zones:
        raise Exception(f"Zone {zone_name} not found")
    return zones[0]['id']

def delete_record_if_exists(cf: Cloudflare, zone_id: str, record_name: str, record_type: str) -> None:
    existing_records = cf.zones.dns_records.get(zone_id, params={'name': record_name, 'type': record_type})
    for record in existing_records:
        cf.zones.dns_records.delete(zone_id, record['id'])
        print(f"Deleted existing {record_type} record for {record_name}")

def create_mta_sts_record(cf: Cloudflare, zone_id: str, zone_name: str) -> None:
    record_name = f"_mta-sts.{zone_name}"
    record_content = f"v=STSv1; id={datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    delete_record_if_exists(cf, zone_id, record_name, 'TXT')
    
    cf.zones.dns_records.post(zone_id, data={
        'type': 'TXT',
        'name': record_name,
        'content': record_content,
        'ttl': 1
    })
    print(f"Created MTA-STS record for {zone_name}")

def handle_tlsrpt_record(cf: Cloudflare, zone_id: str, zone_name: str, email: Optional[str], url: Optional[str]) -> None:
    record_name = f"_smtp._tls.{zone_name}"
    
    # Always delete existing TLSRPT record
    delete_record_if_exists(cf, zone_id, record_name, 'TXT')
    
    if not email and not url:
        print(f"No TLSRPT reporting methods specified. Deleted existing TLSRPT record for {zone_name}")
        return
    
    record_content = "v=TLSRPTv1;"
    if email:
        record_content += f" rua=mailto:{email}"
    if url:
        record_content += f" rua=https:{url}" if record_content.endswith(';') else f",https:{url}"
    
    cf.zones.dns_records.post(zone_id, data={
        'type': 'TXT',
        'name': record_name,
        'content': record_content,
        'ttl': 1
    })
    print(f"Created TLSRPT record for {zone_name}")

def main():
    parser = argparse.ArgumentParser(description="Update MTA-STS and optionally TLSRPT records in Cloudflare DNS")
    parser.add_argument("zones", nargs='+', help="Zone names to update")
    parser.add_argument("--email", help="Email address for TLSRPT reporting")
    parser.add_argument("--url", help="HTTPS URL for TLSRPT reporting")
    args = parser.parse_args()

    api_token = read_cloudflare_api_token()
    if not api_token:
        print("Error: Cloudflare API token not found in config file")
        sys.exit(1)

    cf = Cloudflare(token=api_token)

    for zone_name in args.zones:
        try:
            zone_id = get_zone_id(cf, zone_name)
            create_mta_sts_record(cf, zone_id, zone_name)
            handle_tlsrpt_record(cf, zone_id, zone_name, args.email, args.url)
        except Exception as e:
            print(f"Error updating records for {zone_name}: {str(e)}")

if __name__ == "__main__":
    main()
