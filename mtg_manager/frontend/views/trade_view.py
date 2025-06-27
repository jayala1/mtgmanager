# frontend/views/trade_view.py
"""
Trade view for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List
from datetime import datetime, timedelta

class TradeView:
    """Trade management view."""
    
    def __init__(self, parent, app):
        """Initialize trade view."""
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Set up the trade view UI."""
        # Toolbar
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="New Trade", command=self.new_trade).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Filter by date
        ttk.Label(toolbar, text="Show trades from:").pack(side=tk.LEFT, padx=5)
        self.date_filter_var = tk.StringVar(value="all")
        date_combo = ttk.Combobox(toolbar, textvariable=self.date_filter_var,
                                 values=["all", "last_week", "last_month", "last_year"],
                                 state="readonly", width=12)
        date_combo.pack(side=tk.LEFT, padx=5)
        date_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Trade statistics
        stats_frame = ttk.LabelFrame(self.frame, text="Trade Statistics")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="")
        self.stats_label.pack(padx=10, pady=5)
        
        # Trade transactions list
        transactions_frame = ttk.LabelFrame(self.frame, text="Trade Transactions")
        transactions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for transactions
        self.transactions_tree = ttk.Treeview(transactions_frame, 
            columns=('partner', 'date', 'cards_out', 'cards_in', 'note'), 
            show='tree headings')
        
        # Configure columns
        self.transactions_tree.heading('#0', text='ID')
        self.transactions_tree.heading('partner', text='Partner')
        self.transactions_tree.heading('date', text='Date')
        self.transactions_tree.heading('cards_out', text='Given')
        self.transactions_tree.heading('cards_in', text='Received')
        self.transactions_tree.heading('note', text='Note')
        
        # Configure column widths
        self.transactions_tree.column('#0', width=50)
        self.transactions_tree.column('partner', width=120)
        self.transactions_tree.column('date', width=100)
        self.transactions_tree.column('cards_out', width=60)
        self.transactions_tree.column('cards_in', width=60)
        self.transactions_tree.column('note', width=200)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(transactions_frame, orient=tk.VERTICAL, command=self.transactions_tree.yview)
        h_scrollbar = ttk.Scrollbar(transactions_frame, orient=tk.HORIZONTAL, command=self.transactions_tree.xview)
        self.transactions_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.transactions_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        transactions_frame.grid_rowconfigure(0, weight=1)
        transactions_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu
        self.create_context_menu()
        self.transactions_tree.bind('<Button-3>', self.show_context_menu)
        self.transactions_tree.bind('<Double-1>', self.view_trade_details)
    
    def create_context_menu(self):
        """Create context menu for trade transactions."""
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="View Details", command=self.view_trade_details)
        self.context_menu.add_command(label="Delete Trade", command=self.delete_trade)
    
    def show_context_menu(self, event):
        """Show context menu."""
        item = self.transactions_tree.identify_row(event.y)
        if item:
            self.transactions_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def refresh(self):
        """Refresh the trade view."""
        # Clear existing items
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)
        
        try:
            # Get trade transactions
            transactions = self.app.trade_tracker.get_trade_transactions(self.app.current_collection_id)
            
            # Apply date filter
            filtered_transactions = self.apply_date_filter(transactions)
            
            # Populate tree
            for transaction in filtered_transactions:
                self.transactions_tree.insert('', tk.END,
                    text=transaction['id'],
                    values=(
                        transaction['partner'] or 'Unknown',
                        transaction['date'][:10] if transaction['date'] else '',
                        transaction['cards_out'] or 0,
                        transaction['cards_in'] or 0,
                        transaction['note'] or ''
                    ),
                    tags=(str(transaction['id']),)
                )
            
            # Update statistics
            self.update_statistics()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load trades: {e}")
    
    def apply_date_filter(self, transactions):
        """Apply date filter to transactions."""
        filter_value = self.date_filter_var.get()
        
        if filter_value == "all":
            return transactions
        
        # Calculate cutoff date
        now = datetime.now()
        if filter_value == "last_week":
            cutoff = now - timedelta(weeks=1)
        elif filter_value == "last_month":
            cutoff = now - timedelta(days=30)
        elif filter_value == "last_year":
            cutoff = now - timedelta(days=365)
        else:
            return transactions
        
        # Filter transactions
        filtered = []
        for transaction in transactions:
            if transaction['date']:
                trade_date = datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
                if trade_date >= cutoff:
                    filtered.append(transaction)
        
        return filtered
    
    def on_filter_change(self, event=None):
        """Handle filter change."""
        self.refresh()
    
    def update_statistics(self):
        """Update trade statistics."""
        try:
            stats = self.app.trade_tracker.get_trade_stats(self.app.current_collection_id)
            
            stats_text = (f"Total Transactions: {stats['total_transactions']} | "
                         f"Cards Given: {stats['total_cards_given']} | "
                         f"Cards Received: {stats['total_cards_received']} | "
                         f"Trade Partners: {stats['unique_partners']}")
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.stats_label.config(text="Error loading statistics")
            self.app.logger.error(f"Failed to load trade stats: {e}")
    
    def new_trade(self):
        """Open new trade dialog."""
        from frontend.dialogs.trade_dialog import TradeDialog
        
        dialog = TradeDialog(self.app.root, self.app)
        result = dialog.show()
        
        if result == 'recorded':
            self.refresh()
            # Also refresh inventory view if visible
            if hasattr(self.app, 'inventory_view'):
                self.app.inventory_view.refresh()
    
    def view_trade_details(self, event=None):
        """View details of selected trade."""
        selection = self.transactions_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a trade to view.")
            return
        
        item = selection[0]
        transaction_id = int(self.transactions_tree.item(item)['tags'][0])
        
        # Get detailed trade information
        self.show_trade_details_dialog(transaction_id)
    
    def show_trade_details_dialog(self, transaction_id):
        """Show detailed trade information."""
        # Get trade details
        trades = self.app.trade_tracker.get_trades(self.app.current_collection_id)
        transaction_trades = [t for t in trades if t.get('transaction_id') == transaction_id]
        
        if not transaction_trades:
            messagebox.showerror("Error", "Trade details not found.")
            return
        
        # Create details dialog
        details_dialog = tk.Toplevel(self.app.root)
        details_dialog.title(f"Trade Details - Transaction {transaction_id}")
        details_dialog.geometry("500x400")
        details_dialog.transient(self.app.root)
        details_dialog.grab_set()
        
        # Trade info
        first_trade = transaction_trades[0]
        info_frame = ttk.LabelFrame(details_dialog, text="Trade Information")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Partner: {first_trade['partner']}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(info_frame, text=f"Date: {first_trade['date'][:10]}").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Label(info_frame, text=f"Note: {first_trade['note']}").pack(anchor=tk.W, padx=10, pady=2)
        
        # Cards traded
        cards_frame = ttk.LabelFrame(details_dialog, text="Cards Traded")
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for incoming/outgoing
        notebook = ttk.Notebook(cards_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Outgoing cards
        out_frame = ttk.Frame(notebook)
        notebook.add(out_frame, text="Given Away")
        
        out_tree = ttk.Treeview(out_frame, columns=('quantity', 'set'), show='tree headings')
        out_tree.heading('#0', text='Card Name')
        out_tree.heading('quantity', text='Qty')
        out_tree.heading('set', text='Set')
        out_tree.pack(fill=tk.BOTH, expand=True)
        
        # Incoming cards
        in_frame = ttk.Frame(notebook)
        notebook.add(in_frame, text="Received")
        
        in_tree = ttk.Treeview(in_frame, columns=('quantity', 'set'), show='tree headings')
        in_tree.heading('#0', text='Card Name')
        in_tree.heading('quantity', text='Qty')
        in_tree.heading('set', text='Set')
        in_tree.pack(fill=tk.BOTH, expand=True)
        
        # Populate trees
        for trade in transaction_trades:
            if trade['quantity'] < 0:  # Outgoing
                out_tree.insert('', tk.END,
                    text=trade['card_name'],
                    values=(abs(trade['quantity']), trade['set_code'] or '')
                )
            else:  # Incoming
                in_tree.insert('', tk.END,
                    text=trade['card_name'],
                    values=(trade['quantity'], trade['set_code'] or '')
                )
        
        # Close button
        ttk.Button(details_dialog, text="Close", command=details_dialog.destroy).pack(pady=10)
    
    def delete_trade(self):
        """Delete selected trade."""
        selection = self.transactions_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a trade to delete.")
            return
        
        item = selection[0]
        transaction_id = int(self.transactions_tree.item(item)['tags'][0])
        partner = self.transactions_tree.item(item)['values'][0]
        
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the trade with {partner}?\n\n"
            f"This will remove all trade records for this transaction.\n"
            f"This action cannot be undone.",
            icon='warning'
        )
        
        if result:
            try:
                success = self.app.trade_tracker.delete_trade_transaction(transaction_id)
                if success:
                    self.refresh()
                    self.app.update_status(f"Deleted trade with {partner}")
                else:
                    messagebox.showerror("Error", "Failed to delete trade")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete trade: {e}")