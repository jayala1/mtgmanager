# frontend/dialogs/card_details_dialog.py
"""
Card Details dialog for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional

class CardDetailsDialog:
    """Dialog for viewing detailed card information."""
    
    def __init__(self, parent, card_data: Dict[str, Any], app):
        """
        Initialize card details dialog.
        
        Args:
            parent: Parent window
            card_data: Dictionary containing card data
            app: Main application instance
        """
        self.parent = parent
        self.card_data = card_data
        self.app = app
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the card details dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"Card Details - {self.card_data.get('name', 'Unknown Card')}")
        self.dialog.geometry("600x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"600x700+{x}+{y}")
        
        # Create notebook for different sections
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Card Info Tab
        self.create_card_info_tab(notebook)
        
        # Game Info Tab
        self.create_game_info_tab(notebook)
        
        # Collection Info Tab
        self.create_collection_info_tab(notebook)
        
        # Close button
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # Bind escape key
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
    
    def create_card_info_tab(self, notebook):
        """Create the main card information tab."""
        card_frame = ttk.Frame(notebook)
        notebook.add(card_frame, text="Card Info")
        
        # Create scrollable frame
        canvas = tk.Canvas(card_frame)
        scrollbar = ttk.Scrollbar(card_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Card header
        header_frame = ttk.LabelFrame(scrollable_frame, text="Basic Information")
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Card name
        name_label = ttk.Label(header_frame, text=self.card_data.get('name', 'Unknown'), 
                              font=('TkDefaultFont', 14, 'bold'))
        name_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Mana cost
        mana_cost = self.card_data.get('mana_cost', '')
        if mana_cost:
            ttk.Label(header_frame, text=f"Mana Cost: {mana_cost}", 
                     font=('TkDefaultFont', 11)).pack(anchor=tk.W, padx=10, pady=2)
        
        # CMC
        cmc = self.card_data.get('cmc', 0)
        ttk.Label(header_frame, text=f"Converted Mana Cost: {cmc}").pack(anchor=tk.W, padx=10, pady=2)
        
        # Type line
        type_line = self.card_data.get('type_line', '')
        if type_line:
            ttk.Label(header_frame, text=f"Type: {type_line}", 
                     font=('TkDefaultFont', 10)).pack(anchor=tk.W, padx=10, pady=2)
        
        # Colors
        colors = self.card_data.get('colors', [])
        if colors:
            colors_text = ', '.join(colors) if isinstance(colors, list) else str(colors)
            ttk.Label(header_frame, text=f"Colors: {colors_text}").pack(anchor=tk.W, padx=10, pady=(2, 10))
        
        # Oracle text
        oracle_frame = ttk.LabelFrame(scrollable_frame, text="Oracle Text")
        oracle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        oracle_text = self.card_data.get('oracle_text', 'No oracle text available.')
        
        text_widget = tk.Text(oracle_frame, wrap=tk.WORD, height=8, state=tk.DISABLED,
                             bg=self.dialog.cget('bg'), relief=tk.FLAT)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(1.0, oracle_text)
        text_widget.config(state=tk.DISABLED)
        
        # Set information
        set_frame = ttk.LabelFrame(scrollable_frame, text="Set Information")
        set_frame.pack(fill=tk.X, padx=10, pady=10)
        
        set_code = self.card_data.get('set', self.card_data.get('set_code', ''))
        set_name = self.card_data.get('set_name', '')
        collector_number = self.card_data.get('collector_number', '')
        rarity = self.card_data.get('rarity', '')
        
        if set_name:
            ttk.Label(set_frame, text=f"Set: {set_name} ({set_code.upper()})", 
                     font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))
        elif set_code:
            ttk.Label(set_frame, text=f"Set: {set_code.upper()}", 
                     font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))
        
        if collector_number:
            ttk.Label(set_frame, text=f"Collector Number: #{collector_number}").pack(anchor=tk.W, padx=10, pady=2)
        
        if rarity:
            ttk.Label(set_frame, text=f"Rarity: {rarity.title()}").pack(anchor=tk.W, padx=10, pady=(2, 10))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_game_info_tab(self, notebook):
        """Create the game information tab."""
        game_frame = ttk.Frame(notebook)
        notebook.add(game_frame, text="Game Info")
        
        # Power/Toughness for creatures
        stats_frame = ttk.LabelFrame(game_frame, text="Creature Stats")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        power = self.card_data.get('power')
        toughness = self.card_data.get('toughness')
        
        if power is not None and toughness is not None:
            ttk.Label(stats_frame, text=f"Power/Toughness: {power}/{toughness}", 
                     font=('TkDefaultFont', 12, 'bold')).pack(padx=10, pady=10)
        else:
            ttk.Label(stats_frame, text="Not a creature card", 
                     foreground='gray').pack(padx=10, pady=10)
        
        # Loyalty for planeswalkers
        loyalty = self.card_data.get('loyalty')
        if loyalty is not None:
            loyalty_frame = ttk.LabelFrame(game_frame, text="Planeswalker")
            loyalty_frame.pack(fill=tk.X, padx=10, pady=10)
            ttk.Label(loyalty_frame, text=f"Starting Loyalty: {loyalty}", 
                     font=('TkDefaultFont', 12, 'bold')).pack(padx=10, pady=10)
        
        # Keywords
        keywords = self.card_data.get('keywords', [])
        if keywords:
            keywords_frame = ttk.LabelFrame(game_frame, text="Keywords")
            keywords_frame.pack(fill=tk.X, padx=10, pady=10)
            
            keywords_text = ', '.join(keywords) if isinstance(keywords, list) else str(keywords)
            ttk.Label(keywords_frame, text=keywords_text).pack(padx=10, pady=10)
        
        # Legalities
        legalities = self.card_data.get('legalities', {})
        if legalities:
            legal_frame = ttk.LabelFrame(game_frame, text="Format Legality")
            legal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create treeview for legalities
            legal_tree = ttk.Treeview(legal_frame, columns=('status',), show='tree headings', height=8)
            legal_tree.heading('#0', text='Format')
            legal_tree.heading('status', text='Legality')
            
            legal_tree.column('#0', width=150)
            legal_tree.column('status', width=100)
            
            for format_name, legality in legalities.items():
                legal_tree.insert('', tk.END, text=format_name.title(), values=(legality.title(),))
            
            legal_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_collection_info_tab(self, notebook):
        """Create the collection information tab."""
        collection_frame = ttk.Frame(notebook)
        notebook.add(collection_frame, text="Collection")
        
        # Inventory status
        inventory_frame = ttk.LabelFrame(collection_frame, text="In Your Collection")
        inventory_frame.pack(fill=tk.X, padx=10, pady=10)
        
        try:
            # Check if card is in inventory
            card_name = self.card_data.get('name', '')
            inventory_items = []
            
            if card_name:
                # Search for this card in current collection
                all_inventory = self.app.inventory_manager.get_inventory(
                    self.app.current_collection_id, {'name': card_name}
                )
                inventory_items = [item for item in all_inventory if item['name'].lower() == card_name.lower()]
            
            if inventory_items:
                total_quantity = sum(item['quantity'] for item in inventory_items)
                ttk.Label(inventory_frame, text=f"Total Owned: {total_quantity}", 
                         font=('TkDefaultFont', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
                
                # Show breakdown by condition/foil
                for item in inventory_items:
                    foil_text = "Foil" if item['foil'] else "Non-Foil"
                    item_text = f"{item['quantity']}x {foil_text} ({item['condition']})"
                    ttk.Label(inventory_frame, text=f"  • {item_text}").pack(anchor=tk.W, padx=20, pady=1)
                
                # Add spacer
                ttk.Label(inventory_frame, text="").pack(pady=(5, 10))
            else:
                ttk.Label(inventory_frame, text="Not in your collection", 
                         foreground='gray').pack(padx=10, pady=10)
        
        except Exception as e:
            ttk.Label(inventory_frame, text=f"Error checking collection: {e}", 
                     foreground='red').pack(padx=10, pady=10)
        
        # Deck usage
        deck_frame = ttk.LabelFrame(collection_frame, text="Used in Decks")
        deck_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            # Check if card is in any decks
            # This would require querying the deck_cards table
            decks_with_card = self.get_decks_containing_card(card_name)
            
            if decks_with_card:
                for deck_info in decks_with_card:
                    deck_text = f"{deck_info['deck_name']}: {deck_info['quantity']}x"
                    if deck_info['is_commander']:
                        deck_text += " (Commander)"
                    elif deck_info['is_sideboard']:
                        deck_text += " (Sideboard)"
                    
                    ttk.Label(deck_frame, text=f"  • {deck_text}").pack(anchor=tk.W, padx=10, pady=2)
            else:
                ttk.Label(deck_frame, text="Not used in any decks", 
                         foreground='gray').pack(padx=10, pady=10)
        
        except Exception as e:
            ttk.Label(deck_frame, text=f"Error checking decks: {e}", 
                     foreground='red').pack(padx=10, pady=10)
    
    def get_decks_containing_card(self, card_name: str) -> list:
        """Get list of decks that contain this card."""
        try:
            # Query to find decks containing this card
            query = """
                SELECT d.name as deck_name, dc.quantity, dc.is_commander, dc.is_sideboard
                FROM deck_cards dc
                JOIN decks d ON dc.deck_id = d.id
                JOIN cards c ON dc.card_id = c.id
                WHERE c.name = ? AND d.collection_id = ?
            """
            
            rows = self.app.db_manager.execute_query(query, (card_name, self.app.current_collection_id))
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.app.logger.error(f"Failed to get decks containing card: {e}")
            return []