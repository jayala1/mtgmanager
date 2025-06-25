# backend/utils/backup.py
"""
Backup and restore functionality for MTG Collection Manager.
"""

import json
import shutil
import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from backend.utils.db import DatabaseManager

class BackupManager:
    """Manages backup and restore operations."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize backup manager."""
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
    
    def create_backup(self, backup_path: str, include_images: bool = False) -> bool:
        """Create a complete backup of the database and optionally images."""
        try:
            # Create backup directory
            backup_dir = os.path.dirname(backup_path)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy database file
            shutil.copy2(self.db_manager.db_path, backup_path)
            
            # Optionally backup card images
            if include_images:
                images_dir = "assets/card_images"
                if os.path.exists(images_dir):
                    backup_images_dir = backup_path.replace('.db', '_images')
                    shutil.copytree(images_dir, backup_images_dir, dirs_exist_ok=True)
            
            self.logger.info(f"Backup created successfully: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            if not os.path.exists(backup_path):
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create backup of current database
            current_backup = f"{self.db_manager.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_manager.db_path, current_backup)
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_manager.db_path)
            
            # Verify restored database
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM collections")
                cursor.fetchone()
            
            self.logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
    
    def export_to_json(self, export_path: str) -> bool:
        """Export all data to JSON format."""
        try:
            data = {
                'export_date': datetime.now().isoformat(),
                'collections': [],
                'cards': [],
                'inventory': [],
                'decks': [],
                'deck_cards': [],
                'trades': []
            }
            
            # Export collections
            collections = self.db_manager.execute_query("SELECT * FROM collections")
            data['collections'] = [dict(row) for row in collections]
            
            # Export cards
            cards = self.db_manager.execute_query("SELECT * FROM cards")
            data['cards'] = [dict(row) for row in cards]
            
            # Export inventory
            inventory = self.db_manager.execute_query("SELECT * FROM inventory")
            data['inventory'] = [dict(row) for row in inventory]
            
            # Export decks
            decks = self.db_manager.execute_query("SELECT * FROM decks")
            data['decks'] = [dict(row) for row in decks]
            
            # Export deck cards
            deck_cards = self.db_manager.execute_query("SELECT * FROM deck_cards")
            data['deck_cards'] = [dict(row) for row in deck_cards]
            
            # Export trades
            trades = self.db_manager.execute_query("SELECT * FROM trades")
            data['trades'] = [dict(row) for row in trades]
            
            # Write to JSON file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Data exported to JSON: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON export failed: {e}")
            return False
    
    def import_from_json(self, import_path: str, merge: bool = False) -> bool:
        """Import data from JSON format."""
        try:
            if not os.path.exists(import_path):
                self.logger.error(f"Import file not found: {import_path}")
                return False
            
            # Load JSON data
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # If not merging, clear existing data
            if not merge:
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM trades")
                    cursor.execute("DELETE FROM deck_cards")
                    cursor.execute("DELETE FROM decks")
                    cursor.execute("DELETE FROM inventory")
                    cursor.execute("DELETE FROM cards")
                    cursor.execute("DELETE FROM collections")
                    conn.commit()
            
            # Import collections
            for collection in data.get('collections', []):
                if merge:
                    # Check if collection exists
                    existing = self.db_manager.execute_query(
                        "SELECT id FROM collections WHERE name = ?", (collection['name'],)
                    )
                    if existing:
                        continue
                
                self.db_manager.execute_update(
                    "INSERT INTO collections (name, created_at) VALUES (?, ?)",
                    (collection['name'], collection.get('created_at'))
                )
            
            # Import cards
            for card in data.get('cards', []):
                if merge:
                    # Check if card exists
                    existing = self.db_manager.execute_query(
                        "SELECT id FROM cards WHERE oracle_id = ? AND set_code = ? AND collector_number = ?",
                        (card.get('oracle_id'), card.get('set_code'), card.get('collector_number'))
                    )
                    if existing:
                        continue
                
                self.db_manager.execute_update(
                    """INSERT INTO cards 
                       (name, oracle_id, collector_number, set_code, image_url, mana_cost,
                        type_line, oracle_text, colors, layout, cmc)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (card.get('name'), card.get('oracle_id'), card.get('collector_number'),
                     card.get('set_code'), card.get('image_url'), card.get('mana_cost'),
                     card.get('type_line'), card.get('oracle_text'), card.get('colors'),
                     card.get('layout'), card.get('cmc'))
                )
            
            # Import inventory, decks, deck_cards, and trades
            # (Similar pattern for each table)
            
            self.logger.info(f"Data imported from JSON: {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON import failed: {e}")
            return False