#!/usr/bin/env python3
"""
Crawl specific URLs that were missed during BFS crawling
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def crawl_url(url):
    """Crawl a specific URL and extract content"""
    print(f"\n🔍 Crawling: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Extract title
        title = soup.find('title')
        title = title.get_text().strip() if title else url
        
        # Extract meta description
        description = ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            description = meta_desc.get('content').strip()
        
        # Extract main content
        # Try common article content selectors
        content_selectors = [
            ('article', {}),
            ('main', {}),
            ('div', {'class': 'content'}),
            ('div', {'class': 'article-content'}),
            ('div', {'class': 'post-content'}),
            ('div', {'id': 'content'}),
        ]
        
        content = None
        for tag, attrs in content_selectors:
            content_tag = soup.find(tag, attrs)
            if content_tag:
                content = content_tag
                break
        
        # Fallback to body if no specific content found
        if not content:
            content = soup.find('body')
        
        # Extract text
        if content:
            text = content.get_text(separator='\n', strip=True)
            # Clean up extra whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n\n'.join(lines)
        else:
            text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n\n'.join(lines)
        
        # Extract outgoing links
        outgoing_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and (href.startswith('http') or href.startswith('/')):
                outgoing_links.append(href)
        
        doc = {
            'url': url,
            'title': title,
            'description': description,
            'content': text,
            'word_count': len(text.split()),
            'char_count': len(text),
            'crawled_at': datetime.now().isoformat(),
            'outgoing_links': list(set(outgoing_links))[:50]  # Limit to 50 unique links
        }
        
        print(f"✅ Success! Title: {title}")
        print(f"   Word count: {doc['word_count']}")
        print(f"   Char count: {doc['char_count']}")
        
        return doc
        
    except Exception as e:
        print(f"❌ Error crawling {url}: {str(e)}")
        return None


def main():
    """Crawl specific missing URLs"""
    
    # URLs to crawl
    target_urls = [
        'https://www.rackspace.com/blog/strengthening-healthcare-operations-through-cyber-resilience',
        'https://www.rackspace.com/cloud/cloud-migration',
    ]
    
    print("=" * 80)
    print("🚀 Crawling Specific URLs")
    print("=" * 80)
    
    # Load existing data
    try:
        with open('data/rackspace_knowledge.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"\n📚 Loaded {len(existing_data)} existing documents")
        existing_urls = {doc['url'] for doc in existing_data}
    except Exception as e:
        print(f"❌ Error loading existing data: {e}")
        existing_data = []
        existing_urls = set()
    
    # Crawl new URLs
    new_docs = []
    for url in target_urls:
        if url in existing_urls:
            print(f"\n⏭️  Skipping (already exists): {url}")
            continue
        
        doc = crawl_url(url)
        if doc:
            new_docs.append(doc)
        
        # Be polite - wait between requests
        time.sleep(1)
    
    if new_docs:
        # Merge with existing data
        all_data = existing_data + new_docs
        
        # Save updated data
        with open('data/rackspace_knowledge.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print(f"✅ SUCCESS! Added {len(new_docs)} new documents")
        print(f"   Total documents: {len(all_data)}")
        print("=" * 80)
        
        print("\n📝 New documents added:")
        for doc in new_docs:
            print(f"   • {doc['title']}")
            print(f"     {doc['url']}")
            print(f"     Words: {doc['word_count']:,}")
    else:
        print("\n⚠️  No new documents were added")


if __name__ == '__main__':
    main()
