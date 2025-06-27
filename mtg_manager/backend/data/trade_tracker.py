# backend/data/trade_tracker.py - Replace with enhanced version
"""
Enhanced trade tracking functionality for MTG Collection Manager.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.utils.db import DatabaseManager
from backend.data.models import Trade

class TradeTracker:
    """Manages trade tracking operations with bidirectional support."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize trade tracker."""
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
    
    def add_trade_transaction(self, collection_id: int, trade_data: Dict[str, Any]) -> int:
        """
        Add a complete trade transaction (can include multiple cards in/out).
        
        Args:
            collection_id: Collection ID
            trade_data: Dictionary containing:
                - partner: Trade partner name
                - note: Optional note
                - cards_out: List of cards given away
                - cards_in: List of cards received
                - date: Trade date (optional, defaults to now)
        
        Returns:
            Trade transaction ID
        """
        try:
            trade_date = trade_data.get('date', datetime.now().isoformat())
            partner = trade_data.get('partner', '')
            note = trade_data.get('note', '')
            
            # Create a trade transaction record
            transaction_id = self.db_manager.get_last_insert_id(
                """INSERT INTO trade_transactions (collection_id, partner, note, date)
                   VALUES (?, ?, ?, ?)""",
                (collection_id, partner, note, trade_date)
            )
            
            # Add cards going out (negative quantities)
            cards_out = trade_data.get('cards_out', [])
            for card_out in cards_out:
                self.add_trade(
                    collection_id, 
                    card_out['card_id'], 
                    -card_out['quantity'],  # Negative for outgoing
                    partner, 
                    f"OUT: {note}",
                    transaction_id
                )
            
            # Add cards coming in (positive quantities)
            cards_in = trade_data.get('cards_in', [])
            for card_in in cards_in:
                self.add_trade(
                    collection_id,
                    card_in['card_id'],
                    card_in['quantity'],  # Positive for incoming
                    partner,
                    f"IN: {note}",
                    transaction_id
                )
            
            self.logger.info(f"Added trade transaction {transaction_id} with {len(cards_out)} out, {len(cards_in)} in")
            return transaction_id
            
        except Exception as e:
            self.logger.error(f"Failed to add trade transaction: {e}")
            raise e
    
    def add_trade(self, collection_id: int, card_id: int, quantity: int,
                  partner: str = None, note: str = None, transaction_id: int = None) -> int:
        """Add a single trade record."""
        return self.db_manager.get_last_insert_id(
            """INSERT INTO trades (collection_id, card_id, quantity, partner, note, transaction_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (collection_id, card_id, quantity, partner, note, transaction_id)
        )
    
    def get_trades(self, collection_id: int, 
                   start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get trade history with optional date filtering."""
        query = """
            SELECT t.id, t.quantity, t.date, t.partner, t.note, t.transaction_id,
                   c.name as card_name, c.set_code, c.collector_number
            FROM trades t
            JOIN cards c ON t.card_id = c.id
            WHERE t.collection_id = ?
        """
        params = [collection_id]
        
        if start_date:
            query += " AND t.date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND t.date <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY t.date DESC, t.transaction_id DESC"
        
        rows = self.db_manager.execute_query(query, tuple(params))
        return [dict(row) for row in rows]
    
    def get_trade_transactions(self, collection_id: int) -> List[Dict[str, Any]]:
        """Get grouped trade transactions."""
        query = """
            SELECT tt.id, tt.partner, tt.note, tt.date,
                   COUNT(t.id) as total_cards,
                   SUM(CASE WHEN t.quantity > 0 THEN t.quantity ELSE 0 END) as cards_in,
                   SUM(CASE WHEN t.quantity < 0 THEN ABS(t.quantity) ELSE 0 END) as cards_out
            FROM trade_transactions tt
            LEFT JOIN trades t ON tt.id = t.transaction_id
            WHERE tt.collection_id = ?
            GROUP BY tt.id, tt.partner, tt.note, tt.date
            ORDER BY tt.date DESC
        """
        
        rows = self.db_manager.execute_query(query, (collection_id,))
        return [dict(row) for row in rows]
    
    def get_trade_stats(self, collection_id: int) -> Dict[str, Any]:
        """Get trade statistics for a collection."""
        query = """
            SELECT 
                COUNT(DISTINCT transaction_id) as total_transactions,
                COUNT(*) as total_trade_records,
                SUM(CASE WHEN quantity > 0 THEN quantity ELSE 0 END) as total_cards_received,
                SUM(CASE WHEN quantity < 0 THEN ABS(quantity) ELSE 0 END) as total_cards_given,
                COUNT(DISTINCT partner) as unique_partners
            FROM trades
            WHERE collection_id = ?
        """
        
        result = self.db_manager.execute_query(query, (collection_id,))
        if result:
            return dict(result[0])
        
        return {
            'total_transactions': 0,
            'total_trade_records': 0,
            'total_cards_received': 0,
            'total_cards_given': 0,
            'unique_partners': 0
        }
    
    def delete_trade_transaction(self, transaction_id: int) -> bool:
        """Delete an entire trade transaction and all its records."""
        try:
            # Delete individual trade records
            self.db_manager.execute_update(
                "DELETE FROM trades WHERE transaction_id = ?", (transaction_id,)
            )
            
            # Delete transaction record
            result = self.db_manager.execute_update(
                "DELETE FROM trade_transactions WHERE id = ?", (transaction_id,)
            ) > 0
            
            if result:
                self.logger.info(f"Deleted trade transaction {transaction_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to delete trade transaction {transaction_id}: {e}")
            return False
    
    def get_cards_traded_with_partner(self, collection_id: int, partner: str) -> List[Dict[str, Any]]:
        """Get all cards traded with a specific partner."""
        query = """
            SELECT t.quantity, t.date, t.note,
                   c.name as card_name, c.set_code
            FROM trades t
            JOIN cards c ON t.card_id = c.id
            WHERE t.collection_id = ? AND t.partner = ?
            ORDER BY t.date DESC
        """
        
        rows = self.db_manager.execute_query(query, (collection_id, partner))
        return [dict(row) for row in rows]