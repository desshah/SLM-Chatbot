"""
Enhanced Data Collection with Better Content Extraction
This script:
1. Discovers ALL Rackspace URLs dynamically (not just predefined)
2. Filters out navigation/UI text intelligently
3. Extracts only substantial, meaningful content
4. Uses sitemap.xml for comprehensive URL discovery
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
from collections import deque
from typing import Set, Dict, List
import re
from datetime import datetime
import xml.etree.ElementTree as ET

from config import (
    RACKSPACE_URLS, ALLOWED_DOMAINS, MAX_CRAWL_DEPTH, 
    MAX_PAGES_PER_DOMAIN, CRAWL_DELAY, REQUEST_TIMEOUT,
    DATA_DIR, MIN_CONTENT_LENGTH
)


class EnhancedRackspaceCollector:
    """Enhanced collector with better content extraction and URL discovery"""
    
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.domain_stats: Dict[str, int] = {domain: 0 for domain in ALLOWED_DOMAINS}
        self.documents: List[Dict] = []
        
        # Navigation/UI text patterns to exclude
        self.exclude_patterns = [
            r'^learn more$',
            r'^read more$',
            r'^click here$',
            r'^view all$',
            r'^get started$',
            r'^sign up$',
            r'^log in$',
            r'^contact us$',
            r'^see more$',
            r'^download$',
            r'^subscribe$',
            r'^\s*$',  # Empty lines
            r'cookie',  # Cookie notices
            r'privacy policy',
            r'terms of service',
            r'all rights reserved',
        ]
        self.exclude_regex = re.compile('|'.join(self.exclude_patterns), re.IGNORECASE)
        
        # Tags to completely ignore
        self.ignore_tags = [
            'nav', 'header', 'footer', 'aside', 'script', 'style',
            'iframe', 'noscript', 'form', 'button', 'input'
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RackspaceKnowledgeBot/2.0 (Educational Purpose)'
        })
    
    def discover_urls_from_sitemap(self, base_url: str) -> Set[str]:
        """Discover URLs from sitemap.xml"""
        discovered = set()
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemap-index.xml",
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    # Parse XML
                    root = ET.fromstring(response.content)
                    
                    # Handle both sitemap and sitemap index
                    for elem in root.iter():
                        if 'loc' in elem.tag:
                            url = elem.text.strip()
                            if url and self.is_allowed_domain(url):
                                discovered.add(url)
                    
                    print(f"✅ Discovered {len(discovered)} URLs from {sitemap_url}")
                    break  # Stop if we found a working sitemap
            except Exception as e:
                continue
        
        return discovered
    
    def is_allowed_domain(self, url: str) -> bool:
        """Check if URL belongs to allowed domains"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(allowed in domain for allowed in ALLOWED_DOMAINS)
    
    def is_navigation_text(self, text: str) -> bool:
        """Check if text is navigation/UI element"""
        text = text.strip()
        
        # Too short
        if len(text) < 20:
            return True
        
        # Matches exclude patterns
        if self.exclude_regex.search(text):
            return True
        
        # All caps (likely header/button)
        if text.isupper() and len(text) < 100:
            return True
        
        # Too many special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if special_chars > len(text) * 0.3:
            return True
        
        return False
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract only main content, filtering out navigation/UI"""
        
        # Remove unwanted tags entirely
        for tag in self.ignore_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Try to find main content areas (in priority order)
        main_content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.main-content',
            '.content',
            '#content',
            '.article-content',
            '.post-content',
        ]
        
        content_elements = []
        for selector in main_content_selectors:
            elements = soup.select(selector)
            if elements:
                content_elements.extend(elements)
                break
        
        # If no main content found, use body but be more selective
        if not content_elements:
            body = soup.find('body')
            if body:
                content_elements = [body]
        
        # Extract text from content elements
        extracted_text = []
        
        for element in content_elements:
            # Get paragraphs with substantial content
            for p in element.find_all(['p', 'li', 'div'], recursive=True):
                text = p.get_text(separator=' ', strip=True)
                
                # Filter out navigation text
                if self.is_navigation_text(text):
                    continue
                
                # Must be substantial
                if len(text) >= MIN_CONTENT_LENGTH:
                    extracted_text.append(text)
            
            # Also get headings (but shorter threshold)
            for heading in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = heading.get_text(strip=True)
                if len(text) > 10 and not self.is_navigation_text(text):
                    extracted_text.append(f"\n\n### {text}\n")
        
        # Combine and clean
        full_text = '\n\n'.join(extracted_text)
        
        # Remove excessive whitespace
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        full_text = re.sub(r' {2,}', ' ', full_text)
        
        return full_text.strip()
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extract and normalize links from page"""
        links = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            # Normalize URL
            parsed = urlparse(full_url)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Remove trailing slash for consistency
            if normalized.endswith('/') and normalized.count('/') > 3:
                normalized = normalized[:-1]
            
            if self.is_allowed_domain(normalized):
                links.add(normalized)
        
        return links
    
    def crawl_page(self, url: str) -> Dict:
        """Crawl a single page with enhanced content extraction"""
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else url
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '') if meta_desc else ''
            
            # Extract main content (filtered)
            content = self.extract_main_content(soup)
            
            # Only save if we have substantial content
            if len(content) < MIN_CONTENT_LENGTH:
                print(f"⚠️  Skipping {url} - insufficient content ({len(content)} chars)")
                return None
            
            # Extract outgoing links
            links = self.extract_links(soup, url)
            
            document = {
                'url': url,
                'title': title_text,
                'description': description,
                'content': content,
                'word_count': len(content.split()),
                'char_count': len(content),
                'crawled_at': datetime.now().isoformat(),
                'outgoing_links': list(links)
            }
            
            print(f"✅ Crawled: {url} ({len(content)} chars, {len(content.split())} words)")
            return document
            
        except Exception as e:
            print(f"❌ Error crawling {url}: {str(e)}")
            return None
    
    def bfs_crawl(self):
        """BFS crawling with enhanced URL discovery"""
        print("\n" + "="*80)
        print("🚀 ENHANCED RACKSPACE DATA COLLECTION")
        print("="*80)
        
        # Phase 1: Discover URLs from sitemaps
        print("\n📍 Phase 1: Discovering URLs from sitemaps...")
        discovered_urls = set()
        
        for start_url in RACKSPACE_URLS[:5]:  # Check sitemaps of main domains
            base_url = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"
            sitemap_urls = self.discover_urls_from_sitemap(base_url)
            discovered_urls.update(sitemap_urls)
            time.sleep(1)
        
        print(f"✅ Discovered {len(discovered_urls)} URLs from sitemaps")
        
        # Phase 2: BFS crawling
        print("\n📍 Phase 2: BFS crawling with link following...")
        
        # Initialize queue with both predefined and discovered URLs
        all_start_urls = set(RACKSPACE_URLS) | discovered_urls
        queue = deque([(url, 0) for url in all_start_urls])
        
        while queue:
            current_url, depth = queue.popleft()
            
            # Check if already visited
            if current_url in self.visited_urls:
                continue
            
            # Check depth limit
            if depth > MAX_CRAWL_DEPTH:
                continue
            
            # Check domain limit
            domain = urlparse(current_url).netloc
            if self.domain_stats.get(domain, 0) >= MAX_PAGES_PER_DOMAIN:
                continue
            
            # Mark as visited
            self.visited_urls.add(current_url)
            self.domain_stats[domain] = self.domain_stats.get(domain, 0) + 1
            
            # Crawl the page
            document = self.crawl_page(current_url)
            
            if document:
                self.documents.append(document)
                
                # Add outgoing links to queue
                if depth < MAX_CRAWL_DEPTH:
                    for link in document.get('outgoing_links', []):
                        if link not in self.visited_urls:
                            queue.append((link, depth + 1))
            
            # Status update every 10 pages
            if len(self.documents) % 10 == 0:
                print(f"\n📊 Progress: {len(self.documents)} documents collected, {len(queue)} URLs in queue")
                print(f"   Domain stats: {dict(self.domain_stats)}")
            
            # Be polite
            time.sleep(CRAWL_DELAY)
        
        # Phase 3: Save results
        print("\n📍 Phase 3: Saving results...")
        self.save_results()
    
    def save_results(self):
        """Save collected data"""
        output_file = DATA_DIR / 'rackspace_knowledge.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2, ensure_ascii=False)
        
        # Statistics
        total_words = sum(doc['word_count'] for doc in self.documents)
        total_chars = sum(doc['char_count'] for doc in self.documents)
        
        stats = {
            'total_documents': len(self.documents),
            'total_words': total_words,
            'total_characters': total_chars,
            'unique_domains': len([d for d in self.domain_stats.values() if d > 0]),
            'domain_breakdown': self.domain_stats,
            'crawl_completed_at': datetime.now().isoformat()
        }
        
        stats_file = DATA_DIR / 'crawl_statistics.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        print("\n" + "="*80)
        print("✅ DATA COLLECTION COMPLETE!")
        print("="*80)
        print(f"📄 Total documents: {len(self.documents)}")
        print(f"📝 Total words: {total_words:,}")
        print(f"🔤 Total characters: {total_chars:,}")
        print(f"🌐 Unique domains: {len([d for d in self.domain_stats.values() if d > 0])}")
        print(f"\n💾 Saved to: {output_file}")
        print(f"📊 Statistics: {stats_file}")
        print("="*80)


def main():
    """Main execution"""
    collector = EnhancedRackspaceCollector()
    collector.bfs_crawl()


if __name__ == "__main__":
    main()
