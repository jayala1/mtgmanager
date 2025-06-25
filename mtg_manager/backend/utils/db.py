# backend/utils/db.py
"""
Database management utilities for MTG Collection Manager.
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """Manages SQLite database operations for the MTG Collection Manager."""
    
    def __init__(self, db_path: str = "database/mtg_collection.db"):
        """Initialize database manager with the specified database path."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize_database(self):
        """Create all necessary tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Collections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cards table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    oracle_id TEXT,
                    collector_number TEXT,
                    set_code TEXT,
                    image_url TEXT,
                    mana_cost TEXT,
                    type_line TEXT,
                    oracle_text TEXT,
                    colors TEXT,
                    layout TEXT,
                    cmc INTEGER,
                    UNIQUE(oracle_id, set_code, collector_number)
                )
            """)
            
            # Inventory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id INTEGER,
                    card_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    foil BOOLEAN DEFAULT FALSE,
                    condition TEXT DEFAULT 'Near Mint',
                    FOREIGN KEY (collection_id) REFERENCES collections (id),
                    FOREIGN KEY (card_id) REFERENCES cards (id)
                )
            """)
            
            # Decks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id INTEGER,
                    name TEXT NOT NULL,
                    format TEXT,
                    is_commander BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (collection_id) REFERENCES collections (id)
                )
            """)
            
            # Deck cards table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deck_cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deck_id INTEGER,
                    card_id INTEGER,
                    quantity INTEGER DEFAULT 1,
                    is_commander BOOLEAN DEFAULT FALSE,
                    is_sideboard BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (deck_id) REFERENCES decks (id),
                    FOREIGN KEY (card_id) REFERENCES cards (id)
                )
            """)
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id INTEGER,
                    card_id INTEGER,
                    quantity INTEGER,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    partner TEXT,
                    note TEXT,
                    FOREIGN KEY (collection_id) REFERENCES collections (id),
                    FOREIGN KEY (card_id) REFERENCES cards (id)
                )
            """)
            
            conn.commit()
            
            # Create default collection if none exists
            cursor.execute("SELECT COUNT(*) FROM collections")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO collections (name) VALUES (?)", ("Default Collection",))
                conn.commit()
                
        self.logger.info("Database initialized successfully")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def get_last_insert_id(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the last inserted ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid