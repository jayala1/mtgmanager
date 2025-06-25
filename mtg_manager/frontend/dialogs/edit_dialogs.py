# frontend/dialogs/edit_dialogs.py
"""
Edit dialogs for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional

class EditInventoryDialog:
    """Dialog for editing inventory items."""
    
    def __init__(self, parent, item_data: Dict[str, Any], callback: Callable[[Dict[str, Any]], bool]):
        """
        Initialize edit inventory dialog.
        
        Args:
            parent: Parent window
            item_data: Dictionary containing current item data
            callback: Function to call when saving changes, returns success boolean
        """
        self.parent = parent
        self.item_data = item_data.copy()  # Make a copy to avoid modifying original
        self.callback = callback
        self.result = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the edit dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Edit Inventory Item")
        self.dialog.geometry("400x450")  # Made taller to ensure buttons fit
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"400x450+{x}+{y}")
        
        # Main container frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Card info header
        header_frame = ttk.LabelFrame(main_frame, text="Card Information")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Card name (read-only)
        ttk.Label(header_frame, text="Card Name:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 2))
        card_name_label = ttk.Label(header_frame, text=self.item_data.get('name', 'Unknown Card'), 
                                     font=('TkDefaultFont', 11))
        card_name_label.pack(anchor=tk.W, padx=20, pady=(0, 5))
        
        # Set and collector number (read-only)
        set_info = f"Set: {self.item_data.get('set_code', 'Unknown')}"
        if self.item_data.get('collector_number'):
            set_info += f" #{self.item_data['collector_number']}"
        ttk.Label(header_frame, text=set_info, font=('TkDefaultFont', 9)).pack(anchor=tk.W, padx=20, pady=(0, 10))
        
        # Editable fields frame
        edit_frame = ttk.LabelFrame(main_frame, text="Edit Properties")
        edit_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Quantity
        quantity_frame = ttk.Frame(edit_frame)
        quantity_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(quantity_frame, text="Quantity:", width=12).pack(side=tk.LEFT)
        self.quantity_var = tk.IntVar(value=self.item_data.get('quantity', 1))
        quantity_spin = ttk.Spinbox(
            quantity_frame, 
            from_=1, 
            to=999, 
            textvariable=self.quantity_var, 
            width=10,
            validate='key',
            validatecommand=(self.dialog.register(self.validate_quantity), '%P')
        )
        quantity_spin.pack(side=tk.LEFT, padx=5)
        
        # Foil status
        foil_frame = ttk.Frame(edit_frame)
        foil_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(foil_frame, text="Foil:", width=12).pack(side=tk.LEFT)
        self.foil_var = tk.BooleanVar(value=self.item_data.get('foil', False))
        foil_check = ttk.Checkbutton(foil_frame, text="This card is foil", variable=self.foil_var)
        foil_check.pack(side=tk.LEFT, padx=5)
        
        # Condition
        condition_frame = ttk.Frame(edit_frame)
        condition_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        ttk.Label(condition_frame, text="Condition:", width=12).pack(side=tk.LEFT)
        self.condition_var = tk.StringVar(value=self.item_data.get('condition', 'Near Mint'))
        condition_combo = ttk.Combobox(
            condition_frame,
            textvariable=self.condition_var,
            values=["Mint", "Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", "Damaged"],
            state="readonly",
            width=20
        )
        condition_combo.pack(side=tk.LEFT, padx=5)
        
        # Notes section (optional enhancement)
        notes_frame = ttk.LabelFrame(main_frame, text="Additional Information")
        notes_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Display card type and mana cost if available
        info_added = False
        if self.item_data.get('type_line'):
            ttk.Label(notes_frame, text=f"Type: {self.item_data['type_line']}", 
                      font=('TkDefaultFont', 8)).pack(anchor=tk.W, padx=10, pady=(10, 2))
            info_added = True
        
        if self.item_data.get('mana_cost'):
            ttk.Label(notes_frame, text=f"Mana Cost: {self.item_data['mana_cost']}", 
                      font=('TkDefaultFont', 8)).pack(anchor=tk.W, padx=10, pady=(2 if info_added else 10, 10))
            info_added = True
        
        if not info_added:
            ttk.Label(notes_frame, text="No additional information available", 
                      font=('TkDefaultFont', 8), foreground='gray').pack(anchor=tk.W, padx=10, pady=10)
        
        # BUTTONS - This is the critical section that was missing proper layout
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)  # Explicitly pack at bottom
        
        # Create buttons with proper spacing
        save_button = ttk.Button(button_frame, text="Save Changes", command=self.save_changes)
        save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Delete button (separate, on the right)
        delete_button = ttk.Button(button_frame, text="Delete Item", command=self.delete_item)
        delete_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Bind events
        self.dialog.bind('<Return>', lambda e: self.save_changes())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Focus on quantity field
        quantity_spin.focus()
        quantity_spin.select_range(0, tk.END)
        
        # Force update to ensure everything is displayed
        self.dialog.update_idletasks()
    
    def validate_quantity(self, value):
        """Validate quantity input."""
        if value == "":
            return True
        try:
            qty = int(value)
            return 1 <= qty <= 999
        except ValueError:
            return False
    
    def save_changes(self):
        """Save the changes."""
        try:
            # Validate quantity
            quantity = self.quantity_var.get()
            if quantity < 1:
                messagebox.showerror("Invalid Quantity", "Quantity must be at least 1.")
                return
            
            # Prepare updated data
            updated_data = {
                'id': self.item_data['id'],
                'quantity': quantity,
                'foil': self.foil_var.get(),
                'condition': self.condition_var.get()
            }
            
            # Check if anything actually changed
            changes_made = (
                updated_data['quantity'] != self.item_data.get('quantity') or
                updated_data['foil'] != self.item_data.get('foil') or
                updated_data['condition'] != self.item_data.get('condition')
            )
            
            if not changes_made:
                self.cancel()  # No changes, just close
                return
            
            # Call the callback function to save changes
            success = self.callback(updated_data)
            
            if success:
                self.result = 'saved'
                self.dialog.destroy()
            else:
                messagebox.showerror("Save Failed", "Failed to save changes. Please try again.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving: {e}")
    
    def delete_item(self):
        """Delete the inventory item with double confirmation."""
        card_name = self.item_data.get('name', 'Unknown Card')
        quantity = self.item_data.get('quantity', 0)
        foil_status = "Foil" if self.item_data.get('foil') else "Non-Foil"
        condition = self.item_data.get('condition', 'Unknown')
        
        # First confirmation - basic warning
        first_result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete this item from your inventory?\n\n"
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
            f"This will permanently delete {quantity}x '{card_name}' from your inventory.\n\n"
            f"This action CANNOT be undone!\n\n"
            f"Are you absolutely certain you want to proceed?",
            icon='warning'
        )
        
        if second_result:
            # Call callback with delete action
            delete_data = {'id': self.item_data['id'], 'action': 'delete'}
            success = self.callback(delete_data)
            
            if success:
                self.result = 'deleted'
                self.dialog.destroy()
            else:
                messagebox.showerror("Delete Failed", "Failed to delete item. Please try again.")
    
    def cancel(self):
        """Cancel the edit operation."""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result

class EditDeckCardDialog:
    """Dialog for editing deck cards."""
    
    def __init__(self, parent, card_data: Dict[str, Any], deck_sections: list, 
                 callback: Callable[[Dict[str, Any]], bool]):
        """
        Initialize edit deck card dialog.
        
        Args:
            parent: Parent window
            card_data: Dictionary containing current card data
            deck_sections: List of available deck sections
            callback: Function to call when saving changes
        """
        self.parent = parent
        self.card_data = card_data.copy()
        self.deck_sections = deck_sections
        self.callback = callback
        self.result = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the edit deck card dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Edit Deck Card")
        self.dialog.geometry("350x350")  # Made taller
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (350 // 2)
        self.dialog.geometry(f"350x350+{x}+{y}")
        
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Card info
        info_frame = ttk.LabelFrame(main_frame, text="Card Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=self.card_data.get('name', 'Unknown Card'), 
                  font=('TkDefaultFont', 11, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        if self.card_data.get('mana_cost'):
            ttk.Label(info_frame, text=f"Mana Cost: {self.card_data['mana_cost']}", 
                      font=('TkDefaultFont', 9)).pack(anchor=tk.W, padx=10, pady=(0, 10))
        
        # Edit options
        edit_frame = ttk.LabelFrame(main_frame, text="Edit Options")
        edit_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Quantity
        quantity_frame = ttk.Frame(edit_frame)
        quantity_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(quantity_frame, text="Quantity:", width=10).pack(side=tk.LEFT)
        self.quantity_var = tk.IntVar(value=self.card_data.get('quantity', 1))
        ttk.Spinbox(quantity_frame, from_=1, to=99, textvariable=self.quantity_var, width=8).pack(side=tk.LEFT, padx=5)
        
        # Section
        section_frame = ttk.Frame(edit_frame)
        section_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        ttk.Label(section_frame, text="Section:", width=10).pack(side=tk.LEFT)
        
        # Determine current section
        current_section = "Main Deck"
        if self.card_data.get('is_commander'):
            current_section = "Commander"
        elif self.card_data.get('is_sideboard'):
            current_section = "Sideboard"
        
        self.section_var = tk.StringVar(value=current_section)
        section_combo = ttk.Combobox(section_frame, textvariable=self.section_var,
                                     values=self.deck_sections, state="readonly", width=15)
        section_combo.pack(side=tk.LEFT, padx=5)
        
        # Buttons - Fixed layout
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)
        
        save_button = ttk.Button(button_frame, text="Save", command=self.save_changes)
        save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_button = ttk.Button(button_frame, text="Remove from Deck", command=self.remove_card)
        remove_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Bind events
        self.dialog.bind('<Return>', lambda e: self.save_changes())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Force update
        self.dialog.update_idletasks()
    
    def save_changes(self):
        """Save the changes."""
        try:
            # Determine section flags
            section = self.section_var.get()
            is_commander = (section == "Commander")
            is_sideboard = (section == "Sideboard")
            
            updated_data = {
                'id': self.card_data['id'],
                'quantity': self.quantity_var.get(),
                'is_commander': is_commander,
                'is_sideboard': is_sideboard
            }
            
            success = self.callback(updated_data)
            
            if success:
                self.result = 'saved'
                self.dialog.destroy()
            else:
                messagebox.showerror("Save Failed", "Failed to save changes.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def remove_card(self):
        """Remove the card from the deck."""
        card_name = self.card_data.get('name', 'Unknown Card')
        
        result = messagebox.askyesno(
            "Confirm Removal",
            f"Remove '{card_name}' from the deck?",
            icon='warning'
        )
        
        if result:
            remove_data = {'id': self.card_data['id'], 'action': 'remove'}
            success = self.callback(remove_data)
            
            if success:
                self.result = 'removed'
                self.dialog.destroy()
            else:
                messagebox.showerror("Remove Failed", "Failed to remove card from deck.")
    
    def cancel(self):
        """Cancel the edit operation."""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result