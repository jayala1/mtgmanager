# frontend/views/deck_view.py
"""
Deck view for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, List

class DeckView:
    """Deck management view."""
    
    def __init__(self, parent, app):
        """Initialize deck view."""
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        self.current_deck_id = None
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Set up the deck view UI."""
        # Create paned window for deck list and deck contents
        self.paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Deck list
        self.create_deck_list_panel()
        
        # Right panel - Deck contents
        self.create_deck_contents_panel()
    
    def create_deck_list_panel(self):
        """Create the deck list panel."""
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=1)
        
        # Deck list header
        header_frame = ttk.Frame(left_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header_frame, text="Decks", font=('TkDefaultFont', 12, 'bold')).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="New Deck", command=self.new_deck).pack(side=tk.RIGHT)
        
        # Deck list
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.deck_listbox = tk.Listbox(list_frame)
        deck_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.deck_listbox.yview)
        self.deck_listbox.configure(yscrollcommand=deck_scrollbar.set)
        
        self.deck_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        deck_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.deck_listbox.bind('<<ListboxSelect>>', self.on_deck_select)
        self.deck_listbox.bind('<Double-1>', self.rename_deck)
        
        # Deck actions
        actions_frame = ttk.Frame(left_frame)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Rename", command=self.rename_deck).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Copy", command=self.copy_deck).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Delete", command=self.delete_deck).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Export", command=self.export_deck).pack(side=tk.LEFT, padx=2)
    
    def create_deck_contents_panel(self):
        """Create the deck contents panel."""
        right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(right_frame, weight=2)
        
        # Deck info header
        self.deck_info_frame = ttk.LabelFrame(right_frame, text="Deck Information")
        self.deck_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.deck_info_label = ttk.Label(self.deck_info_frame, text="Select a deck to view details")
        self.deck_info_label.pack(padx=10, pady=5)
        
        # ENHANCED: Add deck tools toolbar
        tools_frame = ttk.Frame(right_frame)
        tools_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Sort options
        ttk.Label(tools_frame, text="Sort by:").pack(side=tk.LEFT, padx=(0, 5))
        self.sort_var = tk.StringVar(value="name")
        sort_combo = ttk.Combobox(tools_frame, textvariable=self.sort_var,
                                  values=["name", "cmc", "type", "color"], 
                                  state="readonly", width=10)
        sort_combo.pack(side=tk.LEFT, padx=(0, 10))
        sort_combo.bind('<<ComboboxSelected>>', self.on_sort_change)
        
        # Filter by card name
        ttk.Label(tools_frame, text="Filter:").pack(side=tk.LEFT, padx=(10, 5))
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(tools_frame, textvariable=self.filter_var, width=15)
        filter_entry.pack(side=tk.LEFT, padx=(0, 5))
        filter_entry.bind('<KeyRelease>', self.on_filter_change)
        
        # Clear filter button
        ttk.Button(tools_frame, text="Clear", command=self.clear_filter).pack(side=tk.LEFT, padx=5)
        
        # Deck statistics button
        ttk.Button(tools_frame, text="Statistics", command=self.show_deck_statistics).pack(side=tk.RIGHT, padx=5)
        
        # Notebook for different card sections
        self.deck_notebook = ttk.Notebook(right_frame)
        self.deck_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Main deck tab
        self.main_frame = ttk.Frame(self.deck_notebook)
        self.deck_notebook.add(self.main_frame, text="Main Deck")
        self.create_enhanced_card_list(self.main_frame, "main")
        
        # Commander tab
        self.commander_frame = ttk.Frame(self.deck_notebook)
        self.deck_notebook.add(self.commander_frame, text="Commander")
        self.create_enhanced_card_list(self.commander_frame, "commander")
        
        # Sideboard tab
        self.sideboard_frame = ttk.Frame(self.deck_notebook)
        self.deck_notebook.add(self.sideboard_frame, text="Sideboard")
        self.create_enhanced_card_list(self.sideboard_frame, "sideboard")
        
        # Add card frame
        add_card_frame = ttk.Frame(right_frame)
        add_card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(add_card_frame, text="Add Card:").pack(side=tk.LEFT, padx=5)
        
        self.add_card_var = tk.StringVar()
        add_card_entry = ttk.Entry(add_card_frame, textvariable=self.add_card_var, width=30)
        add_card_entry.pack(side=tk.LEFT, padx=5)
        add_card_entry.bind('<Return>', self.add_card_to_deck)
        
        ttk.Button(add_card_frame, text="Add to Main", 
                   command=lambda: self.add_card_to_deck(section="main")).pack(side=tk.LEFT, padx=2)
        ttk.Button(add_card_frame, text="Add to Commander", 
                   command=lambda: self.add_card_to_deck(section="commander")).pack(side=tk.LEFT, padx=2)
        ttk.Button(add_card_frame, text="Add to Sideboard", 
                   command=lambda: self.add_card_to_deck(section="sideboard")).pack(side=tk.LEFT, padx=2)
    
    def create_card_list(self, parent, section):
        """DEPRECATED: Create a card list for a deck section. Replaced by create_enhanced_card_list."""
        # This method is being replaced by create_enhanced_card_list
        pass 

    def create_enhanced_card_list(self, parent, section):
        """Create an enhanced card list for a deck section."""
        # Create tree for this section
        tree = ttk.Treeview(parent, columns=('quantity', 'mana_cost', 'type', 'cmc'), show='tree headings')
        
        # Configure columns
        tree.heading('#0', text='Card Name')
        tree.heading('quantity', text='Qty')
        tree.heading('mana_cost', text='Cost')
        tree.heading('type', text='Type')
        tree.heading('cmc', text='CMC')
        
        # Configure column widths
        tree.column('#0', width=200)
        tree.column('quantity', width=50)
        tree.column('mana_cost', width=80)
        tree.column('type', width=150)
        tree.column('cmc', width=50)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store reference
        setattr(self, f"{section}_tree", tree)
        
        # Enhanced context menu
        self.create_enhanced_context_menu(tree, section)
        
        # Bind events
        tree.bind('<Double-1>', lambda e: self.edit_card_quantity(section))
        tree.bind('<Delete>', lambda e: self.remove_card_from_deck(section))
        tree.bind('<Button-3>', lambda e: self.show_enhanced_context_menu(e, section))

    def create_enhanced_context_menu(self, tree, section):
        """Create enhanced context menu for deck cards."""
        context_menu = tk.Menu(self.frame, tearoff=0)
        
        context_menu.add_command(label="Edit Quantity", 
                                  command=lambda: self.edit_card_quantity(section))
        context_menu.add_command(label="Move to Other Section", 
                                  command=lambda: self.move_card_between_sections(section))
        context_menu.add_separator()
        context_menu.add_command(label="Remove from Deck", 
                                  command=lambda: self.remove_card_from_deck(section))
        context_menu.add_separator()
        context_menu.add_command(label="View Card Details", 
                                  command=lambda: self.view_deck_card_details(section))
        
        # Store reference to context menu
        setattr(self, f"{section}_context_menu", context_menu)

    def show_enhanced_context_menu(self, event, section):
        """Show enhanced context menu."""
        tree = getattr(self, f"{section}_tree")
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu = getattr(self, f"{section}_context_menu")
            context_menu.post(event.x_root, event.y_root)

    def move_card_between_sections(self, current_section):
        """Move a card between deck sections."""
        tree = getattr(self, f"{current_section}_tree")
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("Warning", "Please select a card to move.")
            return
        
        item = selection[0]
        deck_card_id = int(tree.item(item)['tags'][0])
        
        # Get card data
        card_data = self.app.deck_builder.get_deck_card_by_id(deck_card_id)
        
        if not card_data:
            messagebox.showerror("Error", "Could not load card data.")
            return
        
        # Define callback function
        def move_callback(move_data: dict) -> bool:
            try:
                # Handle partial vs full move
                move_quantity = move_data['move_quantity']
                total_quantity = move_data['total_quantity']
                target_section = move_data['target_section']
                
                if move_quantity == total_quantity:
                    # Move entire card
                    is_commander = (target_section == "commander")
                    is_sideboard = (target_section == "sideboard")
                    
                    success = self.app.deck_builder.update_deck_card(
                        deck_card_id, None, is_commander, is_sideboard
                    )
                else:
                    # Partial move - reduce current and add new
                    remaining_quantity = total_quantity - move_quantity
                    
                    # Update current card quantity
                    self.app.deck_builder.update_deck_card(
                        deck_card_id, remaining_quantity, None, None
                    )
                    
                    # Add new card in target section
                    is_commander = (target_section == "commander")
                    is_sideboard = (target_section == "sideboard")
                    
                    success = self.app.deck_builder.add_card_to_deck(
                        self.current_deck_id, card_data['name'], 
                        move_quantity, is_commander, is_sideboard
                    )
                
                if success:
                    self.refresh_deck_contents()
                    section_name = self.format_section_name(target_section)
                    self.app.update_status(f"Moved {move_quantity}x {card_data['name']} to {section_name}")
                
                return success
                
            except Exception as e:
                self.app.logger.error(f"Failed to move card: {e}")
                return False
        
        # Show move dialog
        from frontend.dialogs.move_card_dialog import MoveCardDialog
        dialog = MoveCardDialog(self.app.root, card_data, current_section, move_callback)
        result = dialog.show()
        
        if result == 'moved':
            self.app.logger.info(f"Card moved between sections successfully")

    def format_section_name(self, section: str) -> str:
        """Format section name for display."""
        if section == "main":
            return "Main Deck"
        elif section == "sideboard":
            return "Sideboard"
        elif section == "commander":
            return "Commander"
        else:
            return section.title()

    def on_sort_change(self, event=None):
        """Handle sort option change."""
        if self.current_deck_id:
            self.refresh_deck_contents()

    def on_filter_change(self, event=None):
        """Handle filter change."""
        if self.current_deck_id:
            self.refresh_deck_contents()

    def clear_filter(self):
        """Clear the card filter."""
        self.filter_var.set("")
        if self.current_deck_id:
            self.refresh_deck_contents()

    def apply_sort_and_filter(self, cards):
        """Apply sorting and filtering to card list."""
        # Apply filter
        filter_text = self.filter_var.get().lower()
        if filter_text:
            cards = [card for card in cards if filter_text in card['name'].lower()]
        
        # Apply sort
        sort_by = self.sort_var.get()
        if sort_by == "name":
            cards.sort(key=lambda x: x['name'].lower())
        elif sort_by == "cmc":
            cards.sort(key=lambda x: x.get('cmc', 0))
        elif sort_by == "type":
            cards.sort(key=lambda x: x.get('type_line', '').lower())
        elif sort_by == "color":
            cards.sort(key=lambda x: x.get('colors', ''))
        
        return cards
    
    def refresh(self):
        """Refresh the deck list and current deck contents."""
        self.refresh_deck_list()
        if self.current_deck_id:
            self.refresh_deck_contents()
    
    def refresh_deck_list(self):
        """Refresh the deck list."""
        self.deck_listbox.delete(0, tk.END)
        
        try:
            decks = self.app.deck_builder.get_decks(self.app.current_collection_id)
            
            for deck in decks:
                display_text = f"{deck['name']} ({deck['format'] or 'No Format'})"
                if deck['is_commander']:
                    display_text += " [Commander]"
                
                self.deck_listbox.insert(tk.END, display_text)
                # Store deck ID as a tag (we'll need to track this separately)
            
            # Store deck data for reference
            self.deck_data = decks
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load decks: {e}")
    
    def refresh_deck_contents(self):
        """Refresh the contents of the current deck with sorting and filtering."""
        if not self.current_deck_id:
            return
        
        try:
            # Get deck cards
            deck_cards = self.app.deck_builder.get_deck_cards(self.current_deck_id)
            
            # Clear existing trees
            for section in ['main', 'commander', 'sideboard']:
                tree = getattr(self, f"{section}_tree")
                for item in tree.get_children():
                    tree.delete(item)
            
            # Populate trees with sorting and filtering
            for section, cards in deck_cards.items():
                tree = getattr(self, f"{section}_tree")
                
                # Apply sort and filter
                sorted_filtered_cards = self.apply_sort_and_filter(cards)
                
                for card in sorted_filtered_cards:
                    tree.insert('', tk.END,
                        text=card['name'],
                        values=(
                            card['quantity'],
                            card['mana_cost'] or '',
                            card['type_line'] or '',
                            card['cmc'] or 0
                        ),
                        tags=(str(card['id']),)
                    )
            
            # Update deck info
            self.update_deck_info()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load deck contents: {e}")
    
    def update_deck_info(self):
        """Update deck information display."""
        if not self.current_deck_id:
            return
        
        try:
            # Get deck stats
            stats = self.app.deck_builder.get_deck_stats(self.current_deck_id)
            
            # Find current deck info
            current_deck = None
            for deck in self.deck_data:
                if deck['id'] == self.current_deck_id:
                    current_deck = deck
                    break
            
            if current_deck:
                info_text = (f"Name: {current_deck['name']} | "
                             f"Format: {current_deck['format'] or 'None'} | "
                             f"Total Cards: {stats['total_cards']} | "
                             f"Main Deck: {stats['main_deck_count']} | "
                             f"Avg CMC: {stats['avg_cmc']:.1f}")
                
                self.deck_info_label.config(text=info_text)
                self.deck_info_frame.config(text=f"Deck: {current_deck['name']}")
            
        except Exception as e:
            self.app.logger.error(f"Failed to update deck info: {e}")
    
    def on_deck_select(self, event=None):
        """Handle deck selection."""
        selection = self.deck_listbox.curselection()
        if selection:
            deck_index = selection[0]
            if deck_index < len(self.deck_data):
                self.current_deck_id = self.deck_data[deck_index]['id']
                self.refresh_deck_contents()
    
    def new_deck(self):
        """Create a new deck."""
        self.app.quick_new_deck()
    
    def rename_deck(self, event=None):
        """Rename the selected deck."""
        if not self.current_deck_id:
            messagebox.showwarning("Warning", "Please select a deck to rename.")
            return
        
        # Get current deck data
        deck_data = self.app.deck_builder.get_deck_by_id(self.current_deck_id)
        
        if not deck_data:
            messagebox.showerror("Error", "Could not load deck data.")
            return
        
        # Define callback function
        def rename_callback(new_name: str) -> bool:
            try:
                success = self.app.deck_builder.rename_deck(self.current_deck_id, new_name)
                if success:
                    self.refresh_deck_list()
                    self.update_deck_info()
                    self.app.update_status(f"Renamed deck to '{new_name}'")
                return success
            except Exception as e:
                self.app.logger.error(f"Failed to rename deck: {e}")
                return False
        
        # Show rename dialog
        from frontend.dialogs.deck_dialogs import RenameDeckDialog
        dialog = RenameDeckDialog(self.app.root, deck_data, rename_callback)
        result, new_name = dialog.show()
        
        if result == 'renamed':
            self.app.logger.info(f"Deck renamed to '{new_name}'")
    
    def copy_deck(self):
        """Copy the selected deck."""
        if not self.current_deck_id:
            messagebox.showwarning("Warning", "Please select a deck to copy.")
            return
        
        # Get current deck data
        deck_data = self.app.deck_builder.get_deck_by_id(self.current_deck_id)
        
        if not deck_data:
            messagebox.showerror("Error", "Could not load deck data.")
            return
        
        # Define callback function
        def copy_callback(copy_options: Dict[str, Any]) -> bool:
            try:
                new_deck_id = self.app.deck_builder.copy_deck(
                    self.current_deck_id, 
                    copy_options['name'],
                    copy_options
                )
                
                if new_deck_id:
                    self.refresh_deck_list()
                    # Select the new deck
                    for i, deck in enumerate(self.deck_data):
                        if deck['id'] == new_deck_id:
                            self.deck_listbox.selection_clear(0, tk.END)
                            self.deck_listbox.selection_set(i)
                            self.current_deck_id = new_deck_id
                            self.refresh_deck_contents()
                            break
                    
                    self.app.update_status(f"Copied deck to '{copy_options['name']}'")
                    return True
                return False
            except Exception as e:
                self.app.logger.error(f"Failed to copy deck: {e}")
                return False
        
        # Show copy dialog
        from frontend.dialogs.deck_dialogs import CopyDeckDialog
        dialog = CopyDeckDialog(self.app.root, deck_data, copy_callback)
        result, new_name = dialog.show()
        
        if result == 'copied':
            self.app.logger.info(f"Deck copied to '{new_name}'")
    
    def delete_deck(self):
        """Delete the selected deck."""
        if not self.current_deck_id:
            messagebox.showwarning("Warning", "Please select a deck to delete.")
            return
        
        # Get current deck data and stats
        deck_data = self.app.deck_builder.get_deck_by_id(self.current_deck_id)
        deck_stats = self.app.deck_builder.get_deck_stats(self.current_deck_id)
        
        if not deck_data:
            messagebox.showerror("Error", "Could not load deck data.")
            return
        
        # Define callback function
        def delete_callback() -> bool:
            try:
                success = self.app.deck_builder.delete_deck(self.current_deck_id)
                if success:
                    # Clear current selection
                    self.current_deck_id = None
                    
                    # Refresh deck list
                    self.refresh_deck_list()
                    
                    # Clear deck contents
                    for section in ['main', 'commander', 'sideboard']:
                        tree = getattr(self, f"{section}_tree")
                        for item in tree.get_children():
                            tree.delete(item)
                    
                    # Update UI
                    self.deck_info_label.config(text="Select a deck to view details")
                    self.deck_info_frame.config(text="Deck Information")
                    
                    self.app.update_status(f"Deleted deck '{deck_data['name']}'")
                return success
            except Exception as e:
                self.app.logger.error(f"Failed to delete deck: {e}")
                return False
        
        # Show delete confirmation dialog
        from frontend.dialogs.deck_dialogs import DeleteDeckDialog
        dialog = DeleteDeckDialog(self.app.root, deck_data, deck_stats, delete_callback)
        result = dialog.show()
        
        if result == 'deleted':
            self.app.logger.info(f"Deck '{deck_data['name']}' deleted")
    
    def export_deck(self):
        """Export the selected deck."""
        if not self.current_deck_id:
            messagebox.showwarning("Warning", "Please select a deck to export.")
            return
        
        # Find current deck name for default filename
        current_deck_name = "deck"
        for deck in self.deck_data:
            if deck['id'] == self.current_deck_id:
                current_deck_name = deck['name'].replace(' ', '_')
                break
        
        file_path = filedialog.asksaveasfilename(
            title="Export Deck",
            defaultextension=".txt",
            initialvalue=f"{current_deck_name}.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                deck_text = self.app.deck_builder.export_deck_to_text(self.current_deck_id)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(deck_text)
                
                messagebox.showinfo("Success", f"Deck exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export deck: {e}")
    
    def add_card_to_deck(self, event=None, section="main"):
        """Add a card to the current deck."""
        if not self.current_deck_id:
            messagebox.showwarning("Warning", "Please select a deck first.")
            return
        
        card_name = self.add_card_var.get().strip()
        if not card_name:
            messagebox.showwarning("Warning", "Please enter a card name.")
            return
        
        try:
            is_commander = (section == "commander")
            is_sideboard = (section == "sideboard")
            
            success = self.app.deck_builder.add_card_to_deck(
                self.current_deck_id, card_name, 1, is_commander, is_sideboard
            )
            
            if success:
                self.add_card_var.set("")
                self.refresh_deck_contents()
                self.app.update_status(f"Added {card_name} to {section}")
            else:
                messagebox.showerror("Error", f"Card '{card_name}' not found")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add card: {e}")
    
    def edit_card_quantity(self, section):
        """Edit the quantity of a card in the deck."""
        tree = getattr(self, f"{section}_tree")
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("Warning", "Please select a card to edit.")
            return
        
        item = selection[0]
        deck_card_id = int(tree.item(item)['tags'][0])
        
        # Get full card data
        card_data = self.app.deck_builder.get_deck_card_by_id(deck_card_id)
        
        if not card_data:
            messagebox.showerror("Error", "Could not load card data.")
            return
        
        # Define callback function for saving changes
        def save_callback(updated_data: dict) -> bool:
            try:
                if updated_data.get('action') == 'remove':
                    # Remove the card
                    success = self.app.deck_builder.remove_card_from_deck(updated_data['id'])
                    if success:
                        self.refresh_deck_contents()
                        self.app.update_status(f"Removed '{card_data['name']}' from deck")
                    return success
                else:
                    # Update the card
                    success = self.app.deck_builder.update_deck_card(
                        updated_data['id'],
                        updated_data.get('quantity'),
                        updated_data.get('is_commander'),
                        updated_data.get('is_sideboard')
                    )
                    if success:
                        self.refresh_deck_contents()
                        self.app.update_status(f"Updated '{card_data['name']}' in deck")
                    return success
            except Exception as e:
                self.app.logger.error(f"Failed to save deck card changes: {e}")
                return False
        
        # Show edit dialog
        from frontend.dialogs.edit_dialogs import EditDeckCardDialog
        deck_sections = ["Main Deck", "Commander", "Sideboard"]
        dialog = EditDeckCardDialog(self.app.root, card_data, deck_sections, save_callback)
        result = dialog.show()
        
        # Handle result if needed
        if result in ['saved', 'removed']:
            self.app.logger.info(f"Deck card {result}")
    
    def remove_card_from_deck(self, section):
        """Remove a card from the deck."""
        tree = getattr(self, f"{section}_tree")
        selection = tree.selection()
        
        if not selection:
            return
        
        item = selection[0]
        card_name = tree.item(item)['text']
        deck_card_id = int(tree.item(item)['tags'][0])
        
        result = messagebox.askyesno(
            "Confirm Removal",
            f"Remove '{card_name}' from deck?"
        )
        
        if result:
            try:
                success = self.app.deck_builder.remove_card_from_deck(deck_card_id)
                if success:
                    self.refresh_deck_contents()
                    self.app.update_status(f"Removed {card_name} from deck")
                else:
                    messagebox.showerror("Error", "Failed to remove card")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove card: {e}")

    def show_deck_statistics(self):
        """Show comprehensive deck statistics."""
        if not self.current_deck_id:
            messagebox.showwarning("Warning", "Please select a deck first.")
            return
        
        try:
            # Get deck cards and stats
            deck_cards = self.app.deck_builder.get_deck_cards(self.current_deck_id)
            basic_stats = self.app.deck_builder.get_deck_stats(self.current_deck_id)
            
            # Calculate advanced statistics
            all_cards = deck_cards['main'] + deck_cards['commander'] + deck_cards['sideboard']
            
            # Mana curve
            mana_curve = {}
            for card in all_cards:
                cmc = card.get('cmc', 0)
                mana_curve[cmc] = mana_curve.get(cmc, 0) + card['quantity']
            
            # Color distribution
            color_counts = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'Colorless': 0}
            for card in all_cards:
                colors = card.get('colors', '')
                if colors:
                    for color in colors.split(','):
                        color = color.strip()
                        if color in color_counts:
                            color_counts[color] += card['quantity']
                else:
                    color_counts['Colorless'] += card['quantity']
            
            # Type distribution
            type_counts = {}
            for card in all_cards:
                type_line = card.get('type_line', '')
                if type_line:
                    # Get primary type
                    primary_type = type_line.split(' ')[0] if type_line else 'Unknown'
                    type_counts[primary_type] = type_counts.get(primary_type, 0) + card['quantity']
            
            # Show statistics dialog
            self.show_statistics_dialog(basic_stats, mana_curve, color_counts, type_counts)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate statistics: {e}")

    def show_statistics_dialog(self, basic_stats, mana_curve, color_counts, type_counts):
        """Show deck statistics in a dialog."""
        stats_dialog = tk.Toplevel(self.app.root)
        stats_dialog.title("Deck Statistics")
        stats_dialog.geometry("500x600")
        stats_dialog.transient(self.app.root)
        stats_dialog.grab_set()
        
        # Center the dialog
        stats_dialog.update_idletasks()
        x = (stats_dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (stats_dialog.winfo_screenheight() // 2) - (600 // 2)
        stats_dialog.geometry(f"500x600+{x}+{y}")
        
        # Create notebook for different stat categories
        notebook = ttk.Notebook(stats_dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic stats tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Stats")
        
        basic_text = f"""Total Cards: {basic_stats['total_cards']}
Unique Cards: {basic_stats['unique_cards']}
Main Deck: {basic_stats['main_deck_count']}
Average CMC: {basic_stats['avg_cmc']:.2f}"""
        
        ttk.Label(basic_frame, text=basic_text, justify=tk.LEFT, font=('TkDefaultFont', 11)).pack(padx=20, pady=20)
        
        # Mana curve tab
        curve_frame = ttk.Frame(notebook)
        notebook.add(curve_frame, text="Mana Curve")
        
        curve_text = "Mana Curve:\n\n"
        for cmc in sorted(mana_curve.keys()):
            curve_text += f"CMC {cmc}: {mana_curve[cmc]} cards\n"
        
        ttk.Label(curve_frame, text=curve_text, justify=tk.LEFT, font=('TkDefaultFont', 10)).pack(padx=20, pady=20)
        
        # Color distribution tab
        color_frame = ttk.Frame(notebook)
        notebook.add(color_frame, text="Colors")
        
        color_text = "Color Distribution:\n\n"
        for color, count in color_counts.items():
            if count > 0:
                color_text += f"{color}: {count} cards\n"
        
        ttk.Label(color_frame, text=color_text, justify=tk.LEFT, font=('TkDefaultFont', 10)).pack(padx=20, pady=20)
        
        # Type distribution tab
        type_frame = ttk.Frame(notebook)
        notebook.add(type_frame, text="Types")
        
        type_text = "Type Distribution:\n\n"
        for card_type, count in sorted(type_counts.items()):
            type_text += f"{card_type}: {count} cards\n"
        
        ttk.Label(type_frame, text=type_text, justify=tk.LEFT, font=('TkDefaultFont', 10)).pack(padx=20, pady=20)
        
        # Close button
        ttk.Button(stats_dialog, text="Close", command=stats_dialog.destroy).pack(pady=10)
        
        # Bind escape key
        stats_dialog.bind('<Escape>', lambda e: stats_dialog.destroy())

    def view_deck_card_details(self, section):
        """View details for a card in the deck."""
        tree = getattr(self, f"{section}_tree")
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("Warning", "Please select a card to view details.")
            return
        
        item = selection[0]
        deck_card_id = int(tree.item(item)['tags'][0])
        
        # Get card data
        card_data = self.app.deck_builder.get_deck_card_by_id(deck_card_id)
        
        if not card_data:
            messagebox.showerror("Error", "Could not load card data.")
            return
        
        # Try to get enhanced data from Scryfall cache
        card_name = card_data.get('name', '')
        enhanced_card_data = card_data.copy()
        
        if card_name:
            scryfall_data = self.app.scryfall_client.search_card_in_cache(card_name)
            if scryfall_data:
                enhanced_card_data.update(scryfall_data)
        
        # Show card details dialog
        from frontend.dialogs.card_details_dialog import CardDetailsDialog
        dialog = CardDetailsDialog(self.app.root, enhanced_card_data, self.app)