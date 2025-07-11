# frontend/gui.py
"""
Main GUI application for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import threading
from typing import Dict, Any
import csv
import os # Added for debug_image_cache

from backend.utils.db import DatabaseManager
from backend.data.inventory import InventoryManager
from backend.decks.deck_builder import DeckBuilder
from backend.data.trade_tracker import TradeTracker
from backend.utils.backup import BackupManager
from backend.utils.csv_handler import CSVHandler
from backend.api.scryfall_client import ScryfallClient # Import ScryfallClient

from frontend.views.inventory_view import InventoryView
from frontend.views.deck_view import DeckView
from frontend.views.card_browser import CardBrowser
from frontend.views.trade_view import TradeView # NEW: Import TradeView

class MTGCollectionApp:
    """Main application window for MTG Collection Manager."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the main application."""
        self.root = root
        self.logger = logging.getLogger(__name__)
        
        # Initialize shared components first
        self.db_manager = DatabaseManager()
        
        # Create single ScryfallClient instance for the entire app
        self.scryfall_client = ScryfallClient.get_instance()
        self.logger.info("Shared ScryfallClient instance created")
        
        # Initialize Image Manager
        from backend.utils.image_manager import ImageManager
        self.image_manager = ImageManager()
        self.logger.info("Image Manager initialized")
        
        # Initialize backend managers with shared scryfall client
        self.inventory_manager = InventoryManager(self.db_manager, self.scryfall_client)
        self.deck_builder = DeckBuilder(self.db_manager)
        self.trade_tracker = TradeTracker(self.db_manager)
        self.backup_manager = BackupManager(self.db_manager)
        self.csv_handler = CSVHandler(self.db_manager, self.scryfall_client) # Pass scryfall_client to CSVHandler
        
        # Current collection
        self.current_collection_id = 1  # Default collection
        
        self.setup_ui()
        self.load_collections()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.root.title("MTG Collection Manager")
        self.root.geometry("1200x800")
        
        # Create main menu
        self.create_menu()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main content area with tabs
        self.create_main_area()
        
        # Create status bar
        self.create_status_bar()
    
    def create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="New Collection", command=self.new_collection)
        file_menu.add_separator()
        file_menu.add_command(label="Import CSV", command=self.import_csv)
        file_menu.add_command(label="Import JSON", command=self.import_json)
        file_menu.add_separator()
        file_menu.add_command(label="Export CSV", command=self.export_csv)
        file_menu.add_command(label="Export JSON", command=self.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_command(label="Restore Database", command=self.restore_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Updated: Change 'OCR Scanner' to 'AI Vision Scanner' and use new method
        tools_menu.add_command(label="AI Vision Scanner", command=self.open_ocr_scanner) 
        tools_menu.add_command(label="Bulk Download", command=self.bulk_download)
        tools_menu.add_command(label="CSV Format Help", command=self.show_csv_help)
        tools_menu.add_separator()
        tools_menu.add_command(label="Image Cache Stats", command=self.show_image_cache_stats)
        tools_menu.add_command(label="Clear Old Images", command=self.clear_old_images)
        tools_menu.add_separator()
        tools_menu.add_command(label="Debug Image Cache", command=self.debug_image_cache)
        tools_menu.add_command(label="Test Image Download", command=self.test_image_download)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_toolbar(self):
        """Create the application toolbar."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Collection selector
        ttk.Label(toolbar, text="Collection:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.collection_var = tk.StringVar()
        self.collection_combo = ttk.Combobox(
            toolbar, textvariable=self.collection_var, 
            state="readonly", width=20
        )
        self.collection_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.collection_combo.bind('<<ComboboxSelected>>', self.on_collection_changed)
        
        # Quick action buttons
        ttk.Button(toolbar, text="Add Card", command=self.quick_add_card).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="New Deck", command=self.quick_new_deck).pack(side=tk.LEFT, padx=5)
    
    def create_main_area(self):
        """Create the main tabbed interface."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.inventory_view = InventoryView(self.notebook, self)
        self.deck_view = DeckView(self.notebook, self)
        self.card_browser = CardBrowser(self.notebook, self)
        
        # NEW: Add trade view
        self.trade_view = TradeView(self.notebook, self)
        
        # Add tabs to notebook
        self.notebook.add(self.inventory_view.frame, text="Inventory")
        self.notebook.add(self.deck_view.frame, text="Decks")
        self.notebook.add(self.card_browser.frame, text="Card Browser")
        self.notebook.add(self.trade_view.frame, text="Trades") # NEW TAB
    
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
    
    def load_collections(self):
        """Load collections into the combo box."""
        collections = self.inventory_manager.get_collections()
        collection_names = [f"{col.name} (ID: {col.id})" for col in collections]
        
        self.collection_combo['values'] = collection_names
        if collection_names:
            self.collection_combo.set(collection_names[0])
            self.current_collection_id = collections[0].id
    
    def on_collection_changed(self, event=None):
        """Handle collection selection change."""
        selected = self.collection_var.get()
        if selected:
            # Extract collection ID from the selected text
            collection_id = int(selected.split("ID: ")[1].split(")")[0])
            self.current_collection_id = collection_id
            
            # Refresh all views
            self.inventory_view.refresh()
            self.deck_view.refresh()
            self.trade_view.refresh() # NEW: Refresh TradeView
            
            self.update_status(f"Switched to collection: {selected.split(' (ID:')[0]}")
    
    def update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    # Menu command implementations
    def new_collection(self):
        """Create a new collection."""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Collection")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Collection Name:").pack(pady=10)
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def create_collection():
            name = name_var.get().strip()
            if name:
                try:
                    collection_id = self.inventory_manager.create_collection(name)
                    self.load_collections()
                    # Select the new collection
                    for i, value in enumerate(self.collection_combo['values']):
                        if f"ID: {collection_id}" in value:
                            self.collection_combo.current(i)
                            self.on_collection_changed()
                            break
                    dialog.destroy()
                    self.update_status(f"Created collection: {name}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create collection: {e}")
            else:
                messagebox.showwarning("Warning", "Please enter a collection name.")
        
        ttk.Button(button_frame, text="Create", command=create_collection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        dialog.bind('<Return>', lambda e: create_collection())
    
    def quick_add_card(self):
        """Quick add card dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Card")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Card name
        ttk.Label(dialog, text="Card Name:").pack(pady=5)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        # Quantity
        ttk.Label(dialog, text="Quantity:").pack(pady=5)
        quantity_var = tk.IntVar(value=1)
        quantity_spin = ttk.Spinbox(dialog, from_=1, to=100, textvariable=quantity_var, width=10)
        quantity_spin.pack(pady=5)
        
        # Foil checkbox
        foil_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="Foil", variable=foil_var).pack(pady=5)
        
        # Condition
        ttk.Label(dialog, text="Condition:").pack(pady=5)
        condition_var = tk.StringVar(value="Near Mint")
        condition_combo = ttk.Combobox(
            dialog, textvariable=condition_var,
            values=["Mint", "Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", "Damaged"],
            state="readonly"
        )
        condition_combo.pack(pady=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def add_card():
            name = name_var.get().strip()
            if name:
                try:
                    success = self.inventory_manager.add_card_to_inventory(
                        self.current_collection_id,
                        name,
                        quantity_var.get(),
                        foil_var.get(),
                        condition_var.get()
                    )
                    if success:
                        dialog.destroy()
                        self.inventory_view.refresh()
                        self.update_status(f"Added {quantity_var.get()}x {name} to inventory")
                    else:
                        messagebox.showerror("Error", f"Card '{name}' not found")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to add card: {e}")
            else:
                messagebox.showwarning("Warning", "Please enter a card name.")
        
        ttk.Button(button_frame, text="Add", command=add_card).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        dialog.bind('<Return>', lambda e: add_card())
    
    def quick_new_deck(self):
        """Quick new deck dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Deck")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Deck name
        ttk.Label(dialog, text="Deck Name:").pack(pady=5)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        # Format
        ttk.Label(dialog, text="Format:").pack(pady=5)
        format_var = tk.StringVar(value="Standard")
        format_combo = ttk.Combobox(
            dialog, textvariable=format_var,
            values=["Standard", "Modern", "Legacy", "Vintage", "Commander", "Pioneer", "Historic", "Casual"],
            state="readonly"
        )
        format_combo.pack(pady=5)
        
        # Commander checkbox
        commander_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="Commander Deck", variable=commander_var).pack(pady=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def create_deck():
            name = name_var.get().strip()
            if name:
                try:
                    deck_id = self.deck_builder.create_deck(
                        self.current_collection_id,
                        name,
                        format_var.get(),
                        commander_var.get()
                    )
                    dialog.destroy()
                    self.deck_view.refresh()
                    self.update_status(f"Created deck: {name}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create deck: {e}")
            else:
                messagebox.showwarning("Warning", "Please enter a deck name.")
        
        ttk.Button(button_frame, text="Create", command=create_deck).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        dialog.bind('<Return>', lambda e: create_deck())
    
    def import_csv(self):
        """Import inventory from CSV file."""
        file_path = filedialog.askopenfilename(
            title="Import CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            # Show import options dialog
            self.show_csv_import_dialog(file_path)
    
    def show_csv_import_dialog(self, file_path: str):
        """Show CSV import options dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("CSV Import Options")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # File info
        ttk.Label(dialog, text=f"File: {file_path.split('/')[-1]}", 
                            font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        # Import options
        options_frame = ttk.LabelFrame(dialog, text="Import Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Update existing cards option
        update_existing_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, 
            text="Update quantities for existing cards",
            variable=update_existing_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Preview option
        show_preview_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Show preview before importing",
            variable=show_preview_var
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Progress frame (hidden initially)
        progress_frame = ttk.LabelFrame(dialog, text="Import Progress")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        progress_frame.pack_forget()  # Hide initially
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=10, pady=5)
        
        status_label = ttk.Label(progress_frame, text="")
        status_label.pack(pady=2)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def start_import():
            if show_preview_var.get():
                # Show preview first
                self.show_csv_preview(file_path, dialog, update_existing_var.get())
            else:
                # Import directly
                self.perform_csv_import(file_path, update_existing_var.get(), 
                                         progress_frame, progress_var, status_label, dialog)
        
        ttk.Button(button_frame, text="Import", command=start_import).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_csv_preview(self, file_path: str, parent_dialog: tk.Toplevel, update_existing: bool):
        """Show CSV import preview."""
        preview_dialog = tk.Toplevel(parent_dialog)
        preview_dialog.title("CSV Import Preview")
        preview_dialog.geometry("800x500")
        preview_dialog.transient(parent_dialog)
        preview_dialog.grab_set()
        
        # Preview frame
        preview_frame = ttk.LabelFrame(preview_dialog, text="Preview (First 10 rows)")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for preview
        columns = ('Card Name', 'Quantity', 'Foil', 'Condition', 'Status')
        tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load preview data using shared scryfall client
        try:
            # Use the app's shared scryfall client for the CSVHandler
            csv_handler_preview = CSVHandler(self.db_manager, self.scryfall_client)
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for i, row in enumerate(reader):
                    if i >= 10:  # Only show first 10 rows
                        break
                    
                    card_name = row.get('Card Name', '').strip()
                    quantity = row.get('Quantity', '1')
                    foil = row.get('Foil', 'No')
                    condition = row.get('Condition', 'Near Mint')
                    
                    # Check if card exists in database using scryfall_client from csv_handler
                    card_data = csv_handler_preview.scryfall_client.search_card_in_cache(card_name)
                    status = "✓ Found" if card_data else "⚠ Not Found"
                    
                    tree.insert('', tk.END, values=(card_name, quantity, foil, condition, status))
            
        except Exception as e:
            tree.insert('', tk.END, values=("Error reading file", str(e), "", "", "✗ Error"))
        
        # Button frame
        button_frame = ttk.Frame(preview_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def proceed_import():
            preview_dialog.destroy()
            self.perform_csv_import(file_path, update_existing, None, None, None, parent_dialog)
        
        ttk.Button(button_frame, text="Proceed with Import", command=proceed_import).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=preview_dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def perform_csv_import(self, file_path: str, update_existing: bool, 
                            progress_frame=None, progress_var=None, status_label=None, dialog=None):
        """Perform the actual CSV import."""
        if progress_frame:
            progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def import_worker():
            try:
                # Use the app's shared scryfall client for the CSVHandler
                csv_handler_import = CSVHandler(self.db_manager, self.scryfall_client)
                
                if status_label:
                    self.root.after(0, lambda: status_label.config(text="Importing CSV..."))
                
                self.root.after(0, lambda: self.update_status("Importing CSV..."))
                
                results = csv_handler_import.import_inventory_from_csv(
                    self.current_collection_id, file_path, update_existing
                )
                
                # Update UI in main thread
                self.root.after(0, lambda: self.handle_csv_import_results(results, dialog))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_csv_import_error(str(e), dialog))
        
        # Start import in background thread
        threading.Thread(target=import_worker, daemon=True).start()
    
    def handle_csv_import_results(self, results: Dict[str, Any], dialog: tk.Toplevel):
        """Handle CSV import results."""
        if dialog:
            dialog.destroy()
        
        if results['success']:
            message = (f"Import completed!\n\n"
                       f"Imported: {results['imported']} cards\n"
                       f"Skipped: {results['skipped']} cards\n"
                       f"Total rows processed: {results['total_rows']}")
            
            if results['errors']:
                message += f"\n\nErrors encountered: {len(results['errors'])}"
                if len(results['errors']) <= 5:
                    message += "\n" + "\n".join(results['errors'][:5])
                else:
                    message += f"\nFirst 5 errors:\n" + "\n".join(results['errors'][:5])
                    message += f"\n... and {len(results['errors']) - 5} more errors"
            
            messagebox.showinfo("Import Results", message)
            
            # Refresh inventory view
            self.inventory_view.refresh()
            self.update_status(f"Imported {results['imported']} cards from CSV")
        else:
            error_message = "Import failed!\n\n"
            if results['errors']:
                error_message += "\n".join(results['errors'][:10])
            messagebox.showerror("Import Failed", error_message)
            self.update_status("CSV import failed")
    
    def handle_csv_import_error(self, error_message: str, dialog: tk.Toplevel):
        """Handle CSV import error."""
        if dialog:
            dialog.destroy()
        
        messagebox.showerror("Error", f"Import failed: {error_message}")
        self.update_status("CSV import failed")
    
    def export_csv(self):
        """Export inventory to CSV file."""
        file_path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.update_status("Exporting to CSV...")
                
                success = self.csv_handler.export_inventory_to_csv(
                    self.current_collection_id, file_path
                )
                
                if success:
                    messagebox.showinfo("Success", f"Inventory exported to {file_path}")
                    self.update_status("CSV export completed")
                else:
                    messagebox.showerror("Error", "Failed to export inventory")
                    self.update_status("CSV export failed")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
                self.update_status("CSV export failed")
    
    def show_csv_help(self):
        """Show CSV format help dialog."""
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("CSV Format Help")
        help_dialog.geometry("600x500")
        help_dialog.transient(self.root)
        help_dialog.grab_set()
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(help_dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        help_text = """CSV Import/Export Format Help

REQUIRED COLUMNS:
• Card Name - The exact name of the Magic card
• Quantity - Number of copies (must be a positive integer)

OPTIONAL COLUMNS:
• Set Code - Three-letter set code (e.g., "M21", "ZNR")
• Collector Number - Card number within the set
• Foil - "Yes", "No", "True", "False", "1", or "0"
• Condition - "Mint", "Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", or "Damaged"

SAMPLE CSV FORMAT:
Card Name,Set Code,Collector Number,Quantity,Foil,Condition
Lightning Bolt,M11,146,4,No,Near Mint
Black Lotus,LEA,232,1,No,Lightly Played
Jace the Mind Sculptor,WWK,31,2,Yes,Near Mint
Counterspell,M21,59,4,No,Near Mint

IMPORT NOTES:
• The first row must contain column headers
• Card names must match exactly (case-insensitive)
• Cards not found in the database will be skipped
• Use the bulk download feature first to populate the card database
• Commas in card names should be properly escaped
• UTF-8 encoding is recommended for special characters

EXPORT NOTES:
• Exported files include all available card information
• Files are saved in UTF-8 encoding
• Compatible with Excel and other spreadsheet programs
• Set names and oracle text are included when available

TIPS:
• Download the card database first for better import success
• Use "Show preview" option to check your data before importing
• Check the import results dialog for any errors or skipped cards
• Keep backups of your data before importing large CSV files
"""
        
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        ttk.Button(help_dialog, text="Close", command=help_dialog.destroy).pack(pady=10)
    
    def import_json(self):
        """Import data from JSON file."""
        file_path = filedialog.askopenfilename(
            title="Import JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                success = self.backup_manager.import_from_json(file_path, merge=True)
                if success:
                    self.load_collections()
                    self.inventory_view.refresh()
                    self.deck_view.refresh()
                    self.trade_view.refresh() # NEW: Refresh TradeView after import
                    messagebox.showinfo("Success", "Data imported successfully")
                else:
                    messagebox.showerror("Error", "Failed to import data")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {e}")
    
    def export_json(self):
        """Export data to JSON file."""
        file_path = filedialog.asksaveasfilename(
            title="Export JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                success = self.backup_manager.export_to_json(file_path)
                if success:
                    messagebox.showinfo("Success", "Data exported successfully")
                else:
                    messagebox.showerror("Error", "Failed to export data")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    def backup_database(self):
        """Create database backup."""
        file_path = filedialog.asksaveasfilename(
            title="Backup Database",
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                success = self.backup_manager.create_backup(file_path)
                if success:
                    messagebox.showinfo("Success", "Database backed up successfully")
                else:
                    messagebox.showerror("Error", "Failed to create backup")
            except Exception as e:
                messagebox.showerror("Error", f"Backup failed: {e}")
    
    def restore_database(self):
        """Restore database from backup."""
        file_path = filedialog.askopenfilename(
            title="Restore Database",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if file_path:
            result = messagebox.askyesno(
                "Confirm Restore",
                "This will replace your current database. Are you sure?"
            )
            if result:
                try:
                    success = self.backup_manager.restore_backup(file_path)
                    if success:
                        self.load_collections()
                        self.inventory_view.refresh()
                        self.deck_view.refresh()
                        self.trade_view.refresh() # NEW: Refresh TradeView after restore
                        messagebox.showinfo("Success", "Database restored successfully")
                    else:
                        messagebox.showerror("Error", "Failed to restore database")
                except Exception as e:
                    messagebox.showerror("Error", f"Restore failed: {e}")
    
    # Replaced open_ocr_scanner with open_ai_vision_scanner
    def open_ocr_scanner(self):
        """Open AI Vision scanner window."""
        try:
            # Check if Ollama is available before opening scanner
            from backend.ai.ollama_client import OllamaClient
            
            # Quick availability check
            test_client = OllamaClient()
            if not test_client.is_available:
                result = messagebox.askyesno(
                    "Ollama Not Running",
                    "Ollama AI service is not running or not installed.\n\n"
                    "The AI Vision Scanner requires Ollama to be running.\n\n"
                    "Would you like to open the scanner anyway?\n"
                    "(You can set up Ollama later)",
                    icon='warning'
                )
                if not result:
                    return
            
            # Open the vision scanner
            from frontend.views.ocr_scanner import VisionScannerWindow
            scanner = VisionScannerWindow(self.root, self)
            
        except ImportError as e:
            messagebox.showerror(
                "Missing Dependencies", 
                f"AI Vision scanner dependencies not available: {e}\n\n"
                "Required packages:\n"
                "• requests\n"
                "• opencv-python\n"
                "• Pillow\n\n"
                "Install with: pip install requests opencv-python Pillow"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open AI Vision scanner: {e}")
            self.logger.error(f"Vision scanner error: {e}")
    
    def bulk_download(self):
        """Download bulk card data from Scryfall."""
        from frontend.dialogs.bulk_download_dialog import BulkDownloadDialog
        
        try:
            dialog = BulkDownloadDialog(self.root, self.inventory_manager.scryfall_client)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open bulk download dialog: {e}")
    
    def show_image_cache_stats(self):
        """Show image cache statistics."""
        try:
            stats = self.image_manager.get_cache_stats()
            
            # The original code's `stats` dict had 'total_images' and 'last_cleaned'
            # but the ImageManager's `get_cache_stats` returns 'total_files' and does not track 'last_cleaned'.
            # Adjusting to match the actual ImageManager implementation.
            message = (f"Image Cache Statistics:\n\n"
                       f"Total images: {stats['total_files']}\n"
                       f"Cache size: {stats['total_size_mb']:.2f} MB\n"
                       f"Cache Directory: {stats['cache_directory']}")
            messagebox.showinfo("Image Cache Stats", message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve image cache stats: {e}")

    def clear_old_images(self):
        """Clear old images from the cache."""
        result = messagebox.askyesno(
            "Confirm Clear Cache",
            "This will remove images not associated with cards in your current collections.\n"
            "Are you sure you want to proceed?"
        )
        if result:
            try:
                self.update_status("Clearing old images from cache...")
                # Pass a list of all card IDs from all collections to image_manager
                all_card_ids = []
                collections = self.inventory_manager.get_collections()
                for collection in collections:
                    cards = self.inventory_manager.get_all_cards_in_collection(collection.id)
                    all_card_ids.extend([card.scryfall_id for card in cards if card.scryfall_id])
                
                # Note: The original image_manager.clear_old_images does not take card_ids.
                # Assuming this functionality will be added or is handled differently.
                # For now, it will just clear based on `older_than_days`.
                cleaned_count = self.image_manager.clear_cache() # Changed to clear_cache as per ImageManager
                messagebox.showinfo("Clear Cache", f"Successfully cleared {cleaned_count} old images from cache.")
                self.update_status(f"Cleared {cleaned_count} old images from cache.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear old images: {e}")
                self.update_status("Failed to clear image cache.")
    
    def debug_image_cache(self):
        """Debug image cache contents."""
        try:
            cache_dir = self.image_manager.cache_dir
            
            if not os.path.exists(cache_dir):
                messagebox.showinfo("Debug", f"Cache directory doesn't exist: {cache_dir}")
                return
            
            files = os.listdir(cache_dir)
            
            message = f"Image Cache Debug:\n\n"
            message += f"Cache Directory: {cache_dir}\n"
            message += f"Files in cache: {len(files)}\n\n"
            
            if files:
                message += "Recent files:\n"
                for file in files[:10]:  # Show first 10 files
                    file_path = os.path.join(cache_dir, file)
                    file_size = os.path.getsize(file_path)
                    message += f"  {file} ({file_size} bytes)\n"
                
                if len(files) > 10:
                    message += f"  ... and {len(files) - 10} more files\n"
            else:
                message += "No cached images found."
            
            messagebox.showinfo("Image Cache Debug", message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Debug failed: {e}")

    def test_image_download(self):
        """Test image download with a known URL."""
        # Test with a known Magic card image URL
        test_url = "https://cards.scryfall.io/normal/front/c/1/c1109d26-ab70-4a9a-8a7e-6b2c3a0e3a0e.jpg"
        
        self.logger.info(f"Testing image download with URL: {test_url}")
        
        def download_callback(success, cache_path):
            message = f"Test download result:\n\nSuccess: {success}\nCache path: {cache_path}"
            if success and cache_path:
                message += f"\nFile exists: {os.path.exists(cache_path)}"
                if os.path.exists(cache_path):
                    file_size = os.path.getsize(cache_path)
                    message += f"\nFile size: {file_size} bytes"
            
            messagebox.showinfo("Test Image Download", message)
        
        self.image_manager.download_image(test_url, 'medium', download_callback)

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About MTG Collection Manager",
            "MTG Collection Manager v1.0\n\n"
            "A desktop application for managing Magic: The Gathering\n"
            "card collections and deck building.\n\n"
            "Built with Python and Tkinter\n"
            "Card data provided by Scryfall API"
        )