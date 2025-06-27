# frontend/dialogs/trade_dialog.py
"""
Trade dialog for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Callable
from datetime import datetime

class TradeDialog:
    """Dialog for creating trade transactions."""
    
    def __init__(self, parent, app, initial_card_data: Dict[str, Any] = None):
        """
        Initialize trade dialog.
        
        Args:
            parent: Parent window
            app: Main application instance
            initial_card_data: Optional card to start trade with
        """
        self.parent = parent
        self.app = app
        self.initial_card_data = initial_card_data
        self.result = None
        
        # Trade data
        self.cards_out = []  # Cards being traded away
        self.cards_in = []   # Cards being received
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the trade dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Record Trade")
        self.dialog.geometry("700x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"700x600+{x}+{y}")
        
        # Main container
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Trade info frame
        self.create_trade_info_frame(main_container)
        
        # Cards frame
        self.create_cards_frame(main_container)
        
        # Buttons
        self.create_buttons_frame(main_container)
        
        # Add initial card if provided
        if self.initial_card_data:
            self.add_initial_card()
        
        # Bind events
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Force update
        self.dialog.update_idletasks()
    
    def create_trade_info_frame(self, parent):
        """Create trade information frame."""
        info_frame = ttk.LabelFrame(parent, text="Trade Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Partner
        partner_frame = ttk.Frame(info_frame)
        partner_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(partner_frame, text="Trade Partner:", width=12).pack(side=tk.LEFT)
        self.partner_var = tk.StringVar()
        ttk.Entry(partner_frame, textvariable=self.partner_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # Date
        date_frame = ttk.Frame(info_frame)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(date_frame, text="Date:", width=12).pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(date_frame, textvariable=self.date_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # Note
        note_frame = ttk.Frame(info_frame)
        note_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        ttk.Label(note_frame, text="Note:", width=12).pack(side=tk.LEFT)
        self.note_var = tk.StringVar()
        ttk.Entry(note_frame, textvariable=self.note_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def create_cards_frame(self, parent):
        """Create cards trading frame."""
        cards_frame = ttk.Frame(parent)
        cards_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Cards out (giving away)
        out_frame = ttk.LabelFrame(cards_frame, text="Cards Going Out (Giving Away)")
        out_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.create_card_list(out_frame, "out")
        
        # Cards in (receiving)
        in_frame = ttk.LabelFrame(cards_frame, text="Cards Coming In (Receiving)")
        in_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_card_list(in_frame, "in")
    
    def create_card_list(self, parent, direction):
        """Create a card list for either incoming or outgoing cards."""
        # List frame
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview
        tree = ttk.Treeview(list_frame, columns=('quantity', 'set'), show='tree headings', height=10)
        tree.heading('#0', text='Card Name')
        tree.heading('quantity', text='Qty')
        tree.heading('set', text='Set')
        
        tree.column('#0', width=150)
        tree.column('quantity', width=50)
        tree.column('set', width=60)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store reference
        setattr(self, f"tree_{direction}", tree)
        
        # Add/remove buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text=f"Add Card", 
                  command=lambda: self.add_card_to_trade(direction)).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Remove Selected", 
                  command=lambda: self.remove_card_from_trade(direction)).pack(side=tk.LEFT, padx=2)
        
        # Bind double-click to edit
        tree.bind('<Double-1>', lambda e: self.edit_card_quantity(direction))
    
    def create_buttons_frame(self, parent):
        """Create buttons frame."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Record Trade", command=self.record_trade).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT)
        
        # Summary label
        self.summary_label = ttk.Label(button_frame, text="")
        self.summary_label.pack(side=tk.RIGHT, padx=10)
        
        self.update_summary()
    
    def add_initial_card(self):
        """Add initial card to outgoing trade."""
        # Ask user if they're giving this card away or receiving it
        result = messagebox.askyesquestion(
            "Trade Direction",
            f"Are you giving away '{self.initial_card_data['name']}'?",
            icon='question'
        )
        
        if result == 'yes':
            self.add_card_to_list("out", self.initial_card_data, 1)
        else:
            self.add_card_to_list("in", self.initial_card_data, 1)
    
    def add_card_to_trade(self, direction):
        """Add a card to the trade."""
        # Open card selection dialog
        card_dialog = tk.Toplevel(self.dialog)
        card_dialog.title("Add Card to Trade")
        card_dialog.geometry("400x200")
        card_dialog.transient(self.dialog)
        card_dialog.grab_set()
        
        # Card name entry
        ttk.Label(card_dialog, text="Card Name:").pack(pady=5)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(card_dialog, textvariable=name_var, width=40)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        # Quantity
        ttk.Label(card_dialog, text="Quantity:").pack(pady=5)
        quantity_var = tk.IntVar(value=1)
        ttk.Spinbox(card_dialog, from_=1, to=99, textvariable=quantity_var).pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(card_dialog)
        btn_frame.pack(pady=20)
        
        def add_card():
            card_name = name_var.get().strip()
            if not card_name:
                messagebox.showwarning("Warning", "Please enter a card name.")
                return
            
            # Search for card
            card_data = self.app.scryfall_client.search_card_by_name(card_name)
            if not card_data:
                messagebox.showerror("Error", f"Card '{card_name}' not found.")
                return
            
            # Add to trade list
            self.add_card_to_list(direction, card_data, quantity_var.get())
            card_dialog.destroy()
        
        ttk.Button(btn_frame, text="Add", command=add_card).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=card_dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter
        card_dialog.bind('<Return>', lambda e: add_card())
    
    def add_card_to_list(self, direction, card_data, quantity):
        """Add a card to the specified trade list."""
        tree = getattr(self, f"tree_{direction}")
        
        # Add to tree
        item_id = tree.insert('', tk.END,
            text=card_data['name'],
            values=(quantity, card_data.get('set', '')),
            tags=(card_data.get('id', ''),)
        )
        
        # Add to internal list
        trade_card = {
            'card_data': card_data,
            'quantity': quantity,
            'tree_item': item_id
        }
        
        if direction == "out":
            self.cards_out.append(trade_card)
        else:
            self.cards_in.append(trade_card)
        
        self.update_summary()
    
    def remove_card_from_trade(self, direction):
        """Remove selected card from trade."""
        tree = getattr(self, f"tree_{direction}")
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("Warning", "Please select a card to remove.")
            return
        
        item = selection[0]
        tree.delete(item)
        
        # Remove from internal list
        card_list = self.cards_out if direction == "out" else self.cards_in
        card_list[:] = [card for card in card_list if card['tree_item'] != item]
        
        self.update_summary()
    
    def edit_card_quantity(self, direction):
        """Edit quantity of selected card."""
        tree = getattr(self, f"tree_{direction}")
        selection = tree.selection()
        
        if not selection:
            return
        
        item = selection[0]
        current_qty = tree.item(item)['values'][0]
        
        # Simple quantity dialog
        new_qty = tk.simpledialog.askinteger("Edit Quantity", "New quantity:", initialvalue=current_qty, minvalue=1)
        
        if new_qty:
            # Update tree
            values = list(tree.item(item)['values'])
            values[0] = new_qty
            tree.item(item, values=values)
            
            # Update internal list
            card_list = self.cards_out if direction == "out" else self.cards_in
            for card in card_list:
                if card['tree_item'] == item:
                    card['quantity'] = new_qty
                    break
            
            self.update_summary()
    
    def update_summary(self):
        """Update the trade summary."""
        out_count = sum(card['quantity'] for card in self.cards_out)
        in_count = sum(card['quantity'] for card in self.cards_in)
        
        summary = f"Giving: {out_count} cards | Receiving: {in_count} cards"
        self.summary_label.config(text=summary)
    
    def record_trade(self):
        """Record the trade transaction."""
        partner = self.partner_var.get().strip()
        if not partner:
            messagebox.showwarning("Warning", "Please enter a trade partner.")
            return
        
        if not self.cards_out and not self.cards_in:
            messagebox.showwarning("Warning", "Please add at least one card to the trade.")
            return
        
        try:
            # Prepare trade data
            trade_data = {
                'partner': partner,
                'note': self.note_var.get().strip(),
                'date': f"{self.date_var.get()} 12:00:00",  # Add time component
                'cards_out': [],
                'cards_in': []
            }
            
            # Process outgoing cards
            for card_out in self.cards_out:
                card_id = self.app.inventory_manager.get_or_create_card(card_out['card_data'])
                trade_data['cards_out'].append({
                    'card_id': card_id,
                    'quantity': card_out['quantity']
                })
            
            # Process incoming cards
            for card_in in self.cards_in:
                card_id = self.app.inventory_manager.get_or_create_card(card_in['card_data'])
                trade_data['cards_in'].append({
                    'card_id': card_id,
                    'quantity': card_in['quantity']
                })
            
            # Record trade
            transaction_id = self.app.trade_tracker.add_trade_transaction(
                self.app.current_collection_id, trade_data
            )
            
            # Update inventory (remove outgoing cards, add incoming cards)
            self.update_inventory_for_trade(trade_data)
            
            self.result = 'recorded'
            self.dialog.destroy()
            
            messagebox.showinfo("Success", f"Trade recorded successfully! (ID: {transaction_id})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record trade: {e}")
            self.app.logger.error(f"Trade recording failed: {e}")
    
    def update_inventory_for_trade(self, trade_data):
        """Update inventory based on trade (remove outgoing, add incoming)."""
        # Remove outgoing cards from inventory
        for card_out in trade_data['cards_out']:
            # Find matching inventory items and reduce quantities
            # This is a simplified version - you might want more sophisticated matching
            pass
        
        # Add incoming cards to inventory
        for card_in in trade_data['cards_in']:
            # Add cards to inventory
            pass
    
    def cancel(self):
        """Cancel the trade dialog."""
        self.result = 'cancelled'
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return result."""
        self.dialog.wait_window()
        return self.result

# Add this import to the top
import tkinter.simpledialog