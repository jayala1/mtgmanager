# backend/utils/csv_handler.py
"""
CSV import/export functionality for MTG Collection Manager.
"""

import csv
import logging
import os
from typing import List, Dict, Any, Optional
from backend.utils.db import DatabaseManager
from backend.data.inventory import InventoryManager
from backend.api.scryfall_client import ScryfallClient

class CSVHandler:
    """Handles CSV import and export operations."""
    
    def __init__(self, db_manager: DatabaseManager = None, scryfall_client: ScryfallClient = None):
        """Initialize CSV handler with optional shared instances."""
        self.db_manager = db_manager or DatabaseManager()
        # Use provided scryfall_client to avoid reloading cache
        self.scryfall_client = scryfall_client or ScryfallClient.get_instance() # Ensure singleton is used
        self.inventory_manager = InventoryManager(self.db_manager, self.scryfall_client)
        self.logger = logging.getLogger(__name__)
    
    def export_inventory_to_csv(self, collection_id: int, file_path: str) -> bool:
        """Export inventory to CSV format."""
        try:
            self.logger.info(f"Starting CSV export for collection {collection_id}")
            
            # Get inventory data
            inventory = self.inventory_manager.get_inventory(collection_id)
            
            if not inventory:
                self.logger.warning("No inventory items found to export")
                return True  # Not an error, just empty
            
            # Define CSV headers (including Set Name)
            headers = [
                'Card Name', 'Set Code', 'Set Name', 'Collector Number', 
                'Quantity', 'Foil', 'Condition', 'Mana Cost', 'Type Line', 
                'Colors', 'CMC', 'Oracle Text'
            ]
            
            self.logger.info(f"Exporting {len(inventory)} inventory items")
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for i, item in enumerate(inventory):
                    # Only log progress every 100 items to reduce spam
                    if i % 100 == 0 and i > 0:
                        self.logger.info(f"Exported {i}/{len(inventory)} items")
                    
                    # Get additional card data from cache only (no API calls)
                    card_data = None
                    set_name = ''
                    
                    if item['name']:
                        card_data = self.scryfall_client.search_card_in_cache(item['name'])
                        if card_data:
                            set_name = card_data.get('set_name', '')
                    
                    writer.writerow({
                        'Card Name': item['name'],
                        'Set Code': item['set_code'] or '',
                        'Set Name': set_name,
                        'Collector Number': item['collector_number'] or '',
                        'Quantity': item['quantity'],
                        'Foil': 'Yes' if item['foil'] else 'No',
                        'Condition': item['condition'],
                        'Mana Cost': item['mana_cost'] or '',
                        'Type Line': item['type_line'] or '',
                        'Colors': item['colors'] or '',
                        'CMC': item.get('cmc', ''), # Changed to use item.get('cmc') directly since get_inventory now fetches it
                        'Oracle Text': item.get('oracle_text', '') # Changed to use item.get('oracle_text') directly since get_inventory now fetches it
                    })
            
            self.logger.info(f"Successfully exported {len(inventory)} cards to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export inventory to CSV: {e}")
            return False
    
    def import_inventory_from_csv(self, collection_id: int, file_path: str, 
                                  update_existing: bool = False) -> Dict[str, Any]:
        """Import inventory from CSV format."""
        results = {
            'success': False,
            'imported': 0,
            'skipped': 0,
            'errors': [],
            'total_rows': 0
        }
        
        try:
            if not os.path.exists(file_path):
                results['errors'].append(f"File not found: {file_path}")
                return results
            
            self.logger.info(f"Starting CSV import from {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # Try to detect the CSV format
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                # Validate required columns
                required_columns = ['Card Name', 'Quantity']
                missing_columns = [col for col in required_columns if col not in reader.fieldnames]
                
                if missing_columns:
                    results['errors'].append(f"Missing required columns: {missing_columns}")
                    return results
                
                # Convert to list to get total count and avoid multiple iterations
                rows = list(reader)
                total_rows = len(rows)
                results['total_rows'] = total_rows
                
                self.logger.info(f"Processing {total_rows} rows from CSV")
                
                for row_num, row in enumerate(rows, start=2):  # Start at 2 for header
                    # Log progress every 50 rows
                    if (row_num - 1) % 50 == 0:
                        self.logger.info(f"Processing row {row_num - 1}/{total_rows}")
                    
                    try:
                        card_name = row.get('Card Name', '').strip()
                        if not card_name:
                            results['errors'].append(f"Row {row_num}: Empty card name")
                            continue
                        
                        # Parse quantity
                        try:
                            quantity = int(row.get('Quantity', '1'))
                            if quantity <= 0:
                                results['errors'].append(f"Row {row_num}: Invalid quantity '{quantity}'. Quantity must be positive.")
                                continue
                        except ValueError:
                            results['errors'].append(f"Row {row_num}: Invalid quantity '{row.get('Quantity')}'. Must be a number.")
                            continue
                        
                        # Parse foil status
                        foil_text = row.get('Foil', 'No').strip().lower()
                        foil = foil_text in ['yes', 'true', '1', 'foil']
                        
                        # Get condition
                        condition = row.get('Condition', 'Near Mint').strip()
                        valid_conditions = ['Mint', 'Near Mint', 'Lightly Played', 'Moderately Played', 'Heavily Played', 'Damaged']
                        if condition not in valid_conditions:
                            self.logger.warning(f"Row {row_num}: Invalid condition '{condition}' for '{card_name}'. Defaulting to 'Near Mint'.")
                            condition = 'Near Mint'
                        
                        # Use set code and collector number for more precise search if available
                        set_code = row.get('Set Code', '').strip().lower()
                        collector_number = row.get('Collector Number', '').strip()

                        card_data = None
                        if set_code and collector_number:
                            # Try precise search first
                            card_data = self.scryfall_client.search_card_by_set_and_collector_number(set_code, collector_number)
                            if card_data and card_data['name'].lower() != card_name.lower():
                                self.logger.warning(f"Row {row_num}: Card name '{card_name}' in CSV does not match Scryfall result '{card_data['name']}' for {set_code}/{collector_number}. Using Scryfall data.")
                                # We can proceed with the found card_data, but it's good to log
                        
                        if not card_data:
                            # Fallback to name search if precise search fails or isn't possible
                            card_data = self.scryfall_client.search_card_by_name(card_name)
                            
                        if not card_data:
                            results['skipped'] += 1
                            results['errors'].append(f"Row {row_num}: Card '{card_name}' (Set: {set_code}, Collector #: {collector_number}) not found via Scryfall.")
                            continue
                        
                        # Get or create card in database
                        try:
                            card_id = self.inventory_manager.get_or_create_card(card_data)
                        except Exception as card_error:
                            results['skipped'] += 1
                            results['errors'].append(f"Row {row_num}: Failed to save card '{card_name}' to database: {str(card_error)}")
                            self.logger.error(f"Error saving card data for '{card_name}': {card_error}", exc_info=True)
                            continue
                        
                        # Check if card already exists in inventory for this collection, card_id, foil, and condition
                        existing_inventory_item = self.db_manager.execute_query(
                            """SELECT id, quantity FROM inventory 
                               WHERE collection_id = ? AND card_id = ? AND foil = ? AND condition = ?""",
                            (collection_id, card_id, foil, condition)
                        )
                        
                        if existing_inventory_item:
                            if update_existing:
                                # Update existing quantity
                                new_quantity = existing_inventory_item[0]['quantity'] + quantity
                                self.db_manager.execute_update(
                                    "UPDATE inventory SET quantity = ? WHERE id = ?",
                                    (new_quantity, existing_inventory_item[0]['id'])
                                )
                                results['imported'] += 1
                                self.logger.info(f"Row {row_num}: Updated {quantity}x '{card_name}' (total {new_quantity}) to collection {collection_id}")
                            else:
                                results['skipped'] += 1
                                results['errors'].append(f"Row {row_num}: Card '{card_name}' (Foil: {foil}, Cond: {condition}) already exists. Skipped. (Use 'Update Existing' option to add quantity).")
                                self.logger.info(f"Row {row_num}: Skipped existing card '{card_name}' in collection {collection_id}")
                        else:
                            # Add new inventory item
                            self.db_manager.execute_update(
                                """INSERT INTO inventory (collection_id, card_id, quantity, foil, condition)
                                   VALUES (?, ?, ?, ?, ?)""",
                                (collection_id, card_id, quantity, foil, condition)
                            )
                            results['imported'] += 1
                            self.logger.info(f"Row {row_num}: Added {quantity}x '{card_name}' to collection {collection_id}")
                        
                    except Exception as e:
                        results['errors'].append(f"Row {row_num}: General error processing '{row.get('Card Name', 'N/A')}': {str(e)}")
                        self.logger.error(f"Error processing row {row_num}: {e}", exc_info=True)
                
                results['success'] = results['imported'] > 0
                self.logger.info(f"CSV import completed: {results['imported']} imported, {results['skipped']} skipped, {len(results['errors'])} errors")
                
        except Exception as e:
            results['errors'].append(f"Failed to read or process CSV file: {e}")
            self.logger.error(f"Failed to import CSV: {e}", exc_info=True)
        
        return results
    
    def export_deck_to_csv(self, deck_id: int, file_path: str) -> bool:
        """Export deck to CSV format."""
        try:
            from backend.decks.deck_builder import DeckBuilder
            deck_builder = DeckBuilder(self.db_manager)
            
            # Get deck cards
            deck_cards = deck_builder.get_deck_cards(deck_id)
            
            headers = [
                'Card Name', 'Quantity', 'Section', 'Set Code', 
                'Collector Number', 'Mana Cost', 'Type Line', 'CMC'
            ]
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                # Export each section
                for section, cards in deck_cards.items():
                    section_name = section.title()
                    if section == 'main':
                        section_name = 'Main Deck'
                    
                    for card in cards:
                        writer.writerow({
                            'Card Name': card['name'],
                            'Quantity': card['quantity'],
                            'Section': section_name,
                            'Set Code': card.get('set_code', ''),
                            'Collector Number': card.get('collector_number', ''),
                            'Mana Cost': card.get('mana_cost', ''),
                            'Type Line': card.get('type_line', ''),
                            'CMC': card.get('cmc', 0)
                        })
            
            total_cards = sum(len(cards) for cards in deck_cards.values())
            self.logger.info(f"Exported deck with {total_cards} cards to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export deck to CSV: {e}")
            return False
    
    def get_sample_csv_format(self) -> str:
        """Return a sample CSV format string for user reference."""
        return """Card Name,Set Code,Collector Number,Quantity,Foil,Condition
Lightning Bolt,M11,146,4,No,Near Mint
Black Lotus,LEA,232,1,No,Lightly Played
Jace, the Mind Sculptor,WWK,31,2,Yes,Near Mint"""