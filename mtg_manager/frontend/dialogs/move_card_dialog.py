# frontend/dialogs/move_card_dialog.py - Replace the entire file with this corrected version
"""
Move Card dialog for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable

class MoveCardDialog:
    """Dialog for moving cards between deck sections."""
    
    def __init__(self, parent, card_data: Dict[str, Any], current_section: str, 
                 callback: Callable[[Dict[str, Any]], bool]):
        """
        Initialize move card dialog.
        
        Args:
            parent: Parent window
            card_data: Dictionary containing card data
            current_section: Current section (main, commander, sideboard)
            callback: Function to call when moving card
        """
        self.parent = parent
        self.card_data = card_data
        self.current_section = current_section
        self.callback = callback
        self.result = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the move card dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Move Card")
        self.dialog.geometry("350x400")  # Made taller for all content
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"350x400+{x}+{y}")
        
        # FIXED: Main container with proper structure
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Card info header
        card_frame = ttk.LabelFrame(main_container, text="Card to Move")
        card_frame.pack(fill=tk.X, pady=(0, 15))
        
        card_name = self.card_data.get('name', 'Unknown Card')
        quantity = self.card_data.get('quantity', 1)
        
        ttk.Label(card_frame, text=card_name, font=('TkDefaultFont', 11, 'bold')).pack(padx=10, pady=(10, 2))
        ttk.Label(card_frame, text=f"Quantity: {quantity}", font=('TkDefaultFont', 9)).pack(padx=10, pady=(2, 10))
        
        # Current section info
        current_frame = ttk.LabelFrame(main_container, text="Current Location")
        current_frame.pack(fill=tk.X, pady=(0, 15))
        
        current_text = self.format_section_name(self.current_section)
        ttk.Label(current_frame, text=current_text, font=('TkDefaultFont', 10)).pack(padx=10, pady=10)
        
        # Move options
        move_frame = ttk.LabelFrame(main_container, text="Move To")
        move_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Get available sections (excluding current)
        all_sections = ["main", "sideboard", "commander"]
        available_sections = [s for s in all_sections if s != self.current_section]
        
        self.target_section_var = tk.StringVar()
        
        # Radio buttons for target sections
        radio_frame = ttk.Frame(move_frame)
        radio_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        for section in available_sections:
            section_text = self.format_section_name(section)
            radio = ttk.Radiobutton(radio_frame, text=section_text, 
                                   variable=self.target_section_var, value=section)
            radio.pack(anchor=tk.W, pady=2)
        
        # Set default selection
        if available_sections:
            self.target_section_var.set(available_sections[0])
        
        # Quantity to move (if partial move is desired)
        quantity_frame = ttk.Frame(move_frame)
        quantity_frame.pack(fill=tk.X, padx=10, pady=(10, 10))
        
        ttk.Label(quantity_frame, text="Quantity to move:", width=15).pack(side=tk.LEFT)
        self.move_quantity_var = tk.IntVar(value=quantity)
        quantity_spin = ttk.Spinbox(quantity_frame, from_=1, to=quantity, 
                                   textvariable=self.move_quantity_var, width=8)
        quantity_spin.pack(side=tk.LEFT, padx=5)
        
        # BUTTONS - FIXED: Proper placement at bottom
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))
        
        move_button = ttk.Button(button_frame, text="Move Card", command=self.move_card)
        move_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # Bind events
        self.dialog.bind('<Return>', lambda e: self.move_card())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Force update to ensure everything is displayed
        self.dialog.update_idletasks()
    
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
    
    def move_card(self):
        """Move the card to the selected section."""
        target_section = self.target_section_var.get()
        if not target_section:
            messagebox.showwarning("No Section Selected", "Please select a section to move to.")
            return
        
        move_quantity = self.move_quantity_var.get()
        if move_quantity <= 0:
            messagebox.showerror("Invalid Quantity", "Please enter a valid quantity.")
            return
        
        # Prepare move data
        move_data = {
            'deck_card_id': self.card_data['id'],
            'target_section': target_section,
            'move_quantity': move_quantity,
            'total_quantity': self.card_data.get('quantity', 1)
        }
        
        try:
            success = self.callback(move_data)
            
            if success:
                self.result = 'moved'
                self.dialog.destroy()
            else:
                messagebox.showerror("Move Failed", "Failed to move card.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def cancel(self):
        """Cancel the move operation."""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result