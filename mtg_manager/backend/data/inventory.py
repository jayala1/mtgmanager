# backend/data/inventory.py
"""
Inventory management for MTG Collection Manager.
"""

import logging
from typing import List, Optional, Dict, Any
from backend.utils.db import DatabaseManager
from backend.data.models import Collection, Card, InventoryItem
from backend.api.scryfall_client import ScryfallClient

class InventoryManager:
    """Manages card inventory operations."""
    
    def __init__(self, db_manager: DatabaseManager = None, scryfall_client: ScryfallClient = None):
        """Initialize inventory manager."""
        self.db_manager = db_manager or DatabaseManager()
        # Use provided client or get singleton instance
        self.scryfall_client = scryfall_client or ScryfallClient.get_instance()
        self.logger = logging.getLogger(__name__)
    
    def get_collections(self) -> List[Collection]:
        """Get all collections."""
        rows = self.db_manager.execute_query("SELECT * FROM collections ORDER BY name")
        return [Collection(id=row['id'], name=row['name'], created_at=row['created_at']) 
                for row in rows]
    
    def create_collection(self, name: str) -> int:
        """Create a new collection and return its ID."""
        return self.db_manager.get_last_insert_id(
            "INSERT INTO collections (name) VALUES (?)", (name,)
        )
    
    def get_or_create_card(self, card_data: Dict[str, Any]) -> int:
        """Get existing card or create new one, return card ID."""
        try:
            oracle_id = card_data.get('oracle_id')
            set_code = card_data.get('set', '').lower() # Normalize set_code to lowercase
            collector_number = card_data.get('collector_number')
            card_name = card_data.get('name')
            
            self.logger.debug(f"Looking for card: {card_name} (oracle_id: {oracle_id}, set: {set_code}, collector: {collector_number})")
            
            # Strategy 1: Most specific - oracle_id, set_code, and collector_number
            if oracle_id and set_code and collector_number:
                existing = self.db_manager.execute_query(
                    """SELECT id FROM cards 
                       WHERE oracle_id = ? AND set_code = ? AND collector_number = ?""",
                    (oracle_id, set_code, collector_number)
                )
                if existing:
                    self.logger.debug(f"Found card by oracle_id+set+collector: {existing[0]['id']}")
                    return existing[0]['id']
            
            # Strategy 2: oracle_id and set_code (less specific, but still strong for unique printings)
            # This might catch non-collector-numbered variants like promos, or if collector_number is missing in data.
            if oracle_id and set_code:
                existing = self.db_manager.execute_query(
                    """SELECT id FROM cards 
                       WHERE oracle_id = ? AND set_code = ?""",
                    (oracle_id, set_code)
                )
                if existing:
                    self.logger.debug(f"Found card by oracle_id+set: {existing[0]['id']}")
                    return existing[0]['id']
            
            # Strategy 3: exact name and set match (case insensitive)
            # Useful for when oracle_id might be missing or inconsistent, but set is known.
            if card_name and set_code:
                existing = self.db_manager.execute_query(
                    """SELECT id FROM cards 
                       WHERE LOWER(name) = LOWER(?) AND LOWER(set_code) = LOWER(?)""",
                    (card_name, set_code)
                )
                if existing:
                    self.logger.debug(f"Found card by name+set: {existing[0]['id']}")
                    return existing[0]['id']
            
            # Strategy 4: exact name match only (last resort for finding any version of the card)
            if card_name:
                existing = self.db_manager.execute_query(
                    """SELECT id FROM cards WHERE LOWER(name) = LOWER(?)""",
                    (card_name,)
                )
                if existing:
                    self.logger.debug(f"Found card by name only: {existing[0]['id']}")
                    return existing[0]['id']
            
            # Strategy 5: Check if we have any card with similar oracle_id (for variants/reprints)
            # This is primarily for ensuring the *logical* card exists, even if the specific printing differs.
            # It's less for direct match, more for ensuring base card data is present.
            if oracle_id:
                existing = self.db_manager.execute_query(
                    """SELECT id, name, set_code FROM cards WHERE oracle_id = ?""",
                    (oracle_id,)
                )
                if existing:
                    self.logger.debug(f"Found card with same oracle_id: {existing[0]['id']} - {existing[0]['name']} ({existing[0]['set_code']})")
                    return existing[0]['id']
            
            # No existing card found, create new one
            self.logger.info(f"Creating new card: {card_name} ({set_code})")
            card = Card.from_scryfall_data(card_data)
            
            try:
                card_id = self.db_manager.get_last_insert_id(
                    """INSERT INTO cards 
                       (name, oracle_id, collector_number, set_code, image_url, mana_cost, 
                        type_line, oracle_text, colors, layout, cmc)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (card.name, card.oracle_id, card.collector_number, card.set_code,
                     card.image_url, card.mana_cost, card.type_line, card.oracle_text,
                     card.colors, card.layout, card.cmc)
                )
                self.logger.info(f"Created new card with ID: {card_id}")
                return card_id
                
            except Exception as insert_error:
                # This block handles race conditions or other unique constraint violations
                if "UNIQUE constraint failed" in str(insert_error):
                    self.logger.warning(f"Constraint violation for {card_name}, attempting to find existing card after failed insert.")
                    
                    # Re-attempt the most specific search after a potential race condition
                    if oracle_id and set_code and collector_number:
                        existing = self.db_manager.execute_query(
                            """SELECT id FROM cards 
                               WHERE oracle_id = ? AND set_code = ? AND collector_number = ?""",
                            (oracle_id, set_code, collector_number)
                        )
                        if existing:
                            self.logger.info(f"Found existing card by specific details after race condition: {existing[0]['id']}")
                            return existing[0]['id']
                    # Fallback to oracle_id and set_code if collector number was not available or precise match failed
                    elif oracle_id and set_code:
                            existing = self.db_manager.execute_query(
                                """SELECT id FROM cards 
                                   WHERE oracle_id = ? AND set_code = ?""",
                                (oracle_id, set_code)
                            )
                            if existing:
                                self.logger.info(f"Found existing card by oracle_id+set after race condition: {existing[0]['id']}")
                                return existing[0]['id']
                    
                    # If still not found after re-querying, re-raise the specific error
                    raise Exception(f"Failed to create card '{card_name}' due to unique constraint, but could not retrieve existing card. Error: {str(insert_error)}")
                
                # Re-raise if it's a different error
                raise Exception(f"Failed to create card '{card_name}': {str(insert_error)}")
                
        except Exception as e:
            self.logger.error(f"Failed to get or create card '{card_name}': {e}", exc_info=True)
            raise e
    
    def add_card_to_inventory(self, collection_id: int, card_name: str, 
                              quantity: int = 1, foil: bool = False, 
                              condition: str = "Near Mint") -> bool:
        """Add a card to inventory by searching for it first."""
        # Search for card via Scryfall
        card_data = self.scryfall_client.search_card_by_name(card_name)
        
        if not card_data:
            self.logger.error(f"Card '{card_name}' not found")
            return False
        
        # Get or create card in database
        try:
            card_id = self.get_or_create_card(card_data)
        except Exception as e:
            self.logger.error(f"Failed to get or create card for inventory: {e}")
            return False

        # Check if card already exists in inventory
        existing = self.db_manager.execute_query(
            """SELECT id, quantity FROM inventory 
               WHERE collection_id = ? AND card_id = ? AND foil = ? AND condition = ?""",
            (collection_id, card_id, foil, condition)
        )
        
        if existing:
            # Update existing quantity
            new_quantity = existing[0]['quantity'] + quantity
            self.db_manager.execute_update(
                "UPDATE inventory SET quantity = ? WHERE id = ?",
                (new_quantity, existing[0]['id'])
            )
        else:
            # Add new inventory item
            self.db_manager.execute_update(
                """INSERT INTO inventory (collection_id, card_id, quantity, foil, condition)
                   VALUES (?, ?, ?, ?, ?)""",
                (collection_id, card_id, quantity, foil, condition)
            )
        
        self.logger.info(f"Added {quantity}x {card_name} to inventory")
        return True
    
    def get_inventory(self, collection_id: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get inventory items with optional filtering."""
        query = """
            SELECT i.id, i.quantity, i.foil, i.condition,
                   c.name, c.set_code, c.collector_number, c.mana_cost, 
                   c.type_line, c.image_url, c.colors, c.cmc, c.oracle_text
            FROM inventory i
            JOIN cards c ON i.card_id = c.id
            WHERE i.collection_id = ?
        """
        params = [collection_id]
        
        # Apply filters
        if filters:
            if filters.get('name'):
                query += " AND c.name LIKE ?"
                params.append(f"%{filters['name']}%")
            
            if filters.get('set_code'):
                query += " AND c.set_code = ?"
                params.append(filters['set_code'])
            
            if filters.get('colors'):
                # This will need careful handling for multi-color searches (e.g., 'WU' for Azorius)
                # For a simple LIKE, it will match partial strings.
                query += " AND c.colors LIKE ?"
                params.append(f"%{filters['colors']}%")
            
            if filters.get('foil') is not None:
                query += " AND i.foil = ?"
                params.append(filters['foil'])
        
        query += " ORDER BY c.name"
        
        rows = self.db_manager.execute_query(query, tuple(params))
        return [dict(row) for row in rows]
    
    def update_inventory_item(self, item_id: int, quantity: int = None, 
                              condition: str = None) -> bool:
        """Update an inventory item."""
        updates = []
        params = []
        
        if quantity is not None:
            updates.append("quantity = ?")
            params.append(quantity)
        
        if condition is not None:
            updates.append("condition = ?")
            params.append(condition)
        
        if not updates:
            return False
        
        params.append(item_id)
        query = f"UPDATE inventory SET {', '.join(updates)} WHERE id = ?"
        
        return self.db_manager.execute_update(query, tuple(params)) > 0
    
    def update_inventory_item_full(self, item_id: int, quantity: int = None, 
                                   foil: bool = None, condition: str = None) -> bool:
        """Update an inventory item with multiple fields."""
        updates = []
        params = []
        
        if quantity is not None:
            if quantity <= 0:
                # If quantity is 0 or negative, delete the item
                return self.remove_from_inventory(item_id)
            updates.append("quantity = ?")
            params.append(quantity)
        
        if foil is not None:
            updates.append("foil = ?")
            params.append(foil)
        
        if condition is not None:
            updates.append("condition = ?")
            params.append(condition)
        
        if not updates:
            return True  # No changes needed
        
        params.append(item_id)
        query = f"UPDATE inventory SET {', '.join(updates)} WHERE id = ?"
        
        try:
            result = self.db_manager.execute_update(query, tuple(params)) > 0
            if result:
                self.logger.info(f"Updated inventory item {item_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to update inventory item {item_id}: {e}")
            return False
            
    def get_inventory_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific inventory item by ID."""
        try:
            rows = self.db_manager.execute_query(
                """SELECT i.id, i.quantity, i.foil, i.condition,
                                    c.name, c.set_code, c.collector_number, c.mana_cost, 
                                    c.type_line, c.image_url, c.colors, c.cmc, c.oracle_text
                   FROM inventory i
                   JOIN cards c ON i.card_id = c.id
                   WHERE i.id = ?""",
                (item_id,)
            )
            
            if rows:
                return dict(rows[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get inventory item {item_id}: {e}")
            return None

    def remove_from_inventory(self, item_id: int) -> bool:
        """Remove an item from inventory."""
        return self.db_manager.execute_update(
            "DELETE FROM inventory WHERE id = ?", (item_id,)
        ) > 0