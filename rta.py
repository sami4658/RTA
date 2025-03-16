#!/usr/bin/env python3

import argparse
import requests
import urllib.parse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re
import socket
import sys

class RobotsTxtFinder:
    def __init__(self, target, max_depth=2, timeout=10, max_threads=10, verbose=False):
        self.target = target
        self.max_depth = max_depth
        self.timeout = timeout
        self.max_threads = max_threads
        self.verbose = verbose
        self.visited_urls = set()
        self.robots_found = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RobotsTxtFinder/1.0 (https://github.com/example/robots-txt-finder)'
        })

    def is_ip_address(self, target):
        try:
            socket.inet_aton(target)
            return True
        except socket.error:
            return False

    def normalize_url(self, url):
        """Normalize URL by removing fragments and ensuring scheme"""
        parsed = urllib.parse.urlparse(url)
        
       
        if not parsed.scheme:
            url = "http://" + url
            parsed = urllib.parse.urlparse(url)
            
      
        url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ''  
        ))
        
      
        if not parsed.path:
            url += '/'
            
        return url

    def get_base_url(self, url):
        """Extract the base URL (scheme + netloc)"""
        parsed = urllib.parse.urlparse(url)
        base_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
        return base_url

    def get_robots_txt_url(self, base_url):
        """Construct robots.txt URL from base URL"""
        return urllib.parse.urljoin(base_url, '/robots.txt')

    def check_robots_txt(self, base_url):
        """Check if robots.txt exists and retrieve its content"""
        robots_url = self.get_robots_txt_url(base_url)
        
        if robots_url in self.robots_found:
            return
            
        try:
            response = self.session.get(robots_url, timeout=self.timeout, allow_redirects=True)
            
            if response.status_code == 200 and 'text/plain' in response.headers.get('Content-Type', ''):
                self.robots_found.add(robots_url)
                if self.verbose:
                    print(f"✓ Found robots.txt: {robots_url}")
                return robots_url, response.text
            else:
                if self.verbose:
                    print(f"✗ No robots.txt at: {robots_url} (Status: {response.status_code})")
                return None
        except Exception as e:
            if self.verbose:
                print(f"✗ Error checking {robots_url}: {str(e)}")
            return None

    def extract_links(self, url, html_content):
        """Extract all links from HTML content"""
        links = set()
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
          
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urllib.parse.urljoin(url, href)
                links.add(absolute_url)
                
         
            text = soup.get_text()
            subdomain_pattern = r'https?://([a-zA-Z0-9][-a-zA-Z0-9]*\.)+' + re.escape(self.base_domain)
            for match in re.finditer(subdomain_pattern, text):
                links.add(match.group(0))
                
        except Exception as e:
            if self.verbose:
                print(f"Error extracting links from {url}: {str(e)}")
                
        return links

    def crawl_url(self, url, depth=0):
        """Crawl a URL to find robots.txt and extract links"""
        if depth > self.max_depth or url in self.visited_urls:
            return set()
            
        self.visited_urls.add(url)
        
     
        base_url = self.get_base_url(url)
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        
      
        if not domain.endswith(self.base_domain) and domain != self.base_domain:
            return set()
            
      
        self.check_robots_txt(base_url)
        
      
        if depth < self.max_depth:
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                    return self.extract_links(url, response.text)
            except Exception as e:
                if self.verbose:
                    print(f"Error crawling {url}: {str(e)}")
                    
        return set()

    def resolve_ip_to_hostname(self, ip):
        """Try to resolve an IP address to hostname(s)"""
        try:
            hostnames = socket.gethostbyaddr(ip)
            return [hostnames[0]] + hostnames[1]
        except socket.herror:
            return []

    def run(self):
        """Main method to find robots.txt files"""
        target = self.normalize_url(self.target)
        
        if self.is_ip_address(self.target):
          
            print(f"Target is an IP address: {self.target}")
            hostnames = self.resolve_ip_to_hostname(self.target)
            
            if hostnames:
                print(f"Found hostnames for IP {self.target}: {', '.join(hostnames)}")
                targets = [f"http://{host}/" for host in hostnames]
                targets.append(f"http://{self.target}/")
            else:
                print(f"No hostnames found for IP {self.target}, using IP directly")
                targets = [f"http://{self.target}/"]
        else:
          
            targets = [target]
        
       
        parsed = urllib.parse.urlparse(targets[0])
        self.base_domain = parsed.netloc
        
       
        urls_to_crawl = set(targets)
        
       
        for depth in range(self.max_depth + 1):
            if not urls_to_crawl:
                break
                
            print(f"\nCrawling {len(urls_to_crawl)} URLs at depth {depth}...")
            
            new_urls = set()
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                results = list(executor.map(lambda url: self.crawl_url(url, depth), urls_to_crawl))
                
       
            for result_set in results:
                new_urls.update(result_set)
                
           
            urls_to_crawl = new_urls - self.visited_urls
        
     
        print("\n--- RESULTS ---")
        if self.robots_found:
            print(f"Found {len(self.robots_found)} robots.txt files:")
            for robots_url in sorted(self.robots_found):
                print(f"- {robots_url}")
                
          
            print("\nWould you like to see the content of these robots.txt files? (y/n)")
            response = input().lower()
            if response.startswith('y'):
                for robots_url in sorted(self.robots_found):
                    try:
                        print(f"\n=== Content of {robots_url} ===")
                        response = self.session.get(robots_url, timeout=self.timeout)
                        print(response.text)
                        print("=" * 50)
                    except Exception as e:
                        print(f"Error retrieving content: {str(e)}")
        else:
            print("No robots.txt files found.")
            
        print(f"\nCrawled {len(self.visited_urls)} URLs in total.")
        return self.robots_found

def main():
    parser = argparse.ArgumentParser(description='Find robots.txt files on websites and IP addresses')
    parser.add_argument('target', help='Target website or IP address')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Maximum crawl depth (default: 2)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Request timeout in seconds (default: 10)')
    parser.add_argument('-m', '--max-threads', type=int, default=10, help='Maximum number of threads (default: 10)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    print(f"Starting robots.txt finder for: {args.target}")
    finder = RobotsTxtFinder(
        args.target,
        max_depth=args.depth,
        timeout=args.timeout,
        max_threads=args.max_threads,
        verbose=args.verbose
    )
    
    try:
        finder.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
