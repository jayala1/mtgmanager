# backend/utils/image_manager.py
"""
Image management for MTG Collection Manager.
Handles downloading, caching, and processing card images.
"""

import os
import requests
import logging
from typing import Optional, Tuple
from PIL import Image, ImageTk
import threading
import hashlib
import time

class ImageManager:
    """Manages card image downloading, caching, and processing."""
    
    def __init__(self, cache_dir: str = "assets/card_images"):
        """Initialize image manager."""
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Image size presets
        self.image_sizes = {
            'thumbnail': (146, 204),    # Small preview
            'medium': (223, 311),       # Standard display
            'large': (488, 680),        # Detailed view
            'original': None            # Full size
        }
        
        # Cache for loaded PIL images to avoid reloading
        self._image_cache = {}
        self._download_queue = set()    # Track ongoing downloads
        
        self.logger.info(f"ImageManager initialized with cache directory: {cache_dir}")
    
    def _get_cache_filename(self, image_url: str, size: str = 'medium') -> str:
        """Generate cache filename from image URL and size."""
        # Create hash of URL for filename
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        return f"{url_hash}_{size}.png"
    
    def _get_cache_path(self, image_url: str, size: str = 'medium') -> str:
        """Get full cache file path."""
        filename = self._get_cache_filename(image_url, size)
        return os.path.join(self.cache_dir, filename)
    
    def is_image_cached(self, image_url: str, size: str = 'medium') -> bool:
        """Check if image is already cached."""
        if not image_url:
            return False
        
        cache_path = self._get_cache_path(image_url, size)
        return os.path.exists(cache_path)
    
    def download_image(self, image_url: str, size: str = 'medium', 
                       callback: Optional[callable] = None) -> bool:
        """
        Download and cache an image.
        
        Args:
            image_url: URL of the image to download
            size: Size preset to save ('thumbnail', 'medium', 'large', 'original')
            callback: Optional callback function to call when download completes
            
        Returns:
            True if successful, False otherwise
        """
        if not image_url:
            return False
        
        # Check if already cached
        if self.is_image_cached(image_url, size):
            if callback:
                callback(True, self._get_cache_path(image_url, size))
            return True
        
        # Check if already downloading
        cache_key = f"{image_url}_{size}"
        if cache_key in self._download_queue:
            return False
        
        self._download_queue.add(cache_key)
        
        def download_worker():
            try:
                self.logger.debug(f"Downloading image: {image_url}")
                
                # Download image with timeout
                response = requests.get(image_url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Load image with PIL
                image = Image.open(response.raw)
                
                # Resize if needed
                if size in self.image_sizes and self.image_sizes[size] is not None:
                    target_size = self.image_sizes[size]
                    # Maintain aspect ratio
                    image.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Save to cache
                cache_path = self._get_cache_path(image_url, size)
                image.save(cache_path, 'PNG', optimize=True)
                
                self.logger.debug(f"Image cached: {cache_path}")
                
                # Call callback if provided
                if callback:
                    callback(True, cache_path)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to download image {image_url}: {e}")
                if callback:
                    callback(False, None)
                return False
            
            finally:
                # Remove from download queue
                self._download_queue.discard(cache_key)
        
        # Start download in background thread
        threading.Thread(target=download_worker, daemon=True).start()
        return True
    
    def get_image_path(self, image_url: str, size: str = 'medium') -> Optional[str]:
        """Get cached image path if it exists."""
        if not image_url:
            return None
        
        cache_path = self._get_cache_path(image_url, size)
        return cache_path if os.path.exists(cache_path) else None
    
    def load_image_for_tkinter(self, image_url: str, size: str = 'medium', 
                               fallback_size: Tuple[int, int] = (146, 204)) -> Optional[ImageTk.PhotoImage]:
        """
        Load an image for Tkinter display.
        
        Args:
            image_url: URL of the image
            size: Size preset
            fallback_size: Size for placeholder if image not available
            
        Returns:
            PhotoImage for Tkinter or None
        """
        try:
            self.logger.debug(f"Loading image for Tkinter: {image_url}")
            
            # Check cache first
            cache_key = f"{image_url}_{size}"
            if cache_key in self._image_cache:
                self.logger.debug(f"Image found in memory cache: {cache_key}")
                return self._image_cache[cache_key]
            
            # Try to load from cache
            cache_path = self.get_image_path(image_url, size)
            self.logger.debug(f"Cache path: {cache_path}")
            
            if cache_path and os.path.exists(cache_path):
                self.logger.debug(f"Loading image from cache: {cache_path}")
                # Load from cache
                pil_image = Image.open(cache_path)
                tk_image = ImageTk.PhotoImage(pil_image)
                
                # Cache the loaded image
                self._image_cache[cache_key] = tk_image
                self.logger.debug(f"Image loaded successfully: {cache_path}")
                return tk_image
            
            else:
                self.logger.debug(f"Image not in cache, returning placeholder")
                # Return placeholder
                return self.create_placeholder_image(fallback_size)
                
        except Exception as e:
            self.logger.error(f"Failed to load image for Tkinter: {e}")
            return self.create_placeholder_image(fallback_size)
    
    def create_placeholder_image(self, size: Tuple[int, int] = (146, 204)) -> ImageTk.PhotoImage:
        """Create a placeholder image when card image is not available."""
        try:
            # Create a simple placeholder
            image = Image.new('RGB', size, color='#2C3E50')  # Dark blue-gray
            
            # Add some text or pattern
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(image)
            
            # Try to use a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            # Add text
            text = "MTG\nCard\nImage"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font, align='center')
            
            # Add border
            draw.rectangle([0, 0, size[0]-1, size[1]-1], outline='white', width=2)
            
            return ImageTk.PhotoImage(image)
            
        except Exception as e:
            self.logger.error(f"Failed to create placeholder image: {e}")
            # Return minimal placeholder
            image = Image.new('RGB', size, color='gray')
            return ImageTk.PhotoImage(image)
    
    def preload_images(self, image_urls: list, size: str = 'medium', 
                       progress_callback: Optional[callable] = None):
        """
        Preload multiple images in background.
        
        Args:
            image_urls: List of image URLs to preload
            size: Size preset to download
            progress_callback: Optional callback with (current, total) progress
        """
        if not image_urls:
            return
        
        def preload_worker():
            total = len(image_urls)
            completed = 0
            
            for i, url in enumerate(image_urls):
                if url and not self.is_image_cached(url, size):
                    self.download_image(url, size)
                    # Small delay to avoid overwhelming the server
                    time.sleep(0.1)
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
        
        threading.Thread(target=preload_worker, daemon=True).start()
    
    def clear_cache(self, older_than_days: int = 30) -> int:
        """
        Clear old cached images.
        
        Args:
            older_than_days: Remove images older than this many days
            
        Returns:
            Number of files removed
        """
        try:
            removed_count = 0
            cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        removed_count += 1
            
            self.logger.info(f"Cleared {removed_count} old cached images")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return 0
    
    def get_cache_stats(self) -> dict:
        """Get statistics about the image cache."""
        try:
            total_files = 0
            total_size = 0
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    total_files += 1
                    total_size += os.path.getsize(file_path)
            
            return {
                'total_files': total_files,
                'total_size_mb': total_size / (1024 * 1024),
                'cache_directory': self.cache_dir
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {'total_files': 0, 'total_size_mb': 0, 'cache_directory': self.cache_dir}