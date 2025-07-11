import argparse
import whois
import dns.resolver
import requests
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

def whois_lookup(domain):
    try:
        w = whois.whois(domain)
        table = Table(title=f"[bold green]Whois Lookup for {domain}[/bold green]")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Registrar", str(w.registrar))
        table.add_row("Creation Date", str(w.creation_date))
        table.add_row("Expiration Date", str(w.expiration_date))
        table.add_row("Name Servers", "\n".join(w.name_servers) if w.name_servers else "N/A")
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error in Whois Lookup: {e}[/red]")

def dns_enum(domain):
    record_types = ['A', 'MX', 'TXT', 'NS', 'CNAME']
    try:
        for record in record_types:
            try:
                answers = dns.resolver.resolve(domain, record)
                table = Table(title=f"[bold blue]DNS {record} Records for {domain}[/bold blue]")
                table.add_column("Record", style="cyan")
                table.add_column("Data", style="magenta")
                for rdata in answers:
                    table.add_row(record, str(rdata))
                console.print(table)
            except dns.resolver.NoAnswer:
                console.print(f"[yellow]No {record} records found for {domain}[/yellow]")
            except Exception as e:
                console.print(f"[red]DNS Error ({record}): {e}[/red]")
    except Exception as e:
        console.print(f"[red]General DNS Enum Error: {e}[/red]")

def http_header_analyze(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        response = requests.get(url, timeout=5)
        table = Table(title=f"[bold yellow]HTTP Headers for {url}[/bold yellow]")
        table.add_column("Header", style="cyan")
        table.add_column("Value", style="magenta")
        
        for header, value in response.headers.items():
            table.add_row(header, value)
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]HTTP Header Error: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="[bold]Security Tool[/bold] - Whois, DNS Enum, HTTP Header Analyzer", 
                                    formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-w", "--whois", help="Perform WHOIS lookup for a domain")
    parser.add_argument("-d", "--dns", help="Perform DNS enumeration for a domain")
    parser.add_argument("-http", "--http", help="Analyze HTTP headers of a URL")
    parser.add_argument("-a", "--all", help="Run all checks for a domain/URL")

    args = parser.parse_args()

    if args.whois:
        whois_lookup(args.whois)
    if args.dns:
        dns_enum(args.dns)
    if args.http:
        http_header_analyze(args.http)
    if args.all:
        rprint(f"[bold green]Running all checks for {args.all}:[/bold green]")
        whois_lookup(args.all)
        dns_enum(args.all)
        http_header_analyze(args.all)

if __name__ == "__main__":
    main()