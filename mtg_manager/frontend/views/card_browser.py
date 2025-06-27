# frontend/views/card_browser.py
"""
Card browser view for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
import threading
import os # Added for path checking

class CardBrowser:
    """Card browser and search view."""
    
    def __init__(self, parent, app):
        """Initialize card browser."""
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        self.current_card_data = None
        
        # Use the app's shared scryfall client instead of creating a new one
        # This prevents cache reloading
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the card browser UI."""
        # Create paned window for search and details
        self.paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Search
        self.create_search_panel()
        
        # Right panel - Card details
        self.create_details_panel()
    
    def create_search_panel(self):
        """Create the search panel."""
        left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(left_frame, weight=1)
        
        # Search header
        search_header = ttk.LabelFrame(left_frame, text="Card Search")
        search_header.pack(fill=tk.X, padx=5, pady=5)
        
        # Search entry
        search_frame = ttk.Frame(search_header)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.search_entry.bind('<Return>', self.search_cards)
        
        ttk.Button(search_frame, text="Search", command=self.search_cards).pack(side=tk.LEFT, padx=5)
        
        # Advanced search options
        advanced_frame = ttk.LabelFrame(left_frame, text="Advanced Search")
        advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Color filter
        color_frame = ttk.Frame(advanced_frame)
        color_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(color_frame, text="Colors:").pack(side=tk.LEFT)
        
        self.color_vars = {}
        colors = [('W', 'White'), ('U', 'Blue'), ('B', 'Black'), ('R', 'Red'), ('G', 'Green')]
        
        for color_code, color_name in colors:
            var = tk.BooleanVar()
            self.color_vars[color_code] = var
            ttk.Checkbutton(color_frame, text=color_code, variable=var).pack(side=tk.LEFT, padx=2)
        
        # Type filter
        type_frame = ttk.Frame(advanced_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(type_frame, text="Type:").pack(side=tk.LEFT)
        
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(type_frame, textvariable=self.type_var, width=15)
        type_combo['values'] = ['', 'Creature', 'Instant', 'Sorcery', 'Artifact', 'Enchantment', 'Planeswalker', 'Land']
        type_combo.pack(side=tk.LEFT, padx=5)
        
        # CMC filter
        cmc_frame = ttk.Frame(advanced_frame)
        cmc_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(cmc_frame, text="CMC:").pack(side=tk.LEFT)
        
        self.cmc_var = tk.StringVar()
        cmc_combo = ttk.Combobox(cmc_frame, textvariable=self.cmc_var, width=10)
        cmc_combo['values'] = ['', '0', '1', '2', '3', '4', '5', '6', '7+']
        cmc_combo.pack(side=tk.LEFT, padx=5)
        
        # Search results
        results_frame = ttk.LabelFrame(left_frame, text="Search Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results listbox with scrollbar
        listbox_frame = ttk.Frame(results_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.results_listbox = tk.Listbox(listbox_frame)
        results_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_listbox.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_listbox.bind('<<ListboxSelect>>', self.on_card_select)
        self.results_listbox.bind('<Double-1>', self.add_selected_to_inventory)
        
        # Quick actions
        actions_frame = ttk.Frame(results_frame)
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(actions_frame, text="Add to Inventory", 
                           command=self.add_selected_to_inventory).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Add to Deck", 
                           command=self.add_selected_to_deck).pack(side=tk.LEFT, padx=2)
    
    def create_details_panel(self):
        """Create the card details panel."""
        self.details_frame = ttk.Frame(self.paned_window) # Changed to self.details_frame for new display_card_details
        self.paned_window.add(self.details_frame, weight=1)
        
        # Card details header
        details_header = ttk.LabelFrame(self.details_frame, text="Card Details")
        details_header.pack(fill=tk.X, padx=5, pady=5)
        
        # Create horizontal layout for image and info
        content_frame = ttk.Frame(details_header)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Card image on the left
        image_container = ttk.Frame(content_frame)
        image_container.pack(side=tk.LEFT, padx=(0, 15))
        
        self.image_label = ttk.Label(image_container, text="No card selected", 
                                             width=20, anchor=tk.CENTER, relief=tk.SUNKEN)
        self.image_label.pack()
        
        # Add refresh image button for debugging
        ttk.Button(image_container, text="Refresh Image", 
                           command=self.refresh_current_image).pack(pady=(5, 0))
        
        # Card info on the right
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Card name
        self.name_label = ttk.Label(info_frame, text="", font=('TkDefaultFont', 12, 'bold'))
        self.name_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Mana cost
        self.cost_label = ttk.Label(info_frame, text="")
        self.cost_label.pack(anchor=tk.W, pady=2)
        
        # Type line
        self.type_label = ttk.Label(info_frame, text="")
        self.type_label.pack(anchor=tk.W, pady=2)
        
        # Set info
        self.set_label = ttk.Label(info_frame, text="")
        self.set_label.pack(anchor=tk.W, pady=2)
        
        # Oracle text
        text_frame = ttk.LabelFrame(self.details_frame, text="Oracle Text") # Changed to self.details_frame
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text widget with scrollbar
        text_widget_frame = ttk.Frame(text_frame)
        text_widget_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.oracle_text = tk.Text(text_widget_frame, wrap=tk.WORD, height=8, state=tk.DISABLED)
        text_scrollbar = ttk.Scrollbar(text_widget_frame, orient=tk.VERTICAL, command=self.oracle_text.yview)
        self.oracle_text.configure(yscrollcommand=text_scrollbar.set)
        
        self.oracle_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Printings info
        printings_frame = ttk.LabelFrame(self.details_frame, text="Printings") # Changed to self.details_frame
        printings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.printings_label = ttk.Label(printings_frame, text="")
        self.printings_label.pack(padx=5, pady=5)
    
    def search_cards(self, event=None):
        """Search for cards using local Scryfall cache."""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return
        
        # Perform search in background thread using local cache
        self.app.update_status("Searching local cache...")
        
        def search_thread():
            try:
                # Use the cached search instead of API
                results = self.app.scryfall_client.search_cards_in_cache(query, limit=50)
                
                # Filter results based on advanced search options
                filtered_results = self.apply_advanced_filters(results)
                
                # Update UI in main thread
                self.app.root.after(0, lambda: self.display_cached_search_results(filtered_results))
                
            except Exception as e:
                self.app.root.after(0, lambda: messagebox.showerror("Error", f"Search failed: {e}"))
                self.app.root.after(0, lambda: self.app.update_status("Ready"))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def apply_advanced_filters(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply advanced search filters to cached results."""
        filtered = results
        
        # Apply color filters
        selected_colors = [color for color, var in self.color_vars.items() if var.get()]
        if selected_colors:
            filtered = [card for card in filtered 
                        if any(color in card.get('colors', []) for color in selected_colors)]
        
        # Apply type filter
        type_filter = self.type_var.get()
        if type_filter:
            filtered = [card for card in filtered 
                        if type_filter.lower() in card.get('type_line', '').lower()]
        
        # Apply CMC filter
        cmc_filter = self.cmc_var.get()
        if cmc_filter:
            try:
                if cmc_filter == "7+":
                    filtered = [card for card in filtered 
                                if card.get('cmc', 0) >= 7]
                else:
                    target_cmc = int(cmc_filter)
                    filtered = [card for card in filtered 
                                if card.get('cmc', 0) == target_cmc]
            except ValueError:
                pass   # Invalid CMC filter, ignore
        
        return filtered
    
    def display_cached_search_results(self, results: List[Dict[str, Any]]):
        """Display search results from cache."""
        self.results_listbox.delete(0, tk.END)
        self.search_results = results
        
        if not results:
            self.app.update_status("No results found")
            return
        
        self.app.logger.debug(f"=== CACHED SEARCH RESULTS ===")
        if results:
            first_card = results[0]
            self.app.logger.debug(f"First card: {first_card.get('name')}")
            self.app.logger.debug(f"Available keys: {list(first_card.keys())}")
            
            # Check for image fields
            for key in first_card.keys():
                if 'image' in key.lower():
                    self.app.logger.debug(f"Image field '{key}': {first_card[key]}")
        
        for card in results:
            display_text = f"{card['name']} ({card.get('set', '').upper()})"
            if card.get('collector_number'):
                display_text += f" #{card['collector_number']}"
            
            self.results_listbox.insert(tk.END, display_text)
        
        self.app.update_status(f"Found {len(results)} cards")
    
    def search_cards_api_fallback(self, query: str):
        """Fallback to API search if cache search fails."""
        self.app.logger.info("Using API fallback search")
        
        def search_thread():
            try:
                # Build search query with filters
                search_query = query
                
                # Add color filters
                selected_colors = [color for color, var in self.color_vars.items() if var.get()]
                if selected_colors:
                    search_query += f" c:{','.join(selected_colors)}"
                
                # Add type filter
                if self.type_var.get():
                    search_query += f" t:{self.type_var.get()}"
                
                # Add CMC filter
                cmc_filter = self.cmc_var.get()
                if cmc_filter:
                    if cmc_filter == "7+":
                        search_query += " cmc>=7"
                    else:
                        search_query += f" cmc:{cmc_filter}"
                
                # Use API search
                result = self.app.scryfall_client.search_cards(search_query)
                
                # Update UI in main thread
                self.app.root.after(0, lambda: self.display_api_search_results(result))
                
            except Exception as e:
                self.app.root.after(0, lambda: messagebox.showerror("Error", f"API search failed: {e}"))
                self.app.root.after(0, lambda: self.app.update_status("Ready"))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def display_api_search_results(self, result: Optional[Dict[str, Any]]):
        """Display API search results (original method)."""
        self.results_listbox.delete(0, tk.END)
        self.search_results = []
        
        if not result or 'data' not in result:
            self.app.update_status("No results found")
            return
        
        cards = result['data']
        self.search_results = cards
        
        for card in cards:
            display_text = f"{card['name']} ({card.get('set', '').upper()})"
            if card.get('collector_number'):
                display_text += f" #{card['collector_number']}"
            
            self.results_listbox.insert(tk.END, display_text)
        
        self.app.update_status(f"Found {len(cards)} cards")
    
    def on_card_select(self, event=None):
        """Handle card selection in results."""
        selection = self.results_listbox.curselection()
        if selection and self.search_results:
            card_index = selection[0]
            if card_index < len(self.search_results):
                self.current_card_data = self.search_results[card_index]
                self.app.logger.debug(f"Selected cached card: {self.current_card_data.get('name')}")
                self.display_card_details(self.current_card_data)
    
    def display_card_details(self, card_data: Dict[str, Any]):
        """Display detailed information about the selected card."""
        if not card_data:
            # Clear all fields
            self.name_label.config(text="")
            self.cost_label.config(text="")
            self.type_label.config(text="")
            self.set_label.config(text="")
            self.oracle_text.config(state=tk.NORMAL)
            self.oracle_text.delete('1.0', tk.END)
            self.oracle_text.config(state=tk.DISABLED)
            self.printings_label.config(text="")
            # No need to remove elements since we are updating existing labels
            return
        
        # Store current card data for refresh button
        self.current_card_data = card_data # Make sure this is stored to be used by image loading
        
        # Update card name
        self.name_label.config(text=card_data.get('name', 'Unknown'))
        
        # Update mana cost
        mana_cost = card_data.get('mana_cost', '')
        if mana_cost:
            self.cost_label.config(text=f"Mana Cost: {mana_cost}")
        else:
            self.cost_label.config(text="")
        
        # Update type line
        type_line = card_data.get('type_line', '')
        if type_line:
            self.type_label.config(text=f"Type: {type_line}")
        else:
            self.type_label.config(text="")
        
        # Update set info
        set_info = f"Set: {card_data.get('set', 'Unknown').upper()}"
        if card_data.get('collector_number'):
            set_info += f" #{card_data['collector_number']}"
        
        # Add other useful info
        if card_data.get('cmc') is not None:
            set_info += f" | CMC: {card_data['cmc']}"
        
        if card_data.get('power') is not None and card_data.get('toughness') is not None:
            set_info += f" | P/T: {card_data['power']}/{card_data['toughness']}"
        
        self.set_label.config(text=set_info)
        
        # Update oracle text
        oracle_text = card_data.get('oracle_text', '')
        self.oracle_text.config(state=tk.NORMAL)
        self.oracle_text.delete('1.0', tk.END)
        if oracle_text:
            self.oracle_text.insert('1.0', oracle_text)
        self.oracle_text.config(state=tk.DISABLED)
        
        # Update printings info
        printings_info = ""
        if card_data.get('set_name'):
            printings_info += f"Set: {card_data['set_name']}"
        if card_data.get('rarity'):
            printings_info += f" | Rarity: {card_data['rarity'].title()}"
        if card_data.get('released_at'):
            printings_info += f" | Released: {card_data['released_at']}"
        
        self.printings_label.config(text=printings_info)
        
        # Load and display card image
        self.load_card_image(card_data)
    
    def load_card_image(self, card_data: Dict[str, Any]):
        """Load and display card image from cached data."""
        self.app.logger.debug(f"=== Loading cached card image for: {card_data.get('name')} ===")
        
        image_url = None
        
        # Try different possible image URL fields from cached data
        if 'image_uris' in card_data and card_data['image_uris']:
            # Standard Scryfall format
            image_uris = card_data['image_uris']
            image_url = (image_uris.get('normal') or 
                         image_uris.get('large') or 
                         image_uris.get('small'))
            self.app.logger.debug(f"Found image_uris, selected: {image_url}")
        
        elif 'card_faces' in card_data and card_data['card_faces']:
            # Double-faced cards
            face = card_data['card_faces'][0]  # Use first face
            if 'image_uris' in face:
                image_uris = face['image_uris']
                image_url = (image_uris.get('normal') or 
                             image_uris.get('large') or 
                             image_uris.get('small'))
                self.app.logger.debug(f"Found double-faced card image: {image_url}")
        
        if not image_url:
            self.app.logger.debug("No image URL found in cached data")
            # Show placeholder
            placeholder = self.app.image_manager.create_placeholder_image((223, 311))
            self.image_label.config(image=placeholder, text="")
            self.image_label.image = placeholder
            return
        
        self.app.logger.debug(f"Attempting to load image: {image_url}")
        
        # Try to load cached image immediately
        tk_image = self.app.image_manager.load_image_for_tkinter(image_url, 'medium')
        
        if tk_image:
            self.image_label.config(image=tk_image, text="")
            self.image_label.image = tk_image
            self.app.logger.debug("Image loaded from cache successfully")
        else:
            # Show placeholder and start download
            self.app.logger.debug("Image not in local cache, downloading...")
            placeholder = self.app.image_manager.create_placeholder_image((223, 311))
            self.image_label.config(image=placeholder, text="")
            self.image_label.image = placeholder
            
            # Download image in background
            def image_downloaded(success, cache_path):
                self.app.logger.debug(f"Image download result: success={success}, path={cache_path}")
                if success and cache_path and os.path.exists(cache_path):
                    def update_image():
                        try:
                            # Load the downloaded image
                            from PIL import Image, ImageTk
                            pil_image = Image.open(cache_path)
                            new_image = ImageTk.PhotoImage(pil_image)
                            
                            self.image_label.config(image=new_image, text="")
                            self.image_label.image = new_image
                            self.app.logger.debug("Image updated successfully after download")
                        except Exception as e:
                            self.app.logger.error(f"Failed to update image after download: {e}")
                        
                    # Schedule UI update in main thread
                    self.app.root.after(0, update_image)
                else:
                    self.app.logger.error(f"Image download failed or file missing: {cache_path}")
            
            self.app.image_manager.download_image(image_url, 'medium', image_downloaded)
    
    def refresh_current_image(self):
        """Refresh the current card image - for debugging."""
        if hasattr(self, 'current_card_data') and self.current_card_data:
            self.app.logger.info("Manually refreshing card image")
            self.load_card_image(self.current_card_data)
        else:
            self.app.logger.info("No current card data to refresh")

    def add_selected_to_inventory(self, event=None):
        """Add selected card to inventory."""
        if not self.current_card_data:
            messagebox.showwarning("Warning", "Please select a card first.")
            return
        
        # Open quantity dialog
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Add to Inventory")
        dialog.geometry("350x280") # Made taller and wider
        dialog.transient(self.app.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (280 // 2)
        dialog.geometry(f"350x280+{x}+{y}")
        
        # Main container
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Card name header
        card_name = self.current_card_data.get('name', 'Unknown Card')
        header_label = ttk.Label(main_frame, text=f"Add '{card_name}' to inventory:", 
                                 font=('TkDefaultFont', 10, 'bold'))
        header_label.pack(pady=(0, 20))
        
        # Quantity frame
        quantity_frame = ttk.Frame(main_frame)
        quantity_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(quantity_frame, text="Quantity:", width=12).pack(side=tk.LEFT)
        quantity_var = tk.IntVar(value=1)
        quantity_spin = ttk.Spinbox(quantity_frame, from_=1, to=100, textvariable=quantity_var, width=10)
        quantity_spin.pack(side=tk.LEFT, padx=(10, 0))
        
        # Foil frame
        foil_frame = ttk.Frame(main_frame)
        foil_frame.pack(fill=tk.X, pady=(0, 15))
        
        foil_var = tk.BooleanVar()
        foil_check = ttk.Checkbutton(foil_frame, text="Foil", variable=foil_var)
        foil_check.pack(side=tk.LEFT)
        
        # Condition frame
        condition_frame = ttk.Frame(main_frame)
        condition_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(condition_frame, text="Condition:", width=12).pack(side=tk.LEFT)
        condition_var = tk.StringVar(value="Near Mint")
        condition_combo = ttk.Combobox(condition_frame, textvariable=condition_var,
                                         values=["Mint", "Near Mint", "Lightly Played",
                                                         "Moderately Played", "Heavily Played", "Damaged"],
                                         state="readonly", width=20)
        condition_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Button frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        def add_card():
            try:
                # Get or create card in database
                card_id = self.app.inventory_manager.get_or_create_card(self.current_card_data)
                
                # Add to inventory
                success = self.app.inventory_manager.add_card_to_inventory(
                    self.app.current_collection_id,
                    self.current_card_data['name'],
                    quantity_var.get(),
                    foil_var.get(),
                    condition_var.get()
                )
                
                if success:
                    dialog.destroy()
                    self.app.inventory_view.refresh()
                    self.app.update_status(f"Added {quantity_var.get()}x {self.current_card_data['name']} to inventory")
                else:
                    messagebox.showerror("Error", "Failed to add card to inventory")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add card: {e}")
        
        def cancel():
            dialog.destroy()
        
        # Buttons
        add_button = ttk.Button(button_frame, text="Add to Inventory", command=add_card)
        add_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=cancel)
        cancel_button.pack(side=tk.LEFT)
        
        # Bind events
        dialog.bind('<Return>', lambda e: add_card())
        dialog.bind('<Escape>', lambda e: cancel())
        dialog.protocol("WM_DELETE_WINDOW", cancel)
        
        # Focus on quantity field
        quantity_spin.focus()
    
    def add_selected_to_deck(self):
        """Add selected card to a deck."""
        if not self.current_card_data:
            messagebox.showwarning("Warning", "Please select a card first.")
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
                    self.app.logger.error(f"Failed to add card to deck from browser: {e}")
                    return False
            
            # Show add to deck dialog
            from frontend.dialogs.add_to_deck_dialog import AddToDeckDialog
            dialog = AddToDeckDialog(self.app.root, self.current_card_data, available_decks, add_callback)
            result = dialog.show()
            
            if result == 'added':
                self.app.logger.info(f"Card added to deck from browser successfully")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add card to deck: {e}")