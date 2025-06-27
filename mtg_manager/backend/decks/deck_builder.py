# backend/decks/deck_builder.py
"""
Deck building functionality for MTG Collection Manager.
"""

import logging
from typing import List, Dict, Any, Optional
from backend.utils.db import DatabaseManager
from backend.data.models import Deck, DeckCard, Card
from backend.data.inventory import InventoryManager

class DeckBuilder:
    """Manages deck building operations."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize deck builder."""
        self.db_manager = db_manager or DatabaseManager()
        self.inventory_manager = InventoryManager(db_manager)
        self.logger = logging.getLogger(__name__)
    
    def create_deck(self, collection_id: int, name: str, format: str = None, 
                    is_commander: bool = False) -> int:
        """Create a new deck and return its ID."""
        return self.db_manager.get_last_insert_id(
            """INSERT INTO decks (collection_id, name, format, is_commander)
               VALUES (?, ?, ?, ?)""",
            (collection_id, name, format, is_commander)
        )
    
    def get_decks(self, collection_id: int) -> List[Dict[str, Any]]:
        """Get all decks for a collection."""
        rows = self.db_manager.execute_query(
            "SELECT * FROM decks WHERE collection_id = ? ORDER BY name",
            (collection_id,)
        )
        return [dict(row) for row in rows]
    
    def get_deck_cards(self, deck_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get all cards in a deck, organized by type (main, commander, sideboard)."""
        query = """
            SELECT dc.id, dc.quantity, dc.is_commander, dc.is_sideboard,
                   c.name, c.set_code, c.collector_number, c.mana_cost,
                   c.type_line, c.image_url, c.colors, c.cmc
            FROM deck_cards dc
            JOIN cards c ON dc.card_id = c.id
            WHERE dc.deck_id = ?
            ORDER BY dc.is_commander DESC, dc.is_sideboard, c.cmc, c.name
        """
        
        rows = self.db_manager.execute_query(query, (deck_id,))
        
        result = {
            'main': [],
            'commander': [],
            'sideboard': []
        }
        
        for row in rows:
            card_data = dict(row)
            if card_data['is_commander']:
                result['commander'].append(card_data)
            elif card_data['is_sideboard']:
                result['sideboard'].append(card_data)
            else:
                result['main'].append(card_data)
        
        return result
    
    def add_card_to_deck(self, deck_id: int, card_name: str, quantity: int = 1,
                         is_commander: bool = False, is_sideboard: bool = False) -> bool:
        """Add a card to a deck."""
        # Search for card
        card_data = self.inventory_manager.scryfall_client.search_card_by_name(card_name)
        
        if not card_data:
            self.logger.error(f"Card '{card_name}' not found")
            return False
        
        # Get or create card
        card_id = self.inventory_manager.get_or_create_card(card_data)
        
        # Check if card already exists in deck
        existing = self.db_manager.execute_query(
            """SELECT id, quantity FROM deck_cards 
               WHERE deck_id = ? AND card_id = ? AND is_commander = ? AND is_sideboard = ?""",
            (deck_id, card_id, is_commander, is_sideboard)
        )
        
        if existing:
            # Update existing quantity
            new_quantity = existing[0]['quantity'] + quantity
            self.db_manager.execute_update(
                "UPDATE deck_cards SET quantity = ? WHERE id = ?",
                (new_quantity, existing[0]['id'])
            )
        else:
            # Add new deck card
            self.db_manager.execute_update(
                """INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander, is_sideboard)
                   VALUES (?, ?, ?, ?, ?)""",
                (deck_id, card_id, quantity, is_commander, is_sideboard)
            )
        
        self.logger.info(f"Added {quantity}x {card_name} to deck")
        return True
    
    def remove_card_from_deck(self, deck_card_id: int) -> bool:
        """Remove a card from a deck."""
        return self.db_manager.execute_update(
            "DELETE FROM deck_cards WHERE id = ?", (deck_card_id,)
        ) > 0
    
    def update_deck_card_quantity(self, deck_card_id: int, quantity: int) -> bool:
        """Update the quantity of a card in a deck."""
        if quantity <= 0:
            return self.remove_card_from_deck(deck_card_id)
        
        return self.db_manager.execute_update(
            "UPDATE deck_cards SET quantity = ? WHERE id = ?",
            (quantity, deck_card_id)
        ) > 0

    def update_deck_card(self, deck_card_id: int, quantity: int = None, 
                         is_commander: bool = None, is_sideboard: bool = None) -> bool:
        """Update a deck card with new values."""
        updates = []
        params = []
        
        if quantity is not None:
            if quantity <= 0:
                # If quantity is 0 or negative, remove the card
                return self.remove_card_from_deck(deck_card_id)
            updates.append("quantity = ?")
            params.append(quantity)
        
        if is_commander is not None:
            updates.append("is_commander = ?")
            params.append(is_commander)
        
        if is_sideboard is not None:
            updates.append("is_sideboard = ?")
            params.append(is_sideboard)
        
        if not updates:
            return True  # No changes needed
        
        params.append(deck_card_id)
        query = f"UPDATE deck_cards SET {', '.join(updates)} WHERE id = ?"
        
        try:
            result = self.db_manager.execute_update(query, tuple(params)) > 0
            if result:
                self.logger.info(f"Updated deck card {deck_card_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to update deck card {deck_card_id}: {e}")
            return False
            
    def get_deck_card_by_id(self, deck_card_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific deck card by ID."""
        try:
            rows = self.db_manager.execute_query(
                """SELECT dc.id, dc.quantity, dc.is_commander, dc.is_sideboard,
                            c.name, c.set_code, c.collector_number, c.mana_cost,
                            c.type_line, c.image_url, c.colors, c.cmc
                   FROM deck_cards dc
                   JOIN cards c ON dc.card_id = c.id
                   WHERE dc.id = ?""",
                (deck_card_id,)
            )
            
            if rows:
                return dict(rows[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get deck card {deck_card_id}: {e}")
            return None
    
    def get_deck_stats(self, deck_id: int) -> Dict[str, Any]:
        """Get statistics for a deck."""
        query = """
            SELECT 
                SUM(dc.quantity) as total_cards,
                COUNT(DISTINCT c.id) as unique_cards,
                AVG(c.cmc) as avg_cmc,
                SUM(CASE WHEN dc.is_sideboard = 0 AND dc.is_commander = 0 THEN dc.quantity ELSE 0 END) as main_deck_count
            FROM deck_cards dc
            JOIN cards c ON dc.card_id = c.id
            WHERE dc.deck_id = ?
        """
        
        result = self.db_manager.execute_query(query, (deck_id,))
        if result:
            stats = dict(result[0])
            # Convert None values to 0
            for key, value in stats.items():
                if value is None:
                    stats[key] = 0
            return stats
        
        return {
            'total_cards': 0,
            'unique_cards': 0,
            'avg_cmc': 0,
            'main_deck_count': 0
        }
    
    def export_deck_to_text(self, deck_id: int) -> str:
        """Export deck to text format."""
        deck_cards = self.get_deck_cards(deck_id)
        
        lines = []
        
        # Commander section
        if deck_cards['commander']:
            lines.append("// Commander")
            for card in deck_cards['commander']:
                lines.append(f"{card['quantity']} {card['name']}")
            lines.append("")
        
        # Main deck
        if deck_cards['main']:
            lines.append("// Main Deck")
            for card in deck_cards['main']:
                lines.append(f"{card['quantity']} {card['name']}")
            lines.append("")
        
        # Sideboard
        if deck_cards['sideboard']:
            lines.append("// Sideboard")
            for card in deck_cards['sideboard']:
                lines.append(f"{card['quantity']} {card['name']}")
        
        return "\n".join(lines)

    def rename_deck(self, deck_id: int, new_name: str) -> bool:
        """Rename a deck."""
        try:
            # Check if name already exists in the same collection
            # First, get the collection_id of the deck being renamed
            current_deck_info = self.db_manager.execute_query(
                "SELECT collection_id FROM decks WHERE id = ?",
                (deck_id,)
            )
            if not current_deck_info:
                self.logger.error(f"Deck {deck_id} not found for renaming.")
                return False
            
            collection_id = current_deck_info[0]['collection_id']

            existing = self.db_manager.execute_query(
                "SELECT id FROM decks WHERE name = ? AND collection_id = ? AND id != ?",
                (new_name, collection_id, deck_id)
            )
            
            if existing:
                self.logger.warning(f"Deck name '{new_name}' already exists in this collection.")
                return False
            
            result = self.db_manager.execute_update(
                "UPDATE decks SET name = ? WHERE id = ?",
                (new_name, deck_id)
            ) > 0
            
            if result:
                self.logger.info(f"Renamed deck {deck_id} to '{new_name}'")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to rename deck {deck_id}: {e}")
            return False
            
    def delete_deck(self, deck_id: int) -> bool:
        """Delete a deck and all its cards."""
        try:
            # Delete deck cards first (foreign key constraint)
            self.db_manager.execute_update(
                "DELETE FROM deck_cards WHERE deck_id = ?",
                (deck_id,)
            )
            
            # Delete the deck
            result = self.db_manager.execute_update(
                "DELETE FROM decks WHERE id = ?",
                (deck_id,)
            ) > 0
            
            if result:
                self.logger.info(f"Deleted deck {deck_id} and all its cards")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to delete deck {deck_id}: {e}")
            return False
            
    def copy_deck(self, source_deck_id: int, new_name: str, copy_options: Dict[str, bool]) -> Optional[int]:
        """
        Copy a deck with specified options.
        
        Args:
            source_deck_id: ID of the deck to copy
            new_name: Name for the new deck
            copy_options: Dict with keys: copy_main, copy_commander, copy_sideboard
            
        Returns:
            ID of the new deck if successful, None otherwise
        """
        try:
            # Get source deck info
            source_deck_rows = self.db_manager.execute_query(
                "SELECT collection_id, format, is_commander FROM decks WHERE id = ?",
                (source_deck_id,)
            )
            
            if not source_deck_rows:
                self.logger.error(f"Source deck {source_deck_id} not found")
                return None
            
            source_deck = source_deck_rows[0]
            
            # Check if name already exists in the target collection
            existing = self.db_manager.execute_query(
                "SELECT id FROM decks WHERE name = ? AND collection_id = ?",
                (new_name, source_deck['collection_id'])
            )
            
            if existing:
                self.logger.warning(f"Deck name '{new_name}' already exists in this collection.")
                return None
            
            # Create new deck
            new_deck_id = self.db_manager.get_last_insert_id(
                "INSERT INTO decks (collection_id, name, format, is_commander) VALUES (?, ?, ?, ?)",
                (source_deck['collection_id'], new_name, source_deck['format'], source_deck['is_commander'])
            )
            
            # Copy cards based on options
            cards_copied = 0
            
            if copy_options.get('copy_main', True):
                # Copy main deck cards
                main_cards = self.db_manager.execute_query(
                    "SELECT card_id, quantity FROM deck_cards WHERE deck_id = ? AND is_commander = 0 AND is_sideboard = 0",
                    (source_deck_id,)
                )
                
                for card in main_cards:
                    self.db_manager.execute_update(
                        "INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander, is_sideboard) VALUES (?, ?, ?, 0, 0)",
                        (new_deck_id, card['card_id'], card['quantity'])
                    )
                    cards_copied += 1
            
            if copy_options.get('copy_commander', True):
                # Copy commander cards
                commander_cards = self.db_manager.execute_query(
                    "SELECT card_id, quantity FROM deck_cards WHERE deck_id = ? AND is_commander = 1",
                    (source_deck_id,)
                )
                
                for card in commander_cards:
                    self.db_manager.execute_update(
                        "INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander, is_sideboard) VALUES (?, ?, ?, 1, 0)",
                        (new_deck_id, card['card_id'], card['quantity'])
                    )
                    cards_copied += 1
            
            if copy_options.get('copy_sideboard', True):
                # Copy sideboard cards
                sideboard_cards = self.db_manager.execute_query(
                    "SELECT card_id, quantity FROM deck_cards WHERE deck_id = ? AND is_sideboard = 1",
                    (source_deck_id,)
                )
                
                for card in sideboard_cards:
                    self.db_manager.execute_update(
                        "INSERT INTO deck_cards (deck_id, card_id, quantity, is_commander, is_sideboard) VALUES (?, ?, ?, 0, 1)",
                        (new_deck_id, card['card_id'], card['quantity'])
                    )
                    cards_copied += 1
            
            self.logger.info(f"Copied deck {source_deck_id} to new deck {new_deck_id} with {cards_copied} cards")
            return new_deck_id
            
        except Exception as e:
            self.logger.error(f"Failed to copy deck {source_deck_id}: {e}")
            return None
            
    def get_deck_by_id(self, deck_id: int) -> Optional[Dict[str, Any]]:
        """Get deck information by ID."""
        try:
            rows = self.db_manager.execute_query(
                "SELECT * FROM decks WHERE id = ?",
                (deck_id,)
            )
            
            if rows:
                return dict(rows[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get deck {deck_id}: {e}")
            return None