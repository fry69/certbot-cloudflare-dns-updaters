#!/usr/bin/env python3

import time
from cloudflare import Cloudflare
import OpenSSL
import hashlib
import argparse
import configparser
from typing import List


def read_cloudflare_api_token(config_path: str = '/etc/letsencrypt/cloudflare.ini') -> str:
    with open(config_path, 'r') as f:
        content = f.read().strip()

    # Check if the file contains a section header
    if content.startswith('['):
        config = configparser.ConfigParser()
        config.read(config_path)
        return config.get('cloudflare', 'dns_cloudflare_api_token', fallback=None)
    else:
        # If no section header, assume it's a simple key=value format
        for line in content.split('\n'):
            if line.strip().startswith('dns_cloudflare_api_token'):
                return line.split('=')[1].strip()

    return None

def get_certificate_hash(cert_path: str) -> str:
    with open(cert_path, "rb") as cert_file:
        cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_file.read())
    pubkey = OpenSSL.crypto.dump_publickey(OpenSSL.crypto.FILETYPE_ASN1, cert.get_pubkey())
    return hashlib.sha256(pubkey).hexdigest()

def get_tlsa_records(cf: Cloudflare, zone_id: str) -> List[dict]:
    return cf.zones.dns_records.get(zone_id, params={"type": "TLSA", "per_page": 100})

def create_tlsa_record(cf: Cloudflare, zone_id: str, name: str, content: str, certificate_hash: str) -> dict:
    data = {
        "type": "TLSA",
        "name": name,
        "content": content,
        "ttl": 1,
        "data": {
            "usage": 3,
            "selector": 1,
            "matching_type": 1,
            "certificate": certificate_hash
        }
    }
    return cf.zones.dns_records.post(zone_id, data=data)

def delete_tlsa_record(cf: Cloudflare, zone_id: str, record_id: str) -> dict:
    return cf.zones.dns_records.delete(zone_id, record_id)

def main():
    parser = argparse.ArgumentParser(description="Update TLSA records for Certbot renewal")
    parser.add_argument("--hostname", required=True, help="DNS hostname")
    parser.add_argument("-p", "--port", type=int, action="append", required=True, help="Port number (can be used multiple times)")
    parser.add_argument("--udp", action="store_true", help="Use UDP instead of TCP")
    parser.add_argument("-s", "--sleep", type=int, default=10, help="Sleep time in seconds (default: 10)")
    args = parser.parse_args()

    hostname = args.hostname
    ports = args.port
    protocol = "udp" if args.udp else "tcp"
    sleep_time = args.sleep

    # Extract zone name from hostname
    zone_name = '.'.join(hostname.split('.')[-2:])

    api_token = read_cloudflare_api_token()
    if not api_token:
        raise Exception("Cloudflare API token not found in config file")

    cf = Cloudflare(token=api_token)
    
    # Get zone ID
    zones = cf.zones.get(params={"name": zone_name})
    if not zones:
        raise Exception(f"Zone {zone_name} not found")
    zone_id = zones[0]["id"]
    
    # Generate TLSA record names
    tlsa_names = [f"_{port}._{protocol}.{hostname}" for port in ports]
    
    # Get current certificate hash
    cert_path = f"/etc/letsencrypt/live/{hostname}/cert.pem"
    cert_hash = get_certificate_hash(cert_path)
    new_content = f"3 1 1 {cert_hash}"
    
    # Get existing TLSA records
    existing_records = get_tlsa_records(cf, zone_id)
    
    # Update or create TLSA records
    for name in tlsa_names:
        existing_record = next((r for r in existing_records if r["name"] == name), None)
        
        if existing_record:
            if existing_record["content"] != new_content:
                print(f"Updating TLSA record for {name}")
                delete_tlsa_record(cf, zone_id, existing_record["id"])
                create_tlsa_record(cf, zone_id, name, new_content, cert_hash)
            else:
                print(f"TLSA record for {name} is up to date")
        else:
            print(f"Creating new TLSA record for {name}")
            create_tlsa_record(cf, zone_id, name, new_content, cert_hash)
    
    print(f"Sleeping for {sleep_time} seconds to allow DNS propagation")
    time.sleep(sleep_time)
    
    print("Done!")

if __name__ == "__main__":
    main()

