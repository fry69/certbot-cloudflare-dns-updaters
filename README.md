# Certbot Cloudflare DNS Record Updaters

This repository contains two scripts for updating DNS records in Cloudflare after Certbot renews a Let's Encrypt certificate:

1. DANE TLSA Hook for Certbot
2. MTA-STS and TLSRPT Record Updater

Both scripts are designed to work as standalone tools or integrate seamlessly with Certbot's renewal process.

## What are DANE, TLSA, MTA-STS, and TLSRPT?

- DANE (DNS-based Authentication of Named Entities) is a protocol that allows X.509 certificates to be bound to domain names using DNS.
- TLSA records are a type of DNS record used to implement DANE.
- MTA-STS (SMTP Mail Transfer Agent Strict Transport Security) is a security standard that enables mail service providers to declare their ability to receive TLS-secured connections.
- TLSRPT (TLS Reporting) is a standard that allows domains to request daily reports about TLS connectivity problems experienced by senders.

These standards enhance email security by providing additional layers of authentication and reporting beyond traditional PKI.

## Prerequisites

- Python 3.7+
- Cloudflare account with API token
- Let's Encrypt certificate managed by Certbot

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/fry69/certbot-cloudflare-dns-updaters.git
   ```

2. Install required packages:
   ```
   pip install cloudflare pyopenssl
   ```

   Alternatively on e.g. Ubuntu 24.04:
   ```
   apt install python3-certbot-dns-cloudflare
   ```

3. Set up your Cloudflare API token:
   Create a file at `/etc/letsencrypt/cloudflare.ini` with the following content:
   ```
   dns_cloudflare_api_token = your_api_token_here
   ```
   Ensure this file is readable only by root: `chmod 600 /etc/letsencrypt/cloudflare.ini`

## DANE TLSA Hook for Certbot

### Usage

#### Standalone

Run the script manually after certificate renewal:

```
python dane.py --hostname mail.example.com -p 25 -p 587 --sleep 30
```

Options:
- `--hostname`: The hostname for which to update TLSA records
- `-p` or `--port`: Port number (can be specified multiple times for multiple ports)
- `--udp`: Use UDP instead of TCP (default is TCP)
- `-s` or `--sleep`: Sleep time in seconds for DNS propagation (default: 10)

#### Integration with Certbot

To automatically update TLSA records after each renewal, add the script as a renewal hook:

1. Make the script executable:
   ```
   chmod +x /path/to/dane.py
   ```

2. Edit your Certbot renewal configuration (`/etc/letsencrypt/renewal/your_domain.conf`):
   ```
   renew_hook = /path/to/dane.py --hostname your_domain.com -p 25 -p 587

   # To reload services optionally add to the above line: 
   #  ; systemctl reload postfix dovecot nginx
   ```

## MTA-STS and TLSRPT Record Updater

This script updates MTA-STS records and optionally TLSRPT records for multiple zones using the Cloudflare API.

### Usage

Run the script manually:

```
python mta-sts.py example.com example.org [--email reports@example.com] [--url //reporting.example.com/v1/tlsrpt]
```

Options:
- Positional arguments: One or more zone names to update
- `--email`: Email address for TLSRPT reporting (optional)
- `--url`: HTTPS URL for TLSRPT reporting (optional)

If neither `--email` nor `--url` is specified, any existing TLSRPT record will be deleted.

### Examples

1. Update MTA-STS records only (delete any existing TLSRPT records):
   ```
   python mta-sts.py example.com example.org
   ```

2. Update MTA-STS and TLSRPT records with email reporting:
   ```
   python mta-sts.py example.com example.org --email reports@example.com
   ```

3. Update MTA-STS and TLSRPT records with URL reporting:
   ```
   python mta-sts.py example.com example.org --url //reporting.example.com/v1/tlsrpt
   ```

4. Update MTA-STS and TLSRPT records with both email and URL reporting:
   ```
   python mta-sts.py example.com example.org --email reports@example.com --url //reporting.example.com/v1/tlsrpt
   ```

## Verification

After updating DNS records, you can verify them using these online tools:

- [DANE TLSA Check](https://www.huque.com/bin/danecheck) (supports various services including IMAP, SMTP, etc.)
- [DANE TLSA validator](https://dane.sys4.de/) (specifically for SMTP)
- [MTA-STS validator](https://www.mailhardener.com/tools/mta-sts-validator) (for checking MTA-STS policies)

## Note

These scripts are companions to the `certbot-dns-cloudflare` plugin and intentionally use the same configuration syntax for the API key configuration file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.