# backend/learning_engine/external_resources.py

import os
import requests
from youtube_search import YoutubeSearch
from serpapi import Client  # Changed import
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

class ExternalResourceFetcher:
    """Fetch external learning resources (images, videos) for concepts"""
    
    def __init__(self):
        self.serpapi_key = getattr(settings, 'SERPAPI_KEY', os.getenv('SERPAPI_KEY', ''))
        self.download_folder = os.path.join(settings.BASE_DIR, 'media', 'concept_images')
        os.makedirs(self.download_folder, exist_ok=True)
    
    def get_youtube_videos(self, topic, max_results=3):
        """
        Search YouTube for videos related to the given topic
        """
        try:
            # Enhance the search query for better educational content
            search_query = f"{topic} tutorial explanation"
            
            # Try-except for youtube-search which might have issues
            try:
                results = YoutubeSearch(search_query, max_results=max_results).to_dict()
            except Exception as e:
                logger.error(f"YouTube search failed: {e}")
                # Fallback: return empty list
                return []
            
            videos = []
            for result in results:
                video = {
                    'title': result.get('title', ''),
                    'url': f"https://youtube.com{result.get('url_suffix', '')}",
                    'channel': result.get('channel', ''),
                    'duration': result.get('duration', ''),
                    'thumbnail': result.get('thumbnails', [''])[0] if result.get('thumbnails') else '',
                    'views': result.get('views', '')
                }
                videos.append(video)
            return videos
        except Exception as e:
            logger.error(f"Error in get_youtube_videos: {e}")
            return []
    
    def get_images(self, query, max_images=3):
        """
        Fetch relevant images/diagrams for a concept using SerpAPI
        """
        if not self.serpapi_key:
            logger.warning("SERPAPI_KEY not set, skipping image fetch")
            return self.get_fallback_images(query, max_images)
        
        try:
            # Priority sites for educational content
            priority_sites = [
                "geeksforgeeks.org",
                "medium.com",
                "tutorialspoint.com",
                "javatpoint.com",
                "programiz.com",
                "w3schools.com"
            ]
            
            image_urls = []
            
            # First try to get images from priority sites
            for site in priority_sites[:max_images]:
                if len(image_urls) >= max_images:
                    break
                
                try:
                    # Using the Client approach for serpapi
                    client = Client(api_key=self.serpapi_key)
                    
                    full_query = f"{query} diagram OR illustration site:{site}"
                    
                    # Create params for image search
                    params = {
                        "engine": "google_images",
                        "q": full_query,
                        "num": 1,
                        "ijn": 0,
                        "api_key": self.serpapi_key
                    }
                    
                    # Make the request
                    result = client.search(params)
                    
                    if hasattr(result, 'get') and result.get('images_results'):
                        images = result['images_results']
                        if images and len(images) > 0:
                            image_urls.append({
                                'url': images[0].get('original', ''),
                                'title': images[0].get('title', ''),
                                'source': site,
                                'thumbnail': images[0].get('thumbnail', '')
                            })
                            logger.info(f"Found image from {site}")
                except Exception as e:
                    logger.error(f"Error fetching image from {site}: {e}")
                    continue
            
            # If we still need more images, do a general search
            if len(image_urls) < max_images:
                try:
                    client = Client(api_key=self.serpapi_key)
                    params = {
                        "engine": "google_images",
                        "q": f"{query} educational diagram",
                        "num": max_images - len(image_urls),
                        "ijn": 0,
                        "api_key": self.serpapi_key
                    }
                    
                    result = client.search(params)
                    
                    if hasattr(result, 'get') and result.get('images_results'):
                        images = result['images_results']
                        for img in images:
                            if len(image_urls) >= max_images:
                                break
                            image_urls.append({
                                'url': img.get('original', ''),
                                'title': img.get('title', ''),
                                'source': img.get('source', ''),
                                'thumbnail': img.get('thumbnail', '')
                            })
                except Exception as e:
                    logger.error(f"Error in general image search: {e}")
            
            return image_urls
            
        except Exception as e:
            logger.error(f"Error in get_images: {e}")
            return self.get_fallback_images(query, max_images)
    
    def get_fallback_images(self, query, max_images=3):
        """Provide fallback placeholder images when API fails"""
        fallback_images = []
        for i in range(min(max_images, 3)):
            fallback_images.append({
                'url': f'https://via.placeholder.com/600x400?text={query.replace(" ", "+")}+Diagram+{i+1}',
                'title': f'{query} - Diagram {i+1}',
                'source': 'placeholder',
                'thumbnail': f'https://via.placeholder.com/300x200?text={query.replace(" ", "+")}+{i+1}'
            })
        return fallback_images
    
    def get_resources_for_concept(self, subject, concept, atom_name=None):
        """
        Get both videos and images for a concept
        """
        # Create search queries
        if atom_name:
            main_query = f"{subject} {concept} {atom_name}"
            specific_query = f"{atom_name} in {concept}"
        else:
            main_query = f"{subject} {concept}"
            specific_query = concept
        
        # Fetch resources with error handling
        videos = []
        images = []
        
        try:
            videos = self.get_youtube_videos(main_query, max_results=2)
        except Exception as e:
            logger.error(f"Error fetching videos: {e}")
        
        try:
            images = self.get_images(main_query, max_images=3)
        except Exception as e:
            logger.error(f"Error fetching images: {e}")
        
        # If no results, try more specific query
        if not videos and not images:
            try:
                videos = self.get_youtube_videos(specific_query, max_results=2)
                images = self.get_images(specific_query, max_images=3)
            except Exception as e:
                logger.error(f"Error in fallback search: {e}")
        
        return {
            'videos': videos,
            'images': images
        }