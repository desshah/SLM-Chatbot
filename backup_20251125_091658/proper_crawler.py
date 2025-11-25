"""
PROPER Web Crawler with High-Quality Content Extraction
This fixes the hallucination issue by:
1. Extracting ONLY main article/documentation content
2. Filtering out navigation, menus, footers, sidebars
3. Using smarter selectors for actual content
4. Saving clean, meaningful text with proper metadata
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import List, Dict, Set, Optional
from collections import deque
import logging
from urllib.parse import urljoin, urlparse
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Rackspace domains to crawl
ALLOWED_DOMAINS = [
    'www.rackspace.com',
    'docs.rackspace.com',
    'developer.rackspace.com',
    'support.rackspace.com',
    'blog.rackspace.com'
]

# Start URLs - key pages with good content
START_URLS = [
    'https://www.rackspace.com/cloud/cloud-migration',
    'https://www.rackspace.com/cloud/aws',
    'https://www.rackspace.com/cloud/azure',
    'https://www.rackspace.com/cloud/google-cloud',
    'https://www.rackspace.com/cloud/multi-cloud',
    'https://www.rackspace.com/security',
    'https://www.rackspace.com/managed-hosting',
    'https://www.rackspace.com/blog',
    'https://docs.rackspace.com',
    'https://developer.rackspace.com',
    'https://support.rackspace.com'
]


class ProperContentExtractor:
    """Extracts high-quality main content from web pages"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special unicode characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"\/\[\]]', '', text)
        return text.strip()
    
    @staticmethod
    def is_navigation_text(text: str) -> bool:
        """Check if text is likely navigation/menu text"""
        text_lower = text.lower()
        nav_patterns = [
            'click here', 'learn more', 'read more', 'view all',
            'next page', 'previous page', 'home', 'about us',
            'contact us', 'privacy policy', 'terms of service',
            'copyright', '© 20', 'all rights reserved',
            'sign in', 'log in', 'register', 'subscribe'
        ]
        
        # Short text with nav keywords is likely navigation
        if len(text) < 100 and any(pattern in text_lower for pattern in nav_patterns):
            return True
        
        # Very short fragments
        if len(text.split()) < 5:
            return True
        
        return False
    
    def extract_main_content(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract ONLY the main article/documentation content"""
        
        # Step 1: Remove noise elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header',
                            'aside', 'iframe', 'noscript', 'form', 'button',
                            'input', 'select', 'textarea']):
            element.decompose()
        
        # Step 2: Remove common navigation/menu classes and IDs
        noise_selectors = [
            '[class*="nav"]', '[class*="menu"]', '[class*="sidebar"]',
            '[class*="footer"]', '[class*="header"]', '[class*="cookie"]',
            '[class*="banner"]', '[class*="popup"]', '[class*="modal"]',
            '[id*="nav"]', '[id*="menu"]', '[id*="sidebar"]',
            '[id*="footer"]', '[id*="header"]'
        ]
        for selector in noise_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Step 3: Find main content area using multiple strategies
        main_content = None
        
        # Strategy 1: Look for semantic HTML5 elements
        main_content = soup.find('main') or soup.find('article')
        
        # Strategy 2: Look for content-specific classes/IDs
        if not main_content:
            content_selectors = [
                'div.content', 'div.main-content', 'div.post-content',
                'div.entry-content', 'div.article-content', 'div.page-content',
                'div.blog-content', 'div.documentation', 'div.doc-content',
                '#content', '#main-content', '#article-content'
            ]
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
        
        # Strategy 3: Find largest text block
        if not main_content:
            candidates = soup.find_all(['div', 'section'], recursive=True)
            max_text_len = 0
            for candidate in candidates:
                text = candidate.get_text(strip=True)
                if len(text) > max_text_len and len(text) > 200:
                    max_text_len = len(text)
                    main_content = candidate
        
        # Strategy 4: Use body as last resort
        if not main_content:
            main_content = soup.body
        
        if not main_content:
            logger.warning(f"No content found for {url}")
            return None
        
        # Step 4: Extract title
        title = None
        # Try h1 in main content first
        h1 = main_content.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        else:
            # Try title tag
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                # Clean up title
                title = title.split('|')[0].split('-')[0].strip()
        
        if not title:
            title = url
        
        # Step 5: Extract paragraphs and headings (ACTUAL CONTENT)
        content_parts = []
        
        # Get all paragraphs and headings in order
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            text = element.get_text(separator=' ', strip=True)
            text = self.clean_text(text)
            
            # Filter out navigation/menu text
            if text and len(text) > 20 and not self.is_navigation_text(text):
                content_parts.append(text)
        
        if not content_parts:
            logger.warning(f"No substantial content found for {url}")
            return None
        
        # Combine content
        full_content = '\n\n'.join(content_parts)
        
        # Step 6: Quality check - must have substantial content
        word_count = len(full_content.split())
        if word_count < 50:  # Less than 50 words is too short
            logger.warning(f"Content too short ({word_count} words) for {url}")
            return None
        
        # Step 7: Extract metadata
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '') if meta_description else ''
        
        # Extract all outgoing links for BFS crawling
        outgoing_links = []
        for link_elem in main_content.find_all('a', href=True):
            href = link_elem['href']
            absolute_url = urljoin(url, href)
            outgoing_links.append(absolute_url)
        
        return {
            'url': url,
            'title': title,
            'description': description,
            'content': full_content,
            'word_count': word_count,
            'char_count': len(full_content),
            'crawled_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'outgoing_links': outgoing_links[:20]  # Keep top 20 links
        }


class ProperBFSCrawler:
    """BFS web crawler with proper content extraction"""
    
    def __init__(self, start_urls: List[str], allowed_domains: List[str]):
        self.start_urls = start_urls
        self.allowed_domains = allowed_domains
        self.visited: Set[str] = set()
        self.queue: deque = deque()
        self.data: List[Dict] = []
        self.extractor = ProperContentExtractor()
        
        # Initialize queue
        for url in start_urls:
            self.queue.append((url, 0))  # (url, depth)
        
        # Session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    
    def is_allowed(self, url: str) -> bool:
        """Check if URL is in allowed domains"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(domain == allowed or domain.endswith('.' + allowed) 
                   for allowed in self.allowed_domains)
    
    def is_valid(self, url: str) -> bool:
        """Check if URL should be crawled"""
        if not url or url.startswith('#'):
            return False
        
        skip_patterns = [
            'javascript:', 'mailto:', 'tel:',
            '.pdf', '.zip', '.jpg', '.png', '.gif',
            'login', 'signin', 'signup', 'logout'
        ]
        
        return not any(pattern in url.lower() for pattern in skip_patterns)
    
    def crawl(self, max_pages: int = 200, max_depth: int = 3):
        """Crawl websites using BFS"""
        logger.info("="*80)
        logger.info("STARTING PROPER BFS CRAWL WITH HIGH-QUALITY CONTENT EXTRACTION")
        logger.info(f"Max pages: {max_pages}, Max depth: {max_depth}")
        logger.info("="*80)
        
        pages_crawled = 0
        
        while self.queue and pages_crawled < max_pages:
            url, depth = self.queue.popleft()
            
            # Skip if already visited or too deep
            normalized_url = self.normalize_url(url)
            if normalized_url in self.visited or depth > max_depth:
                continue
            
            # Skip if not allowed domain
            if not self.is_allowed(url):
                continue
            
            self.visited.add(normalized_url)
            
            try:
                logger.info(f"[{pages_crawled + 1}/{max_pages}] Crawling depth {depth}: {url}")
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract HIGH-QUALITY content
                content_data = self.extractor.extract_main_content(soup, url)
                
                if content_data:
                    self.data.append(content_data)
                    pages_crawled += 1
                    logger.info(f"✅ Extracted {content_data['word_count']} words from {url}")
                    
                    # Add outgoing links to queue for BFS
                    for link in content_data.get('outgoing_links', []):
                        if self.is_valid(link) and self.is_allowed(link):
                            normalized_link = self.normalize_url(link)
                            if normalized_link not in self.visited:
                                self.queue.append((link, depth + 1))
                else:
                    logger.warning(f"❌ No quality content extracted from {url}")
                
                # Be nice to servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                continue
        
        logger.info("="*80)
        logger.info(f"CRAWLING COMPLETE: {len(self.data)} pages with quality content")
        logger.info("="*80)
        
        return self.data
    
    def save_data(self, filename: str = 'rackspace_knowledge_proper.json'):
        """Save crawled data"""
        output_path = DATA_DIR / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(self.data)} documents to {output_path}")
        
        # Statistics
        total_words = sum(doc['word_count'] for doc in self.data)
        avg_words = total_words / len(self.data) if self.data else 0
        
        logger.info(f"📊 Statistics:")
        logger.info(f"   Total documents: {len(self.data)}")
        logger.info(f"   Total words: {total_words:,}")
        logger.info(f"   Average words per document: {avg_words:.0f}")
        
        return output_path


def main():
    """Main execution"""
    crawler = ProperBFSCrawler(
        start_urls=START_URLS,
        allowed_domains=ALLOWED_DOMAINS
    )
    
    # Crawl
    data = crawler.crawl(max_pages=200, max_depth=3)
    
    # Save
    crawler.save_data('rackspace_knowledge_proper.json')
    
    # Show samples
    if data:
        print("\n" + "="*80)
        print("SAMPLE EXTRACTED CONTENT")
        print("="*80)
        sample = data[0]
        print(f"URL: {sample['url']}")
        print(f"Title: {sample['title']}")
        print(f"Words: {sample['word_count']}")
        print(f"Content preview:\n{sample['content'][:500]}...")


if __name__ == "__main__":
    main()
