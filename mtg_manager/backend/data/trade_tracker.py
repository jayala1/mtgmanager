# backend/data/trade_tracker.py
"""
Trade tracking functionality for MTG Collection Manager.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.utils.db import DatabaseManager
from backend.data.models import Trade

class TradeTracker:
    """Manages trade tracking operations."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """Initialize trade tracker."""
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
    
    def add_trade(self, collection_id: int, card_id: int, quantity: int,
                  partner: str = None, note: str = None) -> int:
        """Add a new trade record and return its ID."""
        return self.db_manager.get_last_insert_id(
            """INSERT INTO trades (collection_id, card_id, quantity, partner, note)
               VALUES (?, ?, ?, ?, ?)""",
            (collection_id, card_id, quantity, partner, note)
        )
    
    def get_trades(self, collection_id: int, 
                   start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get trade history with optional date filtering."""
        query = """
            SELECT t.id, t.quantity, t.date, t.partner, t.note,
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
        
        query += " ORDER BY t.date DESC"
        
        rows = self.db_manager.execute_query(query, tuple(params))
        return [dict(row) for row in rows]
    
    def get_trade_stats(self, collection_id: int) -> Dict[str, Any]:
        """Get trade statistics for a collection."""
        query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(quantity) as total_cards_traded,
                COUNT(DISTINCT partner) as unique_partners
            FROM trades
            WHERE collection_id = ?
        """
        
        result = self.db_manager.execute_query(query, (collection_id,))
        if result:
            return dict(result[0])
        
        return {
            'total_trades': 0,
            'total_cards_traded': 0,
            'unique_partners': 0
        }
    
    def delete_trade(self, trade_id: int) -> bool:
        """Delete a trade record."""
        return self.db_manager.execute_update(
            "DELETE FROM trades WHERE id = ?", (trade_id,)
        ) > 0