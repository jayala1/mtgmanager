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
                    cmc INTEGER DEFAULT 0,
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
            
            # Trade transactions table (NEW)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id INTEGER,
                    partner TEXT,
                    note TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (collection_id) REFERENCES collections (id)
                )
            """)
            
            # Check if trades table exists and has the new schema
            cursor.execute("PRAGMA table_info(trades)")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            if not columns:
                # Trades table doesn't exist, create with new schema
                self.logger.info("Creating trades table with new schema...")
                cursor.execute("""
                    CREATE TABLE trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        collection_id INTEGER,
                        card_id INTEGER,
                        quantity INTEGER,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        partner TEXT,
                        note TEXT,
                        transaction_id INTEGER,
                        FOREIGN KEY (collection_id) REFERENCES collections (id),
                        FOREIGN KEY (card_id) REFERENCES cards (id),
                        FOREIGN KEY (transaction_id) REFERENCES trade_transactions (id)
                    )
                """)
            elif 'transaction_id' not in columns:
                # Table exists but missing transaction_id, need to migrate
                self.logger.info("Migrating trades table to new schema...")
                
                try:
                    # First, backup existing trades data
                    cursor.execute("SELECT * FROM trades")
                    existing_trades = cursor.fetchall()
                    
                    # Get column names for the existing data
                    old_columns = [description[0] for description in cursor.description]
                    
                    # Drop old trades table
                    cursor.execute("DROP TABLE trades")
                    
                    # Create new trades table with proper schema
                    cursor.execute("""
                        CREATE TABLE trades (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            collection_id INTEGER,
                            card_id INTEGER,
                            quantity INTEGER,
                            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            partner TEXT,
                            note TEXT,
                            transaction_id INTEGER,
                            FOREIGN KEY (collection_id) REFERENCES collections (id),
                            FOREIGN KEY (card_id) REFERENCES cards (id),
                            FOREIGN KEY (transaction_id) REFERENCES trade_transactions (id)
                        )
                    """)
                    
                    # Migrate existing data if any
                    for trade_row in existing_trades:
                        # Convert row to dictionary
                        trade = dict(zip(old_columns, trade_row))
                        
                        # Create a transaction for each old trade
                        cursor.execute("""
                            INSERT INTO trade_transactions (collection_id, partner, note, date)
                            VALUES (?, ?, ?, ?)
                        """, (
                            trade.get('collection_id', 1), 
                            trade.get('partner', 'Unknown'), 
                            trade.get('note', ''), 
                            trade.get('date', 'CURRENT_TIMESTAMP')
                        ))
                        transaction_id = cursor.lastrowid
                        
                        # Insert the trade with the transaction_id
                        cursor.execute("""
                            INSERT INTO trades (collection_id, card_id, quantity, date, partner, note, transaction_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            trade.get('collection_id', 1),
                            trade.get('card_id', 0),
                            trade.get('quantity', 0),
                            trade.get('date', 'CURRENT_TIMESTAMP'),
                            trade.get('partner', 'Unknown'),
                            trade.get('note', ''),
                            transaction_id
                        ))
                    
                    self.logger.info(f"Migrated {len(existing_trades)} trade records")
                    
                except Exception as e:
                    self.logger.error(f"Error during trades table migration: {e}")
                    # Create empty table if migration fails
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS trades (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            collection_id INTEGER,
                            card_id INTEGER,
                            quantity INTEGER,
                            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            partner TEXT,
                            note TEXT,
                            transaction_id INTEGER,
                            FOREIGN KEY (collection_id) REFERENCES collections (id),
                            FOREIGN KEY (card_id) REFERENCES cards (id),
                            FOREIGN KEY (transaction_id) REFERENCES trade_transactions (id)
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