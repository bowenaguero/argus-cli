# argus

Fast IP geolocation lookups using MaxMind GeoIP2 databases.

## Install

```bash
uv tool install git+https://github.com/bowenaguero/argus-cli
```

## Setup

```bash
argus setup
```

Get your free MaxMind license key at [maxmind.com/en/geolite2/signup](https://www.maxmind.com/en/geolite2/signup)

## Usage

```bash
# Single IP
argus lookup 8.8.8.8

# From file
argus lookup -f ips.txt

# Skip DNS lookups for speed
argus lookup -f ips.txt --no-dns

# Filter results
argus lookup -f ips.txt -xc US -xa 15169

# Export to JSON/CSV
argus lookup -f ips.txt -o results.json
```

## Options

- `-f, --file` - Extract IPs from file (txt, pdf, xlsx)
- `--fqdn` - Show full hostname instead of apex domain
- `--no-dns` - Skip reverse DNS lookups (faster)
- `-xc, --exclude-country` - Exclude country codes (e.g., US, CN)
- `-xct, --exclude-city` - Exclude cities
- `-xa, --exclude-asn` - Exclude ASN numbers
- `-xo, --exclude-org` - Exclude organizations
- `-o, --output` - Write results to file
- `--format` - Output format: json or csv

## License

MIT
