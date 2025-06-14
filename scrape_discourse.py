import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import trafilatura
from urllib.parse import urljoin, urlparse
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscourseScraper:
    def __init__(self, base_url: str = "https://discourse.onlinedegree.iitm.ac.in/"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_category_topics(self, category_slug: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get topics from a specific category within date range"""
        topics = []
        page = 0
        
        while True:
            try:
                # Discourse API endpoint for category topics
                url = f"{self.base_url}/c/{category_slug}.json"
                params = {'page': page}
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                topic_list = data.get('topic_list', {})
                topic_items = topic_list.get('topics', [])
                
                if not topic_items:
                    break
                
                for topic in topic_items:
                    created_at = datetime.fromisoformat(topic['created_at'].replace('Z', '+00:00'))
                    
                    # Filter by date range
                    if start_date <= created_at <= end_date:
                        topic_data = {
                            'id': topic['id'],
                            'title': topic['title'],
                            'slug': topic['slug'],
                            'category_id': topic['category_id'],
                            'created_at': topic['created_at'],
                            'posts_count': topic['posts_count'],
                            'url': f"{self.base_url}/t/{topic['slug']}/{topic['id']}"
                        }
                        topics.append(topic_data)
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching category {category_slug}, page {page}: {str(e)}")
                break
        
        return topics
    
    def get_topic_content(self, topic_id: int, topic_slug: str) -> Optional[Dict]:
        """Get the full content of a topic including posts"""
        try:
            url = f"{self.base_url}/t/{topic_slug}/{topic_id}.json"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract main post content
            posts = data.get('post_stream', {}).get('posts', [])
            if not posts:
                return None
            
            main_post = posts[0]  # First post is the main topic post
            
            # Extract clean text content
            raw_content = main_post.get('cooked', '')
            if raw_content:
                # Use trafilatura to extract clean text
                clean_content = trafilatura.extract(raw_content, include_links=False)
                if not clean_content:
                    # Fallback to BeautifulSoup
                    soup = BeautifulSoup(raw_content, 'html.parser')
                    clean_content = soup.get_text(strip=True)
            else:
                clean_content = main_post.get('raw', '')
            
            # Collect replies
            replies = []
            for post in posts[1:]:  # Skip the main post
                reply_content = post.get('cooked', '')
                if reply_content:
                    clean_reply = trafilatura.extract(reply_content, include_links=False)
                    if not clean_reply:
                        soup = BeautifulSoup(reply_content, 'html.parser')
                        clean_reply = soup.get_text(strip=True)
                else:
                    clean_reply = post.get('raw', '')
                
                if clean_reply and len(clean_reply.strip()) > 10:  # Only meaningful replies
                    replies.append({
                        'id': post['id'],
                        'username': post.get('username', 'Unknown'),
                        'created_at': post.get('created_at', ''),
                        'content': clean_reply[:500]  # Limit reply length
                    })
            
            return {
                'title': data.get('title', ''),
                'content': clean_content,
                'replies': replies[:5],  # Limit to first 5 replies
                'tags': data.get('tags', []),
                'category_id': data.get('category_id'),
                'created_at': main_post.get('created_at', ''),
                'username': main_post.get('username', 'Unknown'),
                'url': f"{self.base_url}/t/{topic_slug}/{topic_id}"
            }
            
        except Exception as e:
            logger.error(f"Error fetching topic {topic_id}: {str(e)}")
            return None
    
    def find_tds_categories(self) -> List[str]:
        """Find categories related to Tools in Data Science"""
        try:
            # Get site categories
            url = f"{self.base_url}/categories.json"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            categories = data.get('category_list', {}).get('categories', [])
            
            tds_categories = []
            tds_keywords = ['tools', 'data', 'science', 'tds', 'python', 'programming']
            
            for category in categories:
                name = category.get('name', '').lower()
                slug = category.get('slug', '')
                
                # Check if category name contains TDS-related keywords
                if any(keyword in name for keyword in tds_keywords):
                    tds_categories.append(slug)
                    logger.info(f"Found TDS-related category: {name} ({slug})")
            
            # If no specific categories found, use general categories
            if not tds_categories:
                tds_categories = ['general', 'support', 'questions', 'help']
                logger.info("Using general categories as fallback")
            
            return tds_categories
            
        except Exception as e:
            logger.error(f"Error finding TDS categories: {str(e)}")
            return ['general']  # Fallback to general category
    
    def scrape_posts(self, start_date: datetime, end_date: datetime, max_posts: int = 100) -> List[Dict]:
        """Scrape Discourse posts within the specified date range"""
        logger.info(f"Starting scrape from {start_date} to {end_date}")
        
        # Find TDS-related categories
        categories = self.find_tds_categories()
        logger.info(f"Scraping categories: {categories}")
        
        all_posts = []
        
        for category in categories:
            logger.info(f"Scraping category: {category}")
            
            # Get topics from this category
            topics = self.get_category_topics(category, start_date, end_date)
            logger.info(f"Found {len(topics)} topics in {category}")
            
            for topic in topics:
                if len(all_posts) >= max_posts:
                    break
                
                # Get topic content
                content = self.get_topic_content(topic['id'], topic['slug'])
                if content:
                    # Merge topic metadata with content
                    post_data = {**topic, **content}
                    all_posts.append(post_data)
                    logger.info(f"Scraped: {topic['title'][:50]}...")
                
                time.sleep(1)  # Rate limiting
            
            if len(all_posts) >= max_posts:
                break
        
        logger.info(f"Scraped {len(all_posts)} posts total")
        return all_posts
    
    def save_posts(self, posts: List[Dict], filename: str = "data/tds_posts.json"):
        """Save scraped posts to JSON file"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Add metadata
        data = {
            'scraped_at': datetime.now().isoformat(),
            'total_posts': len(posts),
            'posts': posts
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data['posts'], f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(posts)} posts to {filename}")

def main():
    """Main function to run the scraper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Discourse posts for TDS Virtual TA')
    parser.add_argument('--start-date', type=str, default='2025-01-01', 
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2025-04-14', 
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--max-posts', type=int, default=100, 
                       help='Maximum number of posts to scrape')
    parser.add_argument('--output', type=str, default='data/tds_posts.json',
                       help='Output file path')
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    # Initialize scraper
    scraper = DiscourseScraper()
    
    # Scrape posts
    posts = scraper.scrape_posts(start_date, end_date, args.max_posts)
    
    # Save posts
    scraper.save_posts(posts, args.output)
    
    print(f"Scraping completed! {len(posts)} posts saved to {args.output}")

if __name__ == "__main__":
    main()
