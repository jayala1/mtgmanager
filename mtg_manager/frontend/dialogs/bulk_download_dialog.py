# frontend/dialogs/bulk_download_dialog.py
"""
Bulk download dialog for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, Any, List

class BulkDownloadDialog:
    """Dialog for downloading bulk card data from Scryfall."""
    
    def __init__(self, parent, scryfall_client):
        """Initialize bulk download dialog."""
        self.parent = parent
        self.scryfall_client = scryfall_client
        self.download_thread = None
        self.is_downloading = False
        
        self.create_dialog()
        self.load_bulk_data_info()
    
    def create_dialog(self):
        """Create the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Download Card Database")
        self.dialog.geometry("500x600")  # Made taller to accommodate all content
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Make dialog non-resizable during download
        self.dialog.resizable(False, False)
        
        # Main container with scrollbar
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="Bulk Data Download")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = (
            "This will download the complete Magic: The Gathering card database\n"
            "from Scryfall for offline use. The download is approximately 50-100 MB\n"
            "and contains information for all Magic cards.\n\n"
            "This process may take several minutes depending on your internet connection."
        )
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Bulk data options frame
        self.options_frame = ttk.LabelFrame(main_frame, text="Download Options")
        self.options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.bulk_type_var = tk.StringVar(value="default_cards")
        
        # Loading label for options
        self.loading_label = ttk.Label(self.options_frame, text="Loading available downloads...")
        self.loading_label.pack(padx=10, pady=10)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Download Progress")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(progress_frame, text="Ready to download")
        self.status_label.pack(pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=400
        )
        self.progress_bar.pack(pady=5, padx=10, fill=tk.X)
        
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(pady=2)
        
        # Buttons frame - FIXED: Create this last and keep it at bottom
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)
        
        self.download_button = ttk.Button(
            self.button_frame, 
            text="Start Download", 
            command=self.start_download,
            state=tk.DISABLED  # Disabled until options are loaded
        )
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(
            self.button_frame, 
            text="Cancel", 
            command=self.cancel_download,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        self.close_button = ttk.Button(
            self.button_frame, 
            text="Close", 
            command=self.close_dialog
        )
        self.close_button.pack(side=tk.RIGHT, padx=5)
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def load_bulk_data_info(self):
        """Load available bulk data information."""
        def load_info():
            try:
                bulk_info = self.scryfall_client.get_bulk_data_info()
                self.dialog.after(0, lambda: self.display_bulk_options(bulk_info))
            except Exception as e:
                self.dialog.after(0, lambda: self.handle_load_error(str(e)))
        
        # Load in background thread
        threading.Thread(target=load_info, daemon=True).start()
    
    def handle_load_error(self, error_message: str):
        """Handle error loading bulk data info."""
        self.loading_label.config(text=f"Error loading options: {error_message}")
        messagebox.showerror("Error", f"Failed to load bulk data info: {error_message}")
    
    def display_bulk_options(self, bulk_info: Dict[str, Any]):
        """Display available bulk data options."""
        if not bulk_info or 'data' not in bulk_info:
            self.loading_label.config(text="Failed to load download options")
            return
        
        # Remove loading label
        self.loading_label.destroy()
        
        # Create radio buttons for each bulk data type
        for i, bulk_item in enumerate(bulk_info['data']):
            bulk_type = bulk_item.get('type', '')
            name = bulk_item.get('name', bulk_type)
            description = bulk_item.get('description', '')
            size_mb = bulk_item.get('size', 0) / (1024 * 1024)
            
            # Create frame for this option
            option_frame = ttk.Frame(self.options_frame)
            option_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Radio button
            radio = ttk.Radiobutton(
                option_frame,
                text=f"{name} (~{size_mb:.1f} MB)",
                variable=self.bulk_type_var,
                value=bulk_type
            )
            radio.pack(anchor=tk.W)
            
            # Description
            if description:
                desc_label = ttk.Label(
                    option_frame, 
                    text=f"  {description}", 
                    font=('TkDefaultFont', 8),
                    foreground='gray'
                )
                desc_label.pack(anchor=tk.W, padx=20)
        
        # Enable the download button now that options are loaded
        self.download_button.config(state=tk.NORMAL)
        self.status_label.config(text="Ready to download")
    
    def start_download(self):
        """Start the bulk data download."""
        if self.is_downloading:
            return
        
        bulk_type = self.bulk_type_var.get()
        if not bulk_type:
            messagebox.showwarning("Warning", "Please select a download option.")
            return
        
        self.is_downloading = True
        self.download_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.close_button.config(state=tk.DISABLED)
        
        # Reset progress
        self.progress_var.set(0)
        self.progress_label.config(text="")
        
        # Start download in background thread
        self.download_thread = threading.Thread(
            target=self._download_worker, 
            args=(bulk_type,),
            daemon=True
        )
        self.download_thread.start()
    
    def _download_worker(self, bulk_type: str):
        """Worker thread for downloading bulk data."""
        try:
            # Update status
            self.dialog.after(0, lambda: self.status_label.config(text="Starting download..."))
            
            # Download with progress callback
            def progress_callback(downloaded: int, total: int):
                if total > 0:
                    percent = (downloaded / total) * 50  # First 50% for download
                    self.dialog.after(0, lambda: self.update_progress(
                        percent, f"Downloading: {downloaded / (1024*1024):.1f} / {total / (1024*1024):.1f} MB"
                    ))
            
            bulk_file = self.scryfall_client.download_bulk_data_with_progress(
                bulk_type, progress_callback
            )
            
            if not bulk_file:
                self.dialog.after(0, lambda: self.download_failed("Download failed"))
                return
            
            # Parse the downloaded file
            self.dialog.after(0, lambda: self.status_label.config(text="Processing cards..."))
            
            def parse_progress_callback(processed: int, total: int):
                if total > 0:
                    percent = 50 + (processed / total) * 50  # Second 50% for parsing
                    self.dialog.after(0, lambda: self.update_progress(
                        percent, f"Processing: {processed:,} / {total:,} cards"
                    ))
            
            success = self.scryfall_client.parse_bulk_data_file(
                bulk_file, parse_progress_callback
            )
            
            if success:
                self.dialog.after(0, self.download_completed)
            else:
                self.dialog.after(0, lambda: self.download_failed("Failed to process card data"))
                
        except Exception as e:
            self.dialog.after(0, lambda: self.download_failed(f"Download error: {e}"))
    
    def update_progress(self, percent: float, status_text: str):
        """Update progress bar and status."""
        self.progress_var.set(percent)
        self.progress_label.config(text=status_text)
        self.dialog.update_idletasks()
    
    def download_completed(self):
        """Handle successful download completion."""
        self.is_downloading = False
        self.progress_var.set(100)
        self.status_label.config(text="Download completed successfully!")
        self.progress_label.config(text="Card database is now available for offline use.")
        
        self.download_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.close_button.config(state=tk.NORMAL)
        
        messagebox.showinfo(
            "Success", 
            "Card database downloaded successfully!\n\n"
            "You can now use the application offline and search will be much faster."
        )
    
    def download_failed(self, error_message: str):
        """Handle download failure."""
        self.is_downloading = False
        self.status_label.config(text="Download failed")
        self.progress_label.config(text=error_message)
        
        self.download_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.close_button.config(state=tk.NORMAL)
        
        messagebox.showerror("Download Failed", error_message)
    
    def cancel_download(self):
        """Cancel the current download."""
        if self.is_downloading:
            self.is_downloading = False
            self.status_label.config(text="Cancelling download...")
            self.cancel_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.NORMAL)
            # Note: We can't actually stop the thread, but we can ignore its results
    
    def close_dialog(self):
        """Close the dialog."""
        if self.is_downloading:
            result = messagebox.askyesno(
                "Download in Progress",
                "A download is currently in progress. Are you sure you want to close?"
            )
            if not result:
                return
        
        self.dialog.destroy()
    
    def on_window_close(self):
        """Handle window close event."""
        self.close_dialog()