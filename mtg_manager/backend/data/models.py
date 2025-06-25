# backend/data/models.py
"""
Data models for MTG Collection Manager.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class Collection:
    """Represents a card collection."""
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None

@dataclass
class Card:
    """Represents a Magic: The Gathering card."""
    id: Optional[int] = None
    name: str = ""
    oracle_id: Optional[str] = None
    collector_number: Optional[str] = None
    set_code: Optional[str] = None
    image_url: Optional[str] = None
    mana_cost: Optional[str] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    colors: Optional[str] = None  # JSON string of color array
    layout: Optional[str] = None
    cmc: Optional[int] = None
    
    @classmethod
    def from_scryfall_data(cls, data: Dict[str, Any]) -> 'Card':
        """Create a Card instance from Scryfall API data."""
        return cls(
            name=data.get('name', ''),
            oracle_id=data.get('oracle_id'),
            collector_number=data.get('collector_number'),
            set_code=data.get('set'),
            image_url=data.get('image_uris', {}).get('normal'),
            mana_cost=data.get('mana_cost'),
            type_line=data.get('type_line'),
            oracle_text=data.get('oracle_text'),
            colors=','.join(data.get('colors', [])),
            layout=data.get('layout'),
            cmc=data.get('cmc', 0)
        )

@dataclass
class InventoryItem:
    """Represents a card in inventory."""
    id: Optional[int] = None
    collection_id: int = 0
    card_id: int = 0
    quantity: int = 1
    foil: bool = False
    condition: str = "Near Mint"

@dataclass
class Deck:
    """Represents a deck."""
    id: Optional[int] = None
    collection_id: int = 0
    name: str = ""
    format: Optional[str] = None
    is_commander: bool = False
    created_at: Optional[datetime] = None

@dataclass
class DeckCard:
    """Represents a card in a deck."""
    id: Optional[int] = None
    deck_id: int = 0
    card_id: int = 0
    quantity: int = 1
    is_commander: bool = False
    is_sideboard: bool = False

@dataclass
class Trade:
    """Represents a trade transaction."""
    id: Optional[int] = None
    collection_id: int = 0
    card_id: int = 0
    quantity: int = 0
    date: Optional[datetime] = None
    partner: Optional[str] = None
    note: Optional[str] = None