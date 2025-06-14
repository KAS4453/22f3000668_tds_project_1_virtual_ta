import json
import os
from typing import Dict, List, Any, Optional
from fuzzywuzzy import fuzz, process
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class QAEngine:
    def __init__(self):
        self.discourse_posts = []
        self.course_content = []
        self.load_data()
    
    def load_data(self):
        """Load discourse posts and course content from JSON files"""
        try:
            # Load discourse posts
            discourse_path = "data/tds_posts.json"
            if os.path.exists(discourse_path):
                with open(discourse_path, 'r', encoding='utf-8') as f:
                    self.discourse_posts = json.load(f)
                logger.info(f"Loaded {len(self.discourse_posts)} discourse posts")
            else:
                logger.warning(f"Discourse posts file not found: {discourse_path}")
                self.discourse_posts = []
            
            # Load course content
            content_path = "data/course_content.json"
            if os.path.exists(content_path):
                with open(content_path, 'r', encoding='utf-8') as f:
                    self.course_content = json.load(f)
                logger.info(f"Loaded {len(self.course_content)} course content items")
            else:
                logger.warning(f"Course content file not found: {content_path}")
                self.course_content = []
        
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            self.discourse_posts = []
            self.course_content = []
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters but keep alphanumeric and basic punctuation
        text = re.sub(r'[^\w\s\-\.\?\!]', '', text)
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from question text"""
        # Common data science and programming terms
        keywords = []
        text_lower = text.lower()
        
        # Technical terms that might be important
        tech_terms = [
            'python', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'sklearn',
            'jupyter', 'notebook', 'dataframe', 'csv', 'api', 'sql', 'database',
            'visualization', 'plot', 'chart', 'regression', 'classification',
            'machine learning', 'ml', 'data science', 'statistics', 'analysis'
        ]
        
        for term in tech_terms:
            if term in text_lower:
                keywords.append(term)
        
        # Extract words that are likely to be important (longer than 3 characters)
        words = re.findall(r'\b\w{4,}\b', text_lower)
        keywords.extend(words[:10])  # Limit to top 10 words
        
        return list(set(keywords))  # Remove duplicates
    
    def find_similar_posts(self, question: str, threshold: int = 60) -> List[Dict]:
        """Find discourse posts similar to the question"""
        if not self.discourse_posts:
            return []
        
        question_processed = self.preprocess_text(question)
        similar_posts = []
        
        for post in self.discourse_posts:
            # Combine title and content for matching
            post_text = f"{post.get('title', '')} {post.get('content', '')}"
            post_text_processed = self.preprocess_text(post_text)
            
            # Calculate similarity scores
            title_score = fuzz.partial_ratio(question_processed, self.preprocess_text(post.get('title', '')))
            content_score = fuzz.partial_ratio(question_processed, post_text_processed)
            combined_score = max(title_score, content_score * 0.8)  # Weight content slightly less
            
            # Check for keyword matches
            keywords = self.extract_keywords(question)
            keyword_matches = sum(1 for keyword in keywords if keyword in post_text_processed)
            keyword_bonus = min(keyword_matches * 10, 30)  # Max 30 point bonus
            
            final_score = combined_score + keyword_bonus
            
            if final_score >= threshold:
                similar_posts.append({
                    'post': post,
                    'score': final_score,
                    'title_score': title_score,
                    'content_score': content_score,
                    'keyword_matches': keyword_matches
                })
        
        # Sort by score (highest first)
        similar_posts.sort(key=lambda x: x['score'], reverse=True)
        return similar_posts[:5]  # Return top 5 matches
    
    def find_relevant_content(self, question: str, threshold: int = 50) -> List[Dict]:
        """Find relevant course content"""
        if not self.course_content:
            return []
        
        question_processed = self.preprocess_text(question)
        relevant_content = []
        
        for content in self.course_content:
            # Combine title and description for matching
            content_text = f"{content.get('title', '')} {content.get('description', '')}"
            content_text_processed = self.preprocess_text(content_text)
            
            # Calculate similarity score
            score = fuzz.partial_ratio(question_processed, content_text_processed)
            
            # Check for keyword matches
            keywords = self.extract_keywords(question)
            keyword_matches = sum(1 for keyword in keywords if keyword in content_text_processed)
            keyword_bonus = min(keyword_matches * 15, 40)  # Max 40 point bonus
            
            final_score = score + keyword_bonus
            
            if final_score >= threshold:
                relevant_content.append({
                    'content': content,
                    'score': final_score,
                    'keyword_matches': keyword_matches
                })
        
        # Sort by score (highest first)
        relevant_content.sort(key=lambda x: x['score'], reverse=True)
        return relevant_content[:3]  # Return top 3 matches
    
    def generate_answer(self, question: str, similar_posts: List[Dict], relevant_content: List[Dict]) -> str:
        """Generate a comprehensive answer based on found content"""
        answer_parts = []
        
        # Start with a direct response
        if similar_posts or relevant_content:
            answer_parts.append("Based on the available course materials and forum discussions, here's what I found:")
        else:
            return ("I couldn't find specific information related to your question in the current knowledge base. "
                   "Please try rephrasing your question or contact the course instructor for assistance.")
        
        # Add information from course content
        if relevant_content:
            answer_parts.append("\n**Course Content:**")
            for item in relevant_content[:2]:  # Limit to top 2
                content = item['content']
                title = content.get('title', 'Untitled')
                description = content.get('description', '')
                if description:
                    answer_parts.append(f"• **{title}**: {description[:200]}...")
                else:
                    answer_parts.append(f"• **{title}**")
        
        # Add information from forum posts
        if similar_posts:
            answer_parts.append("\n**Related Forum Discussions:**")
            for item in similar_posts[:2]:  # Limit to top 2
                post = item['post']
                title = post.get('title', 'Untitled Post')
                content = post.get('content', '')
                if content:
                    # Extract first meaningful sentence or paragraph
                    content_preview = content[:300].split('.')[0] + '.'
                    answer_parts.append(f"• **{title}**: {content_preview}")
                else:
                    answer_parts.append(f"• **{title}**")
        
        # Add a helpful closing
        answer_parts.append("\nFor more detailed information, please check the supporting links provided below.")
        
        return '\n'.join(answer_parts)
    
    def get_answer(self, question: str) -> Dict[str, Any]:
        """Main method to get answer for a question"""
        if not question or not question.strip():
            return {
                "answer": "Please provide a valid question.",
                "links": []
            }
        
        # Find similar posts and relevant content
        similar_posts = self.find_similar_posts(question)
        relevant_content = self.find_relevant_content(question)
        
        # Generate answer
        answer = self.generate_answer(question, similar_posts, relevant_content)
        
        # Prepare links
        links = []
        
        # Add course content links
        for item in relevant_content:
            content = item['content']
            if content.get('url'):
                links.append({
                    "url": content['url'],
                    "text": f"Course Material: {content.get('title', 'Untitled')}"
                })
        
        # Add forum post links
        for item in similar_posts:
            post = item['post']
            if post.get('url'):
                links.append({
                    "url": post['url'],
                    "text": f"Forum Discussion: {post.get('title', 'Untitled Post')}"
                })
        
        # Limit total links to 5
        links = links[:5]
        
        return {
            "answer": answer,
            "links": links
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        return {
            "discourse_posts": len(self.discourse_posts),
            "course_content_items": len(self.course_content),
            "total_items": len(self.discourse_posts) + len(self.course_content),
            "last_updated": datetime.now().isoformat()
        }
