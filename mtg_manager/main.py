# main.py
"""
MTG Collection Manager - Main Entry Point
A desktop application for managing Magic: The Gathering card collections and deck building.
"""

import tkinter as tk
from tkinter import messagebox
import os
import sys
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.utils.db import DatabaseManager
from frontend.gui import MTGCollectionApp

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mtg_manager.log'),
            logging.StreamHandler()
        ]
    )

def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        'assets/card_images',
        'assets/set_icons',
        'assets/styles',
        'database'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """Main application entry point."""
    try:
        # Setup
        setup_logging()
        create_directories()
        
        logger = logging.getLogger(__name__)
        logger.info("Starting MTG Collection Manager...")
        
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize_database()
        
        # Pre-load ScryfallClient singleton to avoid multiple cache loads
        logger.info("Initializing card database cache...")
        from backend.api.scryfall_client import ScryfallClient
        scryfall_client = ScryfallClient.get_instance()
        logger.info("Card database cache ready")
        
        # Create and run the GUI application
        root = tk.Tk()
        app = MTGCollectionApp(root)
        
        logger.info("Application startup complete")
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Application startup failed: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()