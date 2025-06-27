# frontend/dialogs/model_selection_dialog.py
"""
Model selection dialog for Ollama vision models.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

class ModelSelectionDialog:
    """Dialog for selecting Ollama vision models."""
    
    def __init__(self, parent, ollama_client):
        """Initialize model selection dialog."""
        self.parent = parent
        self.ollama_client = ollama_client
        self.selected_model = None
        self.result = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the model selection dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Vision Model")
        self.dialog.geometry("600x500")  # Made taller
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)  # Allow resizing
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        self.setup_ui()
        
        # Load available models
        self.refresh_models()
        
        # Bind close event
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def setup_ui(self):
        """Set up the dialog UI with proper layout."""
        # Main container with proper expansion
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configure main_frame grid weights
        main_frame.grid_rowconfigure(2, weight=1)  # Model list gets extra space
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = ttk.Label(main_frame, 
                                 text="Select Ollama Vision Model for Card Recognition",
                                 font=('TkDefaultFont', 12, 'bold'))
        header_label.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        
        # Ollama status
        self.status_frame = ttk.LabelFrame(main_frame, text="Ollama Status")
        self.status_frame.grid(row=1, column=0, sticky='ew', pady=(0, 20))
        
        self.status_label = ttk.Label(self.status_frame, text="Checking Ollama...")
        self.status_label.pack(padx=10, pady=10)
        
        # Model selection frame
        model_frame = ttk.LabelFrame(main_frame, text="Available Vision Models")
        model_frame.grid(row=2, column=0, sticky='nsew', pady=(0, 15))
        
        # Configure model_frame grid weights
        model_frame.grid_rowconfigure(0, weight=1)
        model_frame.grid_columnconfigure(0, weight=1)
        
        # Model list with fixed height
        list_frame = ttk.Frame(model_frame)
        list_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.model_listbox = tk.Listbox(list_frame, height=8)  # Fixed height
        model_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.model_listbox.yview)
        self.model_listbox.configure(yscrollcommand=model_scrollbar.set)
        
        self.model_listbox.grid(row=0, column=0, sticky='nsew')
        model_scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.model_listbox.bind('<<ListboxSelect>>', self.on_model_select)
        self.model_listbox.bind('<Double-1>', self.select_model)
        
        # Model info with fixed height and wrapping
        info_frame = ttk.Frame(model_frame)
        info_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))
        
        # FIX START: Removed height=3 from the ttk.Label to allow it to expand vertically
        self.info_label = ttk.Label(info_frame, text="Select a model to see details", 
                                     wraplength=550, justify=tk.LEFT) 
        # FIX END
        self.info_label.pack(fill=tk.X)
        
        # Buttons frame - FIXED: Always at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky='ew', pady=(15, 0))
        
        self.refresh_btn = ttk.Button(button_frame, text="Refresh Models", 
                                      command=self.refresh_models)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_btn = ttk.Button(button_frame, text="Select Model", 
                                     command=self.select_model, state=tk.DISABLED)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        self.cancel_btn.pack(side=tk.RIGHT)
        
        # Download info frame - FIXED: Separate frame at bottom
        info_frame = ttk.LabelFrame(main_frame, text="Need Models?")
        info_frame.grid(row=4, column=0, sticky='ew', pady=(15, 0))
        
        info_text = ("Don't see vision models? Download them with:\n"
                     "ollama pull llava\n"
                     "ollama pull moondream\n"
                     "ollama pull bakllava")
        
        ttk.Label(info_frame, text=info_text, font=('Courier', 9), 
                  justify=tk.LEFT).pack(padx=10, pady=10)
    
    def refresh_models(self):
        """Refresh the list of available models."""
        self.status_label.config(text="Checking Ollama connection...")
        self.model_listbox.delete(0, tk.END)
        
        # Check if Ollama is available
        if not self.ollama_client.check_availability():
            self.status_label.config(text="❌ Ollama not running or not accessible")
            self.model_listbox.insert(tk.END, "Ollama not available")
            self.model_listbox.insert(tk.END, "Make sure Ollama is running:")
            self.model_listbox.insert(tk.END, "1. Install Ollama from ollama.ai")
            self.model_listbox.insert(tk.END, "2. Start Ollama service")
            self.model_listbox.insert(tk.END, "3. Download vision models")
            return
        
        # Get available models
        models = self.ollama_client.refresh_models()
        
        if models:
            self.status_label.config(text="✅ Ollama connected - Found vision models")
            for model in models:
                self.model_listbox.insert(tk.END, model)
        else:
            self.status_label.config(text="⚠️ Ollama connected - No vision models found")
            self.model_listbox.insert(tk.END, "No vision models available")
            self.model_listbox.insert(tk.END, "Download models with:")
            self.model_listbox.insert(tk.END, "ollama pull llava")
            self.model_listbox.insert(tk.END, "ollama pull moondream")
    
    def on_model_select(self, event=None):
        """Handle model selection."""
        selection = self.model_listbox.curselection()
        if selection:
            model_name = self.model_listbox.get(selection[0])
            
            # Check if it's an actual model (not a message)
            if model_name in self.ollama_client.available_models:
                self.selected_model = model_name
                self.select_btn.config(state=tk.NORMAL)
                
                # Show model info
                info_text = (f"Selected: {model_name}\n\n"
                             f"This model will analyze card images and extract "
                             f"card names and details for your collection.")
                self.info_label.config(text=info_text)
            else:
                self.selected_model = None
                self.select_btn.config(state=tk.DISABLED)
                self.info_label.config(text="Select a valid vision model")
    
    def select_model(self, event=None):
        """Select the chosen model."""
        if self.selected_model:
            success = self.ollama_client.set_model(self.selected_model)
            if success:
                self.result = self.selected_model
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", f"Failed to set model: {self.selected_model}")
    
    def cancel(self):
        """Cancel model selection."""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[str]:
        """Show the dialog and return selected model."""
        self.dialog.wait_window()
        return self.result