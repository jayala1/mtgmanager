# frontend/views/inventory_view.py
"""
Inventory view for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List

class InventoryView:
    """Inventory management view."""
    
    def __init__(self, parent, app):
        """Initialize inventory view."""
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Set up the inventory view UI."""
        # Search and filter frame
        filter_frame = ttk.LabelFrame(self.frame, text="Search & Filters")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search by name
        ttk.Label(filter_frame, text="Card Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_filter_var = tk.StringVar()
        self.name_filter_entry = ttk.Entry(filter_frame, textvariable=self.name_filter_var, width=20)
        self.name_filter_entry.grid(row=0, column=1, padx=5, pady=5)
        self.name_filter_entry.bind('<KeyRelease>', self.on_filter_change)
        
        # Set filter
        ttk.Label(filter_frame, text="Set:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.set_filter_var = tk.StringVar()
        self.set_filter_combo = ttk.Combobox(filter_frame, textvariable=self.set_filter_var, width=15)
        self.set_filter_combo.grid(row=0, column=3, padx=5, pady=5)
        self.set_filter_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Foil filter
        self.foil_filter_var = tk.StringVar(value="All")
        foil_frame = ttk.Frame(filter_frame)
        foil_frame.grid(row=0, column=4, padx=5, pady=5)
        ttk.Label(foil_frame, text="Foil:").pack(side=tk.LEFT)
        foil_combo = ttk.Combobox(foil_frame, textvariable=self.foil_filter_var, 
                                 values=["All", "Foil Only", "Non-Foil Only"], 
                                 state="readonly", width=12)
        foil_combo.pack(side=tk.LEFT, padx=(5, 0))
        foil_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Clear filters button
        ttk.Button(filter_frame, text="Clear Filters", 
                   command=self.clear_filters).grid(row=0, column=5, padx=10, pady=5)
        
        # Inventory tree
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame, columns=(
            'quantity', 'foil', 'condition', 'set', 'collector_number', 'mana_cost', 'type'
        ), show='tree headings')
        
        # Configure columns
        self.tree.heading('#0', text='Card Name')
        self.tree.heading('quantity', text='Qty')
        self.tree.heading('foil', text='Foil')
        self.tree.heading('condition', text='Condition')
        self.tree.heading('set', text='Set')
        self.tree.heading('collector_number', text='#')
        self.tree.heading('mana_cost', text='Cost')
        self.tree.heading('type', text='Type')
        
        # Configure column widths
        self.tree.column('#0', width=200)
        self.tree.column('quantity', width=50)
        self.tree.column('foil', width=50)
        self.tree.column('condition', width=100)
        self.tree.column('set', width=60)
        self.tree.column('collector_number', width=40)
        self.tree.column('mana_cost', width=80)
        self.tree.column('type', width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.create_context_menu()
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<Double-1>', self.edit_item)
        
        # Action buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Add Card", command=self.add_card).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit", command=self.edit_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove", command=self.remove_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.refresh).pack(side=tk.RIGHT, padx=5)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(self.frame, text="Collection Stats")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="")
        self.stats_label.pack(padx=10, pady=5)
    
    def create_context_menu(self):
        """Create context menu for tree items."""
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_item)
        self.context_menu.add_command(label="Remove (Double Confirm)", command=self.remove_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Add to Deck", command=self.add_to_deck)
        self.context_menu.add_command(label="Trade Card", command=self.trade_card) # NEW
        self.context_menu.add_separator()
        self.context_menu.add_command(label="View Card Details", command=self.view_card_details)
    
    def show_context_menu(self, event):
        """Show context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def refresh(self):
        """Refresh the inventory display."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get current filters
        filters = self.get_current_filters()
        
        # Get inventory data
        try:
            inventory = self.app.inventory_manager.get_inventory(
                self.app.current_collection_id, filters
            )
            
            # Collect image URLs for preloading
            image_urls = []
            
            # Populate tree
            for item in inventory:
                foil_text = "Yes" if item['foil'] else "No"
                
                self.tree.insert('', tk.END, 
                    text=item['name'],
                    values=(
                        item['quantity'],
                        foil_text,
                        item['condition'],
                        item['set_code'] or '',
                        item['collector_number'] or '',
                        item['mana_cost'] or '',
                        item['type_line'] or ''
                    ),
                    tags=(str(item['id']),)
                )
                
                # DEBUG: Check what image URL we have
                if item.get('image_url'):
                    self.app.logger.debug(f"Inventory item '{item['name']}' has image_url: {item['image_url']}")
                    image_urls.append(item['image_url'])
                else:
                    self.app.logger.debug(f"Inventory item '{item['name']}' has NO image_url")
            
            # Start preloading images in background
            if image_urls:
                self.app.logger.debug(f"Starting preload of {len(image_urls)} images")
                self.app.image_manager.preload_images(image_urls, 'thumbnail')
            else:
                self.app.logger.debug("No image URLs found for preloading")
            
            # Update stats
            self.update_stats(inventory)
            
            # Update set filter options
            self.update_set_filter_options(inventory)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load inventory: {e}")
    
    def get_current_filters(self) -> Dict[str, Any]:
        """Get current filter values."""
        filters = {}
        
        if self.name_filter_var.get().strip():
            filters['name'] = self.name_filter_var.get().strip()
        
        if self.set_filter_var.get().strip():
            filters['set_code'] = self.set_filter_var.get().strip()
        
        foil_filter = self.foil_filter_var.get()
        if foil_filter == "Foil Only":
            filters['foil'] = True
        elif foil_filter == "Non-Foil Only":
            filters['foil'] = False
        
        return filters
    
    def on_filter_change(self, event=None):
        """Handle filter changes."""
        self.refresh()
    
    def clear_filters(self):
        """Clear all filters."""
        self.name_filter_var.set("")
        self.set_filter_var.set("")
        self.foil_filter_var.set("All")
        self.refresh()
    
    def update_stats(self, inventory: List[Dict[str, Any]]):
        """Update collection statistics."""
        total_cards = sum(item['quantity'] for item in inventory)
        unique_cards = len(inventory)
        foil_cards = sum(item['quantity'] for item in inventory if item['foil'])
        
        stats_text = f"Total Cards: {total_cards} | Unique Cards: {unique_cards} | Foil Cards: {foil_cards}"
        self.stats_label.config(text=stats_text)
    
    def update_set_filter_options(self, inventory: List[Dict[str, Any]]):
        """Update set filter combo box options."""
        sets = sorted(set(item['set_code'] for item in inventory if item['set_code']))
        current_value = self.set_filter_var.get()
        self.set_filter_combo['values'] = [''] + sets
        
        # Restore selection if still valid
        if current_value in sets:
            self.set_filter_var.set(current_value)
    
    def add_card(self):
        """Open add card dialog."""
        self.app.quick_add_card()
    
    def edit_item(self, event=None):
        """Edit selected inventory item."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to edit.")
            return
        
        item = selection[0]
        item_id = int(self.tree.item(item)['tags'][0])
        
        # Get full item data
        item_data = self.app.inventory_manager.get_inventory_item_by_id(item_id)
        
        if not item_data:
            messagebox.showerror("Error", "Could not load item data.")
            return
        
        # Define callback function for saving changes
        def save_callback(updated_data: dict) -> bool:
            try:
                if updated_data.get('action') == 'delete':
                    # Delete the item
                    success = self.app.inventory_manager.remove_from_inventory(updated_data['id'])
                    if success:
                        self.refresh()
                        self.app.update_status(f"Deleted '{item_data['name']}' from inventory")
                    return success
                else:
                    # Update the item
                    success = self.app.inventory_manager.update_inventory_item_full(
                        updated_data['id'],
                        updated_data.get('quantity'),
                        updated_data.get('foil'),
                        updated_data.get('condition')
                    )
                    if success:
                        self.refresh()
                        self.app.update_status(f"Updated '{item_data['name']}' in inventory")
                    return success
            except Exception as e:
                self.app.logger.error(f"Failed to save inventory changes: {e}")
                return False
        
        # Show edit dialog
        from frontend.dialogs.edit_dialogs import EditInventoryDialog
        dialog = EditInventoryDialog(self.app.root, item_data, save_callback)
        result = dialog.show()
        
        # Handle result if needed
        if result in ['saved', 'deleted']:
            self.app.logger.info(f"Inventory item {result}")
    
    def remove_item(self):
        """Remove selected inventory item with double confirmation."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to remove.")
            return
        
        item = selection[0]
        item_id = int(self.tree.item(item)['tags'][0])
        card_name = self.tree.item(item)['text']
        
        # Get item details for confirmation
        values = self.tree.item(item)['values']
        quantity = values[0] if len(values) > 0 else "Unknown"
        foil_status = values[1] if len(values) > 1 else "Unknown"
        condition = values[2] if len(values) > 2 else "Unknown"
        
        # First confirmation - basic warning
        first_result = messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove this item from your inventory?\n\n"
            f"Card: {card_name}\n"
            f"Quantity: {quantity}\n"
            f"Foil: {foil_status}\n"
            f"Condition: {condition}",
            icon='warning'
        )
        
        if not first_result:
            return
        
        # Second confirmation - stronger warning
        second_result = messagebox.askyesno(
            "Final Confirmation",
            f"⚠️ FINAL WARNING ⚠️\n\n"
            f"This will permanently delete '{card_name}' from your inventory.\n\n"
            f"This action CANNOT be undone!\n\n"
            f"Are you absolutely certain you want to proceed?",
            icon='warning'
        )
        
        if second_result:
            try:
                success = self.app.inventory_manager.remove_from_inventory(item_id)
                if success:
                    self.refresh()
                    self.app.update_status(f"Permanently deleted '{card_name}' from inventory")
                else:
                    messagebox.showerror("Error", "Failed to remove item")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove item: {e}")
    
    def add_to_deck(self):
        """Add selected card to a deck."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a card to add to deck.")
            return
        
        item = selection[0]
        item_id = int(self.tree.item(item)['tags'][0])
        
        # Get full item data
        item_data = self.app.inventory_manager.get_inventory_item_by_id(item_id)
        
        if not item_data:
            messagebox.showerror("Error", "Could not load card data.")
            return
        
        # Get available decks
        try:
            available_decks = self.app.deck_builder.get_decks(self.app.current_collection_id)
            
            if not available_decks:
                result = messagebox.askyesno(
                    "No Decks Found",
                    "You don't have any decks yet. Would you like to create one now?"
                )
                if result:
                    self.app.quick_new_deck()
                return
            
            # Define callback function
            def add_callback(add_data: dict) -> bool:
                try:
                    success = self.app.deck_builder.add_card_to_deck(
                        add_data['deck_id'],
                        add_data['card_name'],
                        add_data['quantity'],
                        add_data['is_commander'],
                        add_data['is_sideboard']
                    )
                    
                    if success:
                        # Find deck name for status message
                        deck_name = "Unknown Deck"
                        for deck in available_decks:
                            if deck['id'] == add_data['deck_id']:
                                deck_name = deck['name']
                                break
                        
                        section = "commander" if add_data['is_commander'] else ("sideboard" if add_data['is_sideboard'] else "main deck")
                        self.app.update_status(f"Added {add_data['quantity']}x {add_data['card_name']} to {deck_name} ({section})")
                        
                        # Refresh deck view if it's visible
                        if hasattr(self.app, 'deck_view'):
                            self.app.deck_view.refresh()
                        
                    return success
                except Exception as e:
                    self.app.logger.error(f"Failed to add card to deck: {e}")
                    return False
            
            # Show add to deck dialog
            from frontend.dialogs.add_to_deck_dialog import AddToDeckDialog
            dialog = AddToDeckDialog(self.app.root, item_data, available_decks, add_callback)
            result = dialog.show()
            
            if result == 'added':
                self.app.logger.info(f"Card added to deck successfully")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add card to deck: {e}")
    
    def view_card_details(self):
        """View detailed information about selected card."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a card to view details.")
            return
        
        item = selection[0]
        item_id = int(self.tree.item(item)['tags'][0])
        
        # Get full item data
        item_data = self.app.inventory_manager.get_inventory_item_by_id(item_id)
        
        if not item_data:
            messagebox.showerror("Error", "Could not load card data.")
            return
        
        # Try to get additional card data from Scryfall cache
        card_name = item_data.get('name', '')
        enhanced_card_data = item_data.copy()
        
        if card_name:
            scryfall_data = self.app.scryfall_client.search_card_in_cache(card_name)
            if scryfall_data:
                # Merge data, preferring Scryfall data for completeness
                enhanced_card_data.update(scryfall_data)
        
        # Show card details dialog
        from frontend.dialogs.card_details_dialog import CardDetailsDialog
        dialog = CardDetailsDialog(self.app.root, enhanced_card_data, self.app)

    def trade_card(self):
        """Start a trade with the selected card."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a card to trade.")
            return
        
        item = selection[0]
        item_id = int(self.tree.item(item)['tags'][0])
        
        # Get full item data
        item_data = self.app.inventory_manager.get_inventory_item_by_id(item_id)
        
        if not item_data:
            messagebox.showerror("Error", "Could not load card data.")
            return
        
        # Open trade dialog with this card pre-selected
        from frontend.dialogs.trade_dialog import TradeDialog
        
        dialog = TradeDialog(self.app.root, self.app, item_data)
        result = dialog.show()
        
        if result == 'recorded':
            self.refresh()  # Refresh inventory after trade
            # Switch to trade tab to show the new trade
            self.app.notebook.select(self.app.trade_view.frame)