# frontend/dialogs/deck_dialogs.py - Replace the entire file with this corrected version
"""
Deck management dialogs for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional

class RenameDeckDialog:
    """Dialog for renaming a deck."""
    
    def __init__(self, parent, deck_data: Dict[str, Any], callback: Callable[[str], bool]):
        """
        Initialize rename deck dialog.
        
        Args:
            parent: Parent window
            deck_data: Dictionary containing current deck data
            callback: Function to call when saving new name, returns success boolean
        """
        self.parent = parent
        self.deck_data = deck_data
        self.callback = callback
        self.result = None
        self.new_name = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the rename dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Rename Deck")
        self.dialog.geometry("400x250")  # Made taller for buttons
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (250 // 2)
        self.dialog.geometry(f"400x250+{x}+{y}")
        
        # Main container
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Current deck info
        info_frame = ttk.LabelFrame(container, text="Current Deck")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        current_name = self.deck_data.get('name', 'Unknown Deck')
        deck_format = self.deck_data.get('format', 'No Format')
        is_commander = self.deck_data.get('is_commander', False)
        
        deck_info = f"{current_name} ({deck_format})"
        if is_commander:
            deck_info += " [Commander]"
        
        ttk.Label(info_frame, text=deck_info, font=('TkDefaultFont', 10, 'bold')).pack(padx=10, pady=10)
        
        # New name input
        name_frame = ttk.LabelFrame(container, text="New Name")
        name_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(name_frame, text="Deck Name:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.name_var = tk.StringVar(value=current_name)
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, font=('TkDefaultFont', 11), width=35)
        self.name_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # Buttons - Fixed positioning
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        rename_button = ttk.Button(button_frame, text="Rename", command=self.rename_deck)
        rename_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # Bind events
        self.dialog.bind('<Return>', lambda e: self.rename_deck())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Focus and select text
        self.name_entry.focus()
        self.name_entry.select_range(0, tk.END)
        
        # Force update
        self.dialog.update_idletasks()
    
    def rename_deck(self):
        """Rename the deck."""
        new_name = self.name_var.get().strip()
        
        if not new_name:
            messagebox.showerror("Invalid Name", "Please enter a deck name.")
            self.name_entry.focus()
            return
        
        if new_name == self.deck_data.get('name', ''):
            # No change, just close
            self.cancel()
            return
        
        # Check for reasonable name length
        if len(new_name) > 100:
            messagebox.showerror("Name Too Long", "Deck name must be 100 characters or less.")
            self.name_entry.focus()
            return
        
        try:
            success = self.callback(new_name)
            
            if success:
                self.new_name = new_name
                self.result = 'renamed'
                self.dialog.destroy()
            else:
                messagebox.showerror("Rename Failed", "Failed to rename deck. The name might already be in use.")
                self.name_entry.focus()
                self.name_entry.select_range(0, tk.END)
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while renaming: {e}")
    
    def cancel(self):
        """Cancel the rename operation."""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result, self.new_name

class CopyDeckDialog:
    """Dialog for copying a deck."""
    
    def __init__(self, parent, deck_data: Dict[str, Any], callback: Callable[[str], bool]):
        """
        Initialize copy deck dialog.
        
        Args:
            parent: Parent window
            deck_data: Dictionary containing current deck data
            callback: Function to call when copying with new name, returns success boolean
        """
        self.parent = parent
        self.deck_data = deck_data
        self.callback = callback
        self.result = None
        self.new_name = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the copy dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Copy Deck")
        self.dialog.geometry("450x400")  # Made taller for buttons
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"450x400+{x}+{y}")
        
        # Main container
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Source deck info
        source_frame = ttk.LabelFrame(container, text="Source Deck")
        source_frame.pack(fill=tk.X, pady=(0, 15))
        
        current_name = self.deck_data.get('name', 'Unknown Deck')
        deck_format = self.deck_data.get('format', 'No Format')
        is_commander = self.deck_data.get('is_commander', False)
        
        deck_info = f"{current_name} ({deck_format})"
        if is_commander:
            deck_info += " [Commander]"
        
        ttk.Label(source_frame, text=deck_info, font=('TkDefaultFont', 10, 'bold')).pack(padx=10, pady=10)
        
        # Copy options
        options_frame = ttk.LabelFrame(container, text="Copy Options")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # New name input
        ttk.Label(options_frame, text="New Deck Name:").pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Suggest a default name
        suggested_name = f"{current_name} (Copy)"
        self.name_var = tk.StringVar(value=suggested_name)
        self.name_entry = ttk.Entry(options_frame, textvariable=self.name_var, font=('TkDefaultFont', 11), width=40)
        self.name_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # Copy what options
        copy_options_frame = ttk.Frame(options_frame)
        copy_options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(copy_options_frame, text="What to copy:", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.W)
        
        self.copy_main_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(copy_options_frame, text="Main deck cards", variable=self.copy_main_var).pack(anchor=tk.W, padx=20)
        
        self.copy_commander_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(copy_options_frame, text="Commander", variable=self.copy_commander_var).pack(anchor=tk.W, padx=20)
        
        self.copy_sideboard_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(copy_options_frame, text="Sideboard", variable=self.copy_sideboard_var).pack(anchor=tk.W, padx=20)
        
        # Buttons - Fixed positioning
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        create_button = ttk.Button(button_frame, text="Create Copy", command=self.copy_deck)
        create_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # Bind events
        self.dialog.bind('<Return>', lambda e: self.copy_deck())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Focus and select text
        self.name_entry.focus()
        self.name_entry.select_range(0, tk.END)
        
        # Force update
        self.dialog.update_idletasks()
    
    def copy_deck(self):
        """Copy the deck."""
        new_name = self.name_var.get().strip()
        
        if not new_name:
            messagebox.showerror("Invalid Name", "Please enter a name for the copied deck.")
            self.name_entry.focus()
            return
        
        if len(new_name) > 100:
            messagebox.showerror("Name Too Long", "Deck name must be 100 characters or less.")
            self.name_entry.focus()
            return
        
        # Check if at least one section is selected
        if not (self.copy_main_var.get() or self.copy_commander_var.get() or self.copy_sideboard_var.get()):
            messagebox.showerror("Nothing to Copy", "Please select at least one section to copy.")
            return
        
        try:
            # Prepare copy options
            copy_options = {
                'name': new_name,
                'copy_main': self.copy_main_var.get(),
                'copy_commander': self.copy_commander_var.get(),
                'copy_sideboard': self.copy_sideboard_var.get()
            }
            
            success = self.callback(copy_options)
            
            if success:
                self.new_name = new_name
                self.result = 'copied'
                self.dialog.destroy()
            else:
                messagebox.showerror("Copy Failed", "Failed to copy deck. The name might already be in use.")
                self.name_entry.focus()
                self.name_entry.select_range(0, tk.END)
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while copying: {e}")
    
    def cancel(self):
        """Cancel the copy operation."""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result, self.new_name

class DeleteDeckDialog:
    """Dialog for confirming deck deletion."""
    
    def __init__(self, parent, deck_data: Dict[str, Any], deck_stats: Dict[str, Any], callback: Callable[[], bool]):
        """
        Initialize delete deck dialog.
        
        Args:
            parent: Parent window
            deck_data: Dictionary containing deck data
            deck_stats: Dictionary containing deck statistics
            callback: Function to call when confirming deletion, returns success boolean
        """
        self.parent = parent
        self.deck_data = deck_data
        self.deck_stats = deck_stats
        self.callback = callback
        self.result = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the delete confirmation dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Delete Deck")
        self.dialog.geometry("450x450")  # Made taller for buttons
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"450x450+{x}+{y}")
        
        # Main container
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Warning icon and title
        title_frame = ttk.Frame(container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="⚠️ Delete Deck", font=('TkDefaultFont', 14, 'bold'), 
                 foreground='red').pack()
        
        # Deck info
        info_frame = ttk.LabelFrame(container, text="Deck to Delete")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        deck_name = self.deck_data.get('name', 'Unknown Deck')
        deck_format = self.deck_data.get('format', 'No Format')
        is_commander = self.deck_data.get('is_commander', False)
        
        deck_info = f"{deck_name} ({deck_format})"
        if is_commander:
            deck_info += " [Commander]"
        
        ttk.Label(info_frame, text=deck_info, font=('TkDefaultFont', 11, 'bold')).pack(padx=10, pady=(10, 5))
        
        # Deck statistics
        total_cards = self.deck_stats.get('total_cards', 0)
        unique_cards = self.deck_stats.get('unique_cards', 0)
        main_deck_count = self.deck_stats.get('main_deck_count', 0)
        
        stats_text = f"Total Cards: {total_cards} | Unique Cards: {unique_cards} | Main Deck: {main_deck_count}"
        ttk.Label(info_frame, text=stats_text, font=('TkDefaultFont', 9)).pack(padx=10, pady=(0, 10))
        
        # Warning message
        warning_frame = ttk.LabelFrame(container, text="Warning")
        warning_frame.pack(fill=tk.X, pady=(0, 15))
        
        warning_text = (
            "This action will permanently delete the entire deck and all its cards.\n\n"
            "This cannot be undone!\n\n"
            "Are you absolutely sure you want to delete this deck?"
        )
        
        ttk.Label(warning_frame, text=warning_text, font=('TkDefaultFont', 10), 
                 justify=tk.CENTER, foreground='darkred').pack(padx=15, pady=15)
        
        # Confirmation checkbox
        self.confirm_var = tk.BooleanVar()
        confirm_frame = ttk.Frame(container)
        confirm_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Checkbutton(confirm_frame, text="I understand that this action cannot be undone", 
                       variable=self.confirm_var, command=self.update_delete_button).pack()
        
        # Buttons - Fixed positioning
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.delete_button = ttk.Button(button_frame, text="Delete Deck", command=self.delete_deck, 
                                       state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # Bind events
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Force update
        self.dialog.update_idletasks()
    
    def update_delete_button(self):
        """Update delete button state based on confirmation checkbox."""
        if self.confirm_var.get():
            self.delete_button.config(state=tk.NORMAL)
        else:
            self.delete_button.config(state=tk.DISABLED)
    
    def delete_deck(self):
        """Delete the deck."""
        if not self.confirm_var.get():
            messagebox.showerror("Confirmation Required", "Please confirm that you understand this action cannot be undone.")
            return
        
        try:
            success = self.callback()
            
            if success:
                self.result = 'deleted'
                self.dialog.destroy()
            else:
                messagebox.showerror("Delete Failed", "Failed to delete deck. Please try again.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while deleting: {e}")
    
    def cancel(self):
        """Cancel the delete operation."""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        self.dialog.wait_window()
        return self.result