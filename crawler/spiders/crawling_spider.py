import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import os
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

class KamcoInvestSpider(CrawlSpider):
    name = "kamco_crawler"
    allowed_domains = ["kamcoinvest.com"]
    start_urls = ["https://www.kamcoinvest.com/research/type/455"]
    
    def __init__(self):
        self.download_path = "kamco_reports"
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        self.downloaded = False  # Flag to stop after downloading first report
        self.target_keywords = ["kuwait", "- en", "- eng"]  # Keywords to identify Kuwait EN reports
    
    rules = (
        Rule(
            LinkExtractor(allow=[r'research/type/455']),
            callback='parse_page',
            follow=False
        ),
    )
    
    def parse_page(self, response):
        """Find the latest Kuwait English report with - EN suffix"""
        self.logger.info(f"Parsing page: {response.url}")
        
        if self.downloaded:
            return  # Stop if already downloaded
        
        # Find all text elements and links that might contain Kuwait EN reports
        all_text_elements = response.xpath('//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "kuwait") and (contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "- en") or contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "- eng"))]')
        
        # Also check for links with Kuwait and EN in href or title attributes
        kuwait_links = response.xpath('//a[contains(translate(@href, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "kuwait") or contains(translate(@title, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "kuwait") or contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "kuwait")]')
        
        self.logger.info(f"Found {len(all_text_elements)} Kuwait EN text elements")
        self.logger.info(f"Found {len(kuwait_links)} Kuwait-related links")
        
        target_elements = []
        
        for element in all_text_elements:
            text = element.xpath('string(.)').get('').lower()
            if 'kuwait' in text and ('- en' in text or '- eng' in text):
                target_elements.append(element)
        
        for link in kuwait_links:
            link_text = link.xpath('string(.)').get('').lower()
            link_href = link.xpath('@href').get('').lower()
            link_title = link.xpath('@title').get('').lower()
            
            full_text = f"{link_text} {link_href} {link_title}"
            if 'kuwait' in full_text and ('- en' in full_text or '- eng' in full_text):
                target_elements.append(link)
        
        self.logger.info(f"Found {len(target_elements)} Kuwait EN target elements")
        
        if target_elements:
            first_element = target_elements[0]
            
            link = None
            
            if first_element.xpath('self::a'):
                link = first_element.xpath('@href').get()
            else:
                link = first_element.xpath('.//a/@href | ./following-sibling::*//a/@href | ./preceding-sibling::*//a/@href | ../a/@href | ../../a/@href').get()
            
            if link:
                absolute_url = urljoin(response.url, link)
                self.logger.info(f"Processing latest Kuwait English report: {absolute_url}")
                
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.parse_item,
                    meta={'is_latest': True, 'element_text': first_element.xpath('string(.)').get('')}
                )
            else:
                self.logger.warning("No link found for Kuwait EN report element")
        
        if not target_elements:
            self.logger.warning("No Kuwait EN reports found, trying fallback approach")
            all_research_links = response.xpath('//a[contains(@href, "research/")]/@href').getall()
            
            for research_link in all_research_links[:5]: 
                absolute_url = urljoin(response.url, research_link)
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.check_page_for_kuwait,
                    meta={'is_fallback': True}
                )
    
    def check_page_for_kuwait(self, response):
        """Check if a page contains Kuwait content before processing"""
        page_text = response.xpath('string(//body)').get('').lower()
        
        if 'kuwait' in page_text and ('- en' in page_text or '- eng' in page_text):
            self.logger.info(f"Found Kuwait EN content on fallback page: {response.url}")
            return self.parse_item(response)
        else:
            self.logger.info(f"No Kuwait EN content found on: {response.url}")
            return
    
    def parse_item(self, response):
        """Extract PDF from the Kuwait report page"""
        self.logger.info(f"Parsing Kuwait report page: {response.url}")
        
        if self.downloaded:
            return
        
        pdf_links = []
        
        pdf_links.extend(response.xpath('//a[contains(@href, ".pdf")]/@href').getall())
        
        pdf_links.extend(response.xpath('//a[contains(@class, "download") or contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "download")]/@href').getall())

        pdf_links.extend(response.xpath('//a[contains(@href, "download")]/@href').getall())
        
        pdf_links.extend(response.xpath('//a[contains(@class, "btn") and (contains(@href, ".pdf") or contains(text(), "PDF"))]/@href').getall())
        
        pdf_links = list(set([link for link in pdf_links if link and not link.startswith('#') and link.strip()]))
        
        self.logger.info(f"Found {len(pdf_links)} potential PDF links: {pdf_links}")
        
        if pdf_links:
            kuwait_pdfs = [link for link in pdf_links if 'kuwait' in link.lower()]
            
            if kuwait_pdfs:
                pdf_url = kuwait_pdfs[0]
                self.logger.info(f"Using Kuwait-specific PDF: {pdf_url}")
            else:
                pdf_url = pdf_links[0]
                self.logger.info(f"Using first available PDF: {pdf_url}")
            
            absolute_url = urljoin(response.url, pdf_url)
            filename = self.generate_filename(absolute_url, response)
            
            yield scrapy.Request(
                url=absolute_url,
                callback=self.save_pdf,
                meta={
                    'filename': filename, 
                    'report_url': response.url,
                    'element_text': response.meta.get('element_text', '')
                }
            )
        else:
            self.logger.warning("No PDF links found on report page")
            doc_links = response.xpath('//a[contains(@href, "download") or contains(@href, "file") or contains(@href, "document")]/@href').getall()
            
            if doc_links:
                self.logger.info(f"Found alternative document links: {doc_links}")
                doc_url = doc_links[0]
                absolute_url = urljoin(response.url, doc_url)
                filename = self.generate_filename(absolute_url, response)
                
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.save_pdf,
                    meta={'filename': filename, 'report_url': response.url}
                )
        
        yield {
            'page_url': response.url,
            'title': response.xpath('//title/text()').get('').strip(),
            'pdf_links_found': len(pdf_links),
            'is_latest_report': True,
            'page_content_preview': response.xpath('string(//body)').get('')[:200] + '...'
        }
    
    def generate_filename(self, url, response=None):
        """Generate filename based on URL, page title, or use Kuwait report name"""
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
    
        if not filename or not filename.endswith('.pdf'):
            if response:
                title = response.xpath('//title/text()').get('').strip()
                if title and 'kuwait' in title.lower():
                    clean_title = re.sub(r'[^\w\s-]', '', title)
                    clean_title = re.sub(r'\s+', '_', clean_title)
                    filename = f"{clean_title[:50]}.pdf"
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"Kuwait_Report_{timestamp}.pdf"
            else:
                filename = "Latest_Kuwait_Report.pdf"
        
        if not filename.endswith('.pdf'):
            filename += '.pdf'
            
        return filename
    
    def save_pdf(self, response):
        """Save the PDF file"""
        if self.downloaded:
            return
            
        filename = response.meta['filename']
        filepath = os.path.join(self.download_path, filename)
        
        try:
            content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()
            
            if 'pdf' in content_type or response.body.startswith(b'%PDF'):
                with open(filepath, 'wb') as f:
                    f.write(response.body)
                
                self.logger.info(f"✅ Latest Kuwait English report downloaded: {filepath}")
                self.downloaded = True
                
                yield {
                    'downloaded_pdf': filepath,
                    'file_size': len(response.body),
                    'source_url': response.url,
                    'report_page': response.meta['report_url'],
                    'filename': filename,
                    'content_type': content_type,
                    'success': True,
                    'element_text': response.meta.get('element_text', '')
                }
            else:
                self.logger.warning(f"Response is not a PDF (Content-Type: {content_type}), checking for redirect or download links")
                
                pdf_links = response.xpath('//a[contains(@href, ".pdf")]/@href').getall()
                if pdf_links:
                    pdf_url = pdf_links[0]
                    absolute_url = urljoin(response.url, pdf_url)
                    
                    yield scrapy.Request(
                        url=absolute_url,
                        callback=self.save_pdf,
                        meta=response.meta
                    )
                else:
                    yield {
                        'error': f'Response is not a PDF file (Content-Type: {content_type})',
                        'source_url': response.url,
                        'filename': filename,
                        'success': False
                    }
            
        except Exception as e:
            self.logger.error(f"Failed to save {filepath}: {str(e)}")
            yield {
                'error': str(e),
                'source_url': response.url,
                'filename': filename,
                'success': False
            }
    
    def parse_start_url(self, response):
        """Override to ensure start URL is processed"""
        return self.parse_page(response)