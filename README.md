# Certbot Cloudflare TLSA Hook

This script automates the process of updating DANE TLSA records in Cloudflare DNS after Certbot renews a Let's Encrypt certificate. It's designed to work as a standalone script or integrate seamlessly with Certbot's renewal process.

## What are DANE and TLSA records?

DANE (DNS-based Authentication of Named Entities) is a protocol that allows X.509 certificates, commonly used for TLS, to be bound to domain names using DNS. TLSA records are a type of DNS record used to implement DANE.

TLSA records enhance security by allowing domain owners to specify which TLS certificate or public key should be used when connecting to a service. This provides an additional layer of authentication beyond traditional PKI.

## Features

- Updates TLSA records in Cloudflare DNS after certificate renewal
- Supports multiple ports and protocols (TCP/UDP)
- Configurable sleep time for DNS propagation
- Uses the same configuration syntax as the `certbot-dns-cloudflare` plugin

## Prerequisites

- Python 3.6+
- Cloudflare account with API token
- Let's Encrypt certificate managed by Certbot

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/fry69/certbot-cloudflare-tlsa-hook.git
   ```

2. Install required packages:
   ```
   pip install cloudflare pyopenssl
   ```

3. Set up your Cloudflare API token:
   Create a file at `/etc/letsencrypt/cloudflare.ini` with the following content:
   ```
   dns_cloudflare_api_token = your_api_token_here
   ```
   Ensure this file is readable only by root: `chmod 600 /etc/letsencrypt/cloudflare.ini`

## Usage

### Standalone

Run the script manually after certificate renewal:

```
python dane.py --hostname mail.example.com -p 25 -p 587 --sleep 30
```

Options:
- `--hostname`: The hostname for which to update TLSA records
- `-p` or `--port`: Port number (can be specified multiple times for multiple ports)
- `--udp`: Use UDP instead of TCP (default is TCP)
- `-s` or `--sleep`: Sleep time in seconds for DNS propagation (default: 10)

### Integration with Certbot

To automatically update TLSA records after each renewal, add the script as a renewal hook:

1. Make the script executable:
   ```
   chmod +x /path/to/dane.py
   ```

2. Edit your Certbot renewal configuration (`/etc/letsencrypt/renewal/your_domain.conf`):
   ```
   renew_hook = /path/to/dane.py --hostname mail.your_domain.com -p 25 -p 587 ; systemctl reload postfix
   ```

## Verification

After updating TLSA records, you can verify them using these online tools:

- [DANE TLSA Check](https://www.huque.com/bin/danecheck) (supports various services including IMAP, SMTP, etc.)
- [DANE TLSA validator](https://dane.sys4.de/) (specifically for SMTP)

## Note

This script is a companion to the `certbot-dns-cloudflare` plugin and intentionally uses the same configuration syntax for the API key configuration file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.