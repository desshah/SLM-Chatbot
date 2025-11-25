"""
Advanced data scraper for comprehensive Rackspace knowledge collection
Uses BFS (Breadth-First Search) to crawl all related pages within allowed domains
Builds extensive training dataset for our own fine-tuned model (NO AGENTS)
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import List, Dict, Set
from collections import deque
import logging
from urllib.parse import urljoin, urlparse, urlunparse
from config import (
    DATA_DIR, 
    RACKSPACE_URLS, 
    ALLOWED_DOMAINS,
    MAX_CRAWL_DEPTH,
    MAX_PAGES_PER_DOMAIN,
    CRAWL_DELAY,
    REQUEST_TIMEOUT
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedRackspaceCollector:
    """
    Advanced web crawler using BFS to collect comprehensive Rackspace knowledge.
    NO AGENTS - All data collected for training our own model.
    """
    
    def __init__(self, output_dir: Path = DATA_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.visited_urls: Set[str] = set()
        self.data: List[Dict] = []
        self.domain_page_count: Dict[str, int] = {}
        
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes"""
        parsed = urlparse(url)
        # Remove fragment and normalize
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip('/'),
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return normalized
    
    def is_allowed_domain(self, url: str) -> bool:
        """Check if URL belongs to allowed Rackspace domains"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain matches or is subdomain of allowed domains
        for allowed in ALLOWED_DOMAINS:
            if domain == allowed or domain.endswith('.' + allowed):
                return True
        return False
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled"""
        if not url or url.startswith('#'):
            return False
        
        # Skip common non-content URLs
        skip_patterns = [
            'javascript:', 'mailto:', 'tel:', 'ftp:',
            '.pdf', '.zip', '.exe', '.dmg', '.jpg', '.png', '.gif', '.svg',
            'login', 'signin', 'signup', 'logout',
            '/cdn-cgi/', '/search?', '?sort=', '?filter='
        ]
        
        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in skip_patterns)
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc.lower()
    
    def can_crawl_domain(self, url: str) -> bool:
        """Check if we can still crawl this domain"""
        domain = self.get_domain(url)
        count = self.domain_page_count.get(domain, 0)
        return count < MAX_PAGES_PER_DOMAIN
    
    def increment_domain_count(self, url: str):
        """Increment page count for domain"""
        domain = self.get_domain(url)
        self.domain_page_count[domain] = self.domain_page_count.get(domain, 0) + 1
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract meaningful content from page"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 
                            'aside', 'iframe', 'noscript', 'form']):
            element.decompose()
        
        # Try to find main content area
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_=['content', 'main-content', 'post-content', 'entry-content']) or
            soup.find('div', id=['content', 'main-content']) or
            soup.body
        )
        
        if not main_content:
            return None
        
        # Extract title
        title = None
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title = title_elem.get_text(strip=True)
        else:
            title = url
        
        # Extract text content
        text = main_content.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())  # Normalize whitespace
        
        # Only return if substantial content
        if len(text) < 100:
            return None
        
        # Extract metadata
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '') if meta_description else ''
        
        return {
            'url': url,
            'title': title,
            'content': text,
            'description': description,
            'source': 'web_crawl',
            'content_length': len(text)
        }
    
    def get_all_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all valid links from page"""
        links = []
        
        for link_elem in soup.find_all('a', href=True):
            href = link_elem['href']
            
            # Convert to absolute URL
            absolute_url = urljoin(base_url, href)
            
            # Normalize
            normalized_url = self.normalize_url(absolute_url)
            
            # Validate
            if (self.is_valid_url(normalized_url) and 
                self.is_allowed_domain(normalized_url) and
                normalized_url not in self.visited_urls):
                links.append(normalized_url)
        
        return links
    
    def crawl_bfs(self, start_urls: List[str], max_depth: int = MAX_CRAWL_DEPTH):
        """
        BFS web crawling to collect comprehensive Rackspace knowledge.
        Crawls through all linked pages within allowed domains.
        """
        # Initialize queue with (url, depth) tuples
        queue = deque([(url, 0) for url in start_urls])
        
        # Track URLs by depth for logging
        depth_stats = {}
        
        logger.info("="*80)
        logger.info("Starting BFS Web Crawling")
        logger.info(f"Max Depth: {max_depth}")
        logger.info(f"Max Pages per Domain: {MAX_PAGES_PER_DOMAIN}")
        logger.info(f"Starting URLs: {len(start_urls)}")
        logger.info("="*80)
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        while queue:
            url, depth = queue.popleft()
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Skip if max depth reached
            if depth > max_depth:
                continue
            
            # Skip if domain limit reached
            if not self.can_crawl_domain(url):
                logger.warning(f"Domain limit reached for {self.get_domain(url)}, skipping...")
                continue
            
            # Mark as visited
            self.visited_urls.add(url)
            self.increment_domain_count(url)
            
            # Update depth stats
            depth_stats[depth] = depth_stats.get(depth, 0) + 1
            
            try:
                logger.info(f"[Depth {depth}] Crawling: {url}")
                
                # Fetch page
                response = session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract content
                content_data = self.extract_content(soup, url)
                
                if content_data:
                    content_data['depth'] = depth
                    self.data.append(content_data)
                    logger.info(f"  ✓ Extracted {content_data['content_length']} chars: {content_data['title'][:60]}")
                else:
                    logger.info(f"  ⊘ No substantial content found")
                
                # Get all links for BFS (only if not at max depth)
                if depth < max_depth:
                    links = self.get_all_links(soup, url)
                    
                    # Add new links to queue
                    for link in links:
                        if link not in self.visited_urls:
                            queue.append((link, depth + 1))
                    
                    logger.info(f"  → Found {len(links)} new links to explore")
                
                # Rate limiting
                time.sleep(CRAWL_DELAY)
                
            except requests.exceptions.Timeout:
                logger.error(f"  ✗ Timeout: {url}")
            except requests.exceptions.RequestException as e:
                logger.error(f"  ✗ Request error: {url} - {e}")
            except Exception as e:
                logger.error(f"  ✗ Unexpected error: {url} - {e}")
        
        # Print statistics
        logger.info("="*80)
        logger.info("BFS Crawling Complete!")
        logger.info(f"Total pages visited: {len(self.visited_urls)}")
        logger.info(f"Documents collected: {len(self.data)}")
        logger.info("\nPages per depth:")
        for d in sorted(depth_stats.keys()):
            logger.info(f"  Depth {d}: {depth_stats[d]} pages")
        logger.info("\nPages per domain:")
        for domain, count in sorted(self.domain_page_count.items()):
            logger.info(f"  {domain}: {count} pages")
        logger.info("="*80)
    
    def add_manual_knowledge(self):
        """Add manually curated Rackspace knowledge base"""
        logger.info("Adding curated Rackspace knowledge...")
        
        manual_data = [
            {
                'title': 'About Rackspace Technology - Company Overview',
                'content': '''Rackspace Technology is a leading end-to-end multicloud technology services company. Founded in 1998, Rackspace is headquartered in San Antonio, Texas, United States. The company has grown to become one of the world's largest managed cloud providers, serving thousands of customers across various industries worldwide. Rackspace delivers expert services across major public clouds including Amazon Web Services (AWS), Google Cloud Platform (GCP), Microsoft Azure, VMware, and OpenStack. The company combines deep technical expertise with proprietary software and automation to help businesses design, build, and operate their multicloud environments efficiently. With over 6,000 employees globally, Rackspace operates data centers and offices across North America, Europe, Asia, and Australia, providing 24x7x365 support to customers.''',
                'source': 'curated_knowledge',
                'url': 'https://www.rackspace.com/company',
                'depth': 0
            },
            {
                'title': 'Rackspace Mission, Vision and Values',
                'content': '''Rackspace's mission is to design, build, and operate customers' multicloud environments, delivering Fanatical Experience throughout every interaction. The company's vision is to be the world's leading multicloud solutions company, recognized for technical expertise, customer service excellence, and innovation. Rackspace is committed to providing Fanatical Experience, which means going above and beyond to deliver exceptional service and support to every customer, every time. This includes 24x7x365 access to cloud experts, proactive monitoring and management, rapid response times, and a customer-first approach in everything they do. The Fanatical Experience has been the cornerstone of Rackspace's brand identity since its founding and continues to differentiate the company in the competitive cloud services market.''',
                'source': 'curated_knowledge',
                'url': 'https://www.rackspace.com/company/mission',
                'depth': 0
            },
            {
                'title': 'Rackspace Services and Solutions Portfolio',
                'content': '''Rackspace offers a comprehensive portfolio of cloud services and solutions: 1) Managed Cloud Services for AWS, Azure, Google Cloud, and private clouds, providing full lifecycle management including architecture design, migration, deployment, ongoing operations, optimization, and security. 2) Professional Services for cloud strategy consulting, application modernization, cloud migration planning and execution, and digital transformation initiatives. 3) Elastic Engineering providing on-demand access to certified cloud architects and engineers for project-based work. 4) Cloud-Native Services including containerization with Docker, Kubernetes orchestration, microservices architecture, and serverless computing. 5) Data Services covering managed databases (SQL and NoSQL), big data analytics, data lakes, machine learning, and artificial intelligence solutions. 6) Security Services including security assessments, compliance management, threat detection and response, managed SIEM, and security operations center (SOC) services. 7) Colocation and Private Cloud services offering dedicated infrastructure, hybrid cloud solutions, and interconnectivity between cloud providers. 8) Application Services for modern application development, DevOps implementation, CI/CD pipeline setup, and application performance optimization.''',
                'source': 'curated_knowledge',
                'url': 'https://www.rackspace.com/services',
                'depth': 0
            },
            {
                'title': 'Rackspace Company History and Evolution',
                'content': '''Rackspace was founded in 1998 in San Antonio, Texas by Graham Weston, Dirk Elmendorf, Pat Condon, and Morris Miller as a web hosting company. Initially focused on shared hosting services, the company quickly differentiated itself through exceptional customer service, coining the term "Fanatical Support." In 2006, Rackspace expanded into cloud computing by launching Cloud Servers and Cloud Files, becoming one of the early cloud infrastructure providers. In 2010, Rackspace co-founded OpenStack alongside NASA, creating the world's most widely deployed open-source cloud computing platform for public and private clouds. This move established Rackspace as a leader in open cloud technologies. The company went public in 2008 on the NYSE under ticker symbol RAX. In 2016, Rackspace was acquired by Apollo Global Management in a $4.3 billion deal and became a private company. Under Apollo's ownership, Rackspace accelerated its transformation from a hosting company to a comprehensive multicloud solutions provider. In 2020, Rackspace Technology went public again on NASDAQ under ticker symbol RXT, marking a new chapter in its evolution. Today, Rackspace is recognized as a leader in the Gartner Magic Quadrant for Public Cloud Infrastructure Professional and Managed Services, and continues to innovate in multicloud technologies.''',
                'source': 'curated_knowledge',
                'url': 'https://www.rackspace.com/company/history',
                'depth': 0
            },
            {
                'title': 'Rackspace Fanatical Experience - Service Excellence',
                'content': '''Fanatical Experience is Rackspace's commitment to delivering extraordinary customer service and technical support that goes beyond standard service level agreements. This philosophy encompasses several key elements: 24x7x365 Support Access providing customers with round-the-clock access to certified cloud experts via phone, chat, email, and ticketing systems, with no additional charges for support. Proactive Monitoring using advanced monitoring tools and automation to identify and resolve issues before they impact customers, with real-time alerts and automated remediation. Rapid Response Times with initial response within 15 minutes for critical issues and dedicated account teams for enterprise customers. Customer Success Programs including regular business reviews, optimization recommendations, cost management guidance, and strategic planning sessions. Expert Resources with teams holding multiple certifications from AWS, Azure, Google Cloud, VMware, and other technology partners. White-Glove Service for complex migrations, architecture design, and special projects requiring dedicated engineering resources. Continuous Innovation through investment in proprietary tools, automation, and AI-driven solutions to improve service delivery and customer experience. This Fanatical Experience has been recognized with numerous customer service awards and industry accolades, maintaining customer satisfaction scores consistently above 90%.''',
                'source': 'curated_knowledge',
                'url': 'https://www.rackspace.com/fanatical-experience',
                'depth': 0
            },
            {
                'title': 'Rackspace Cloud Platform Partnerships and Certifications',
                'content': '''Rackspace maintains strategic partnerships and premier certifications with all major cloud providers: Amazon Web Services (AWS) - Rackspace is an AWS Premier Tier Services Partner, AWS Managed Service Partner, AWS Well-Architected Partner, and holds competencies in DevOps, Migration, Microsoft Workloads, Data & Analytics, Machine Learning, Security, and SAP. Microsoft Azure - Rackspace is a Microsoft Gold Partner with advanced specializations in Windows Server and SQL Server Migration to Azure, Kubernetes on Azure, Modernization of Web Applications, Analytics on Azure, and Azure Virtual Desktop. Google Cloud Platform - Rackspace is a Google Cloud Premier Partner with specializations in Infrastructure, Application Development, Data Analytics, and Machine Learning. VMware - Rackspace is a VMware Premier Partner and VMware Cloud Verified provider, offering VMware Cloud on AWS and other VMware solutions. Red Hat - Rackspace is a Red Hat Premier Partner certified to deliver OpenShift, Ansible, and other Red Hat technologies. Oracle - Rackspace is an Oracle Cloud Managed Service Provider Partner. These partnerships enable Rackspace to provide certified expertise, access to latest technologies, and comprehensive managed services across all major cloud platforms, giving customers true multicloud flexibility and vendor-neutral guidance.''',
                'source': 'curated_knowledge',
                'url': 'https://www.rackspace.com/partners',
                'depth': 0
            },
            {
                'title': 'Rackspace Cloud Native and Kubernetes Services',
                'content': '''Rackspace provides comprehensive cloud-native services to help organizations modernize their applications and infrastructure: Container Services including Docker containerization, container registry management, and container security. Kubernetes Expertise offering managed Kubernetes services across multiple platforms including Amazon EKS, Azure AKS, Google GKE, Red Hat OpenShift, and Rancher. Rackspace has a team of over 200 certified Kubernetes administrators and developers. Microservices Architecture helping organizations break down monolithic applications into microservices using service mesh technologies like Istio and Linkerd. Serverless Computing implementing AWS Lambda, Azure Functions, Google Cloud Functions for event-driven architectures. CI/CD Pipelines setting up continuous integration and delivery using Jenkins, GitLab, GitHub Actions, Azure DevOps, and AWS CodePipeline. Infrastructure as Code utilizing Terraform, CloudFormation, ARM templates, and Ansible for infrastructure automation. DevOps Transformation providing consulting, training, and implementation services to establish DevOps culture and practices. Observability and Monitoring implementing solutions like Prometheus, Grafana, ELK Stack, Datadog, and cloud-native monitoring tools.''',
                'source': 'curated_knowledge',
                'url': 'https://www.rackspace.com/cloud-native-services',
                'depth': 0
            },
            {
                'title': 'Rackspace Security and Compliance Services',
                'content': '''Rackspace offers comprehensive security and compliance services to protect customers' cloud environments: Security Assessments including vulnerability scanning, penetration testing, security architecture reviews, and risk assessments. Compliance Management supporting frameworks such as HIPAA, PCI-DSS, SOC 2, ISO 27001, FedRAMP, GDPR, and industry-specific regulations. Managed Security Services including 24x7 security monitoring, threat detection and response, security incident management, and managed SIEM solutions. Identity and Access Management implementing robust IAM policies, multi-factor authentication, privileged access management, and zero-trust architectures. Data Protection services including encryption at rest and in transit, key management, data loss prevention, and backup/disaster recovery solutions. Network Security implementing firewalls, web application firewalls (WAF), DDoS protection, VPN, and network segmentation. Security Operations Center providing 24x7 monitoring and response to security events and incidents. Compliance Reporting generating audit-ready documentation and reports for various compliance frameworks. Rackspace maintains its own certifications including SOC 1, SOC 2, ISO 27001, PCI-DSS, and HIPAA, and operates multiple FedRAMP authorized cloud offerings.''',
                'source': 'curated_knowledge',
                'url': 'https://www.rackspace.com/security',
                'depth': 0
            }
        ]
        
        self.data.extend(manual_data)
        logger.info(f"✓ Added {len(manual_data)} curated knowledge entries")
    
    def save_data(self, filename: str = "rackspace_knowledge.json"):
        """Save collected data to JSON and text files"""
        output_path = self.output_dir / filename
        
        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Saved {len(self.data)} documents to {output_path}")
        
        # Save text version for easy reading
        text_path = self.output_dir / "rackspace_knowledge.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            for item in self.data:
                f.write(f"{'='*80}\n")
                f.write(f"Title: {item['title']}\n")
                f.write(f"Source: {item.get('source', 'unknown')}\n")
                f.write(f"URL: {item.get('url', 'N/A')}\n")
                f.write(f"Depth: {item.get('depth', 'N/A')}\n")
                f.write(f"Length: {item.get('content_length', len(item['content']))} characters\n")
                f.write(f"{'-'*80}\n")
                f.write(f"{item['content']}\n\n")
        
        logger.info(f"✓ Saved human-readable version to {text_path}")
        
        # Save statistics
        stats = {
            'total_documents': len(self.data),
            'total_pages_visited': len(self.visited_urls),
            'domains_crawled': list(self.domain_page_count.keys()),
            'pages_per_domain': self.domain_page_count,
            'avg_content_length': sum(d.get('content_length', 0) for d in self.data) / len(self.data) if self.data else 0,
            'total_content_chars': sum(d.get('content_length', 0) for d in self.data)
        }
        
        stats_path = self.output_dir / "crawl_statistics.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"✓ Saved crawl statistics to {stats_path}")
        
        return output_path


def main():
    """Main data collection workflow using BFS crawling"""
    print("\n" + "="*80)
    print("RACKSPACE KNOWLEDGE COLLECTION - BFS WEB CRAWLER")
    print("Building training data for our own fine-tuned model (NO AGENTS)")
    print("="*80 + "\n")
    
    collector = AdvancedRackspaceCollector()
    
    # Step 1: Add curated knowledge base
    collector.add_manual_knowledge()
    
    # Step 2: BFS crawl all Rackspace domains
    try:
        collector.crawl_bfs(RACKSPACE_URLS, max_depth=MAX_CRAWL_DEPTH)
    except KeyboardInterrupt:
        logger.warning("\nCrawling interrupted by user")
    except Exception as e:
        logger.error(f"\nError during crawling: {e}")
    
    # Step 3: Save all collected data
    output_file = collector.save_data()
    
    # Print final summary
    print("\n" + "="*80)
    print("DATA COLLECTION COMPLETE!")
    print("="*80)
    print(f"Total documents collected: {len(collector.data)}")
    print(f"Total pages visited: {len(collector.visited_urls)}")
    print(f"Output saved to: {output_file}")
    print("\nDomain coverage:")
    for domain, count in sorted(collector.domain_page_count.items()):
        print(f"  • {domain}: {count} pages")
    print("\nNext steps:")
    print("  1. python vector_db.py      - Build vector database")
    print("  2. python prepare_dataset.py - Prepare training data")
    print("  3. python fine_tune.py       - Train YOUR OWN model")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
