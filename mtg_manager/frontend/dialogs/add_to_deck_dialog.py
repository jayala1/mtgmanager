# frontend/dialogs/add_to_deck_dialog.py - Replace the entire file with this corrected version
"""
Add to Deck dialog for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Callable

class AddToDeckDialog:
    """Dialog for adding cards to decks."""
    
    def __init__(self, parent, card_data: Dict[str, Any], available_decks: List[Dict[str, Any]], 
                 callback: Callable[[Dict[str, Any]], bool]):
        """
        Initialize add to deck dialog.
        
        Args:
            parent: Parent window
            card_data: Dictionary containing card data
            available_decks: List of available decks
            callback: Function to call when adding card
        """
        self.parent = parent
        self.card_data = card_data
        self.available_decks = available_decks
        self.callback = callback
        self.result = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the add to deck dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Add to Deck")
        self.dialog.geometry("450x500")  # Made taller for buttons
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"450x500+{x}+{y}")
        
        # Main container - FIXED: Proper container structure
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Card info header
        card_frame = ttk.LabelFrame(main_container, text="Card to Add")
        card_frame.pack(fill=tk.X, pady=(0, 15))
        
        card_name = self.card_data.get('name', 'Unknown Card')
        mana_cost = self.card_data.get('mana_cost', '')
        type_line = self.card_data.get('type_line', '')
        
        ttk.Label(card_frame, text=card_name, font=('TkDefaultFont', 11, 'bold')).pack(padx=10, pady=(10, 2))
        
        if mana_cost:
            ttk.Label(card_frame, text=f"Mana Cost: {mana_cost}", font=('TkDefaultFont', 9)).pack(padx=10, pady=2)
        
        if type_line:
            ttk.Label(card_frame, text=f"Type: {type_line}", font=('TkDefaultFont', 9)).pack(padx=10, pady=(2, 10))
        
        # Check if no decks available
        if not self.available_decks:
            no_decks_frame = ttk.LabelFrame(main_container, text="No Decks Available")
            no_decks_frame.pack(fill=tk.X, pady=(0, 20))
            
            ttk.Label(no_decks_frame, text="No decks available. Create a deck first.", 
                     foreground='red').pack(padx=10, pady=20)
            
            # Just close button for no decks case
            button_frame = ttk.Frame(main_container)
            button_frame.pack(fill=tk.X, side=tk.BOTTOM)
            
            ttk.Button(button_frame, text="Close", command=self.cancel).pack()
            
            self.dialog.update_idletasks()
            return
        
        # Deck selection
        deck_frame = ttk.LabelFrame(main_container, text="Select Deck")
        deck_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Deck selection listbox
        deck_list_frame = ttk.Frame(deck_frame)
        deck_list_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.deck_listbox = tk.Listbox(deck_list_frame, height=6)
        deck_scrollbar = ttk.Scrollbar(deck_list_frame, orient=tk.VERTICAL, command=self.deck_listbox.yview)
        self.deck_listbox.configure(yscrollcommand=deck_scrollbar.set)
        
        # Populate deck list
        for deck in self.available_decks:
            deck_name = deck['name']
            deck_format = deck.get('format', 'No Format')
            is_commander = deck.get('is_commander', False)
            
            display_text = f"{deck_name} ({deck_format})"
            if is_commander:
                display_text += " [Commander]"
            
            self.deck_listbox.insert(tk.END, display_text)
        
        self.deck_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        deck_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Select first deck by default
        if self.available_decks:
            self.deck_listbox.selection_set(0)
            self.deck_listbox.bind('<<ListboxSelect>>', self.on_deck_select)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_container, text="Add Options")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Quantity
        quantity_frame = ttk.Frame(options_frame)
        quantity_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(quantity_frame, text="Quantity:", width=12).pack(side=tk.LEFT)
        self.quantity_var = tk.IntVar(value=1)
        quantity_spin = ttk.Spinbox(quantity_frame, from_=1, to=99, textvariable=self.quantity_var, width=8)
        quantity_spin.pack(side=tk.LEFT, padx=5)
        
        # Section selection
        section_frame = ttk.Frame(options_frame)
        section_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(section_frame, text="Add to:", width=12).pack(side=tk.LEFT)
        
        self.section_var = tk.StringVar(value="Main Deck")
        self.section_combo = ttk.Combobox(section_frame, textvariable=self.section_var,
                                         values=["Main Deck", "Sideboard"], 
                                         state="readonly", width=15)
        self.section_combo.pack(side=tk.LEFT, padx=5)
        
        # Commander option (will be enabled/disabled based on deck selection)
        self.commander_var = tk.BooleanVar()
        self.commander_check = ttk.Checkbutton(section_frame, text="As Commander", 
                                              variable=self.commander_var,
                                              command=self.on_commander_toggle)
        self.commander_check.pack(side=tk.LEFT, padx=10)
        
        # Add some spacing
        ttk.Label(options_frame, text="").pack(pady=(5, 10))
        
        # Update commander option based on initial selection
        self.on_deck_select()
        
        # BUTTONS - FIXED: Proper placement at bottom
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        add_button = ttk.Button(button_frame, text="Add to Deck", command=self.add_to_deck)
        add_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # Bind events
        self.dialog.bind('<Return>', lambda e: self.add_to_deck())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Force update to ensure everything is displayed
        self.dialog.update_idletasks()
    
    def on_deck_select(self, event=None):
        """Handle deck selection change."""
        selection = self.deck_listbox.curselection()
        if selection and self.available_decks:
            deck_index = selection[0]
            if deck_index < len(self.available_decks):
                selected_deck = self.available_decks[deck_index]
                is_commander_deck = selected_deck.get('is_commander', False)
                
                # Enable/disable commander option based on deck type
                if is_commander_deck:
                    self.commander_check.config(state=tk.NORMAL)
                    # Update section options for commander deck
                    self.section_combo['values'] = ["Main Deck", "Sideboard"]
                else:
                    self.commander_check.config(state=tk.DISABLED)
                    self.commander_var.set(False)
                    # Standard deck sections
                    self.section_combo['values'] = ["Main Deck", "Sideboard"]
    
    def on_commander_toggle(self):
        """Handle commander checkbox toggle."""
        if self.commander_var.get():
            # If set as commander, change section to main deck
            self.section_var.set("Main Deck")
            self.section_combo.config(state=tk.DISABLED)
            # Set quantity to 1 for commanders
            self.quantity_var.set(1)
        else:
            self.section_combo.config(state=tk.NORMAL)
    
    def add_to_deck(self):
        """Add the card to the selected deck."""
        selection = self.deck_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Deck Selected", "Please select a deck.")
            return
        
        deck_index = selection[0]
        if deck_index >= len(self.available_decks):
            messagebox.showerror("Error", "Invalid deck selection.")
            return
        
        selected_deck = self.available_decks[deck_index]
        
        # Validate commander selection
        if self.commander_var.get():
            # Check if deck already has a commander
            # This would require a callback to check existing commanders
            pass  # For now, we'll let the backend handle validation
        
        # Prepare add data
        add_data = {
            'deck_id': selected_deck['id'],
            'card_name': self.card_data['name'],
            'quantity': self.quantity_var.get(),
            'is_commander': self.commander_var.get(),
            'is_sideboard': self.section_var.get() == "Sideboard"
        }
        
        try:
            success = self.callback(add_data)
            
            if success:
                self.result = 'added'
                self.dialog.destroy()
            else:
                messagebox.showerror("Add Failed", "Failed to add card to deck.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def cancel(self):
        """Cancel the add operation."""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result