# frontend/views/ocr_scanner.py
"""
Ollama Vision Scanner view for MTG Collection Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import cv2
import numpy as np
from PIL import Image, ImageTk
from typing import Optional, List
import os

class VisionScannerWindow:
    """Vision Scanner window for card recognition using Ollama."""
    
    def __init__(self, parent, app):
        """Initialize vision scanner window."""
        self.parent = parent
        self.app = app
        self.window = None
        self.camera = None
        self.is_scanning = False
        self.current_frame = None
        
        # Initialize Ollama client
        try:
            from backend.ai.ollama_client import OllamaClient
            self.ollama_client = OllamaClient()
            self.app.logger.info("Ollama client initialized")
        except Exception as e:
            self.app.logger.error(f"Failed to initialize Ollama client: {e}")
            self.ollama_client = None
        
        self.create_window()
    
    def create_window(self):
        """Create the vision scanner window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("AI Vision Card Scanner")
        self.window.geometry("900x700")
        self.window.transient(self.parent)
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"900x700+{x}+{y}")
        
        self.setup_ui()
        
        # Show model selection dialog
        if self.ollama_client and self.ollama_client.is_available:
            self.select_model()
        else:
            messagebox.showerror("Ollama Not Available", 
                                 "Ollama is not running or not installed.\n\n"
                                 "Please install Ollama from ollama.ai and start the service.")
        
        # Bind close event
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def select_model(self):
        """Show model selection dialog."""
        from frontend.dialogs.model_selection_dialog import ModelSelectionDialog
        
        dialog = ModelSelectionDialog(self.window, self.ollama_client)
        selected_model = dialog.show()
        
        if selected_model:
            self.model_label.config(text=f"Model: {selected_model}")
            self.status_var.set("Ready - Model selected")
        else:
            self.model_label.config(text="No model selected")
            self.status_var.set("No model selected - Choose a model to continue")
    
    def setup_ui(self):
        """Set up the vision scanner UI."""
        # Main container
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="AI Vision Scanner Controls")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Model selection
        model_frame = ttk.Frame(control_frame)
        model_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.model_label = ttk.Label(model_frame, text="No model selected", 
                                     font=('TkDefaultFont', 10, 'bold'))
        self.model_label.pack(side=tk.LEFT)
        
        ttk.Button(model_frame, text="Change Model", 
                   command=self.select_model).pack(side=tk.RIGHT)
        
        # Camera controls
        camera_frame = ttk.Frame(control_frame)
        camera_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_camera_btn = ttk.Button(camera_frame, text="Start Camera", 
                                           command=self.start_camera)
        self.start_camera_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_camera_btn = ttk.Button(camera_frame, text="Stop Camera", 
                                          command=self.stop_camera, state=tk.DISABLED)
        self.stop_camera_btn.pack(side=tk.LEFT, padx=5)
        
        self.capture_btn = ttk.Button(camera_frame, text="Capture & Analyze", 
                                       command=self.capture_and_analyze, state=tk.DISABLED)
        self.capture_btn.pack(side=tk.LEFT, padx=5)
        
        # File input option
        ttk.Separator(camera_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.load_file_btn = ttk.Button(camera_frame, text="Load Image File", 
                                        command=self.load_image_file)
        self.load_file_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Camera view
        camera_frame = ttk.LabelFrame(content_frame, text="Camera View")
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.camera_label = ttk.Label(camera_frame, text="No camera feed", 
                                       width=50, anchor=tk.CENTER)
        self.camera_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results panel
        results_frame = ttk.LabelFrame(content_frame, text="AI Analysis Results")
        results_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Analysis results
        analysis_frame = ttk.LabelFrame(results_frame, text="Card Analysis")
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.analysis_text = tk.Text(analysis_frame, width=35, height=12, wrap=tk.WORD)
        analysis_scrollbar = ttk.Scrollbar(analysis_frame, orient=tk.VERTICAL, command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=analysis_scrollbar.set)
        self.analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        analysis_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Card matches
        matches_frame = ttk.LabelFrame(results_frame, text="Database Matches")
        matches_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.matches_listbox = tk.Listbox(matches_frame, height=8)
        matches_scrollbar = ttk.Scrollbar(matches_frame, orient=tk.VERTICAL, command=self.matches_listbox.yview)
        self.matches_listbox.configure(yscrollcommand=matches_scrollbar.set)
        self.matches_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        matches_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.matches_listbox.bind('<Double-1>', self.add_selected_match)
        
        # Action buttons
        action_frame = ttk.Frame(results_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.add_to_inventory_btn = ttk.Button(action_frame, text="Add to Inventory", 
                                               command=self.add_selected_match, state=tk.DISABLED)
        self.add_to_inventory_btn.pack(fill=tk.X, pady=2)
        
        self.clear_results_btn = ttk.Button(action_frame, text="Clear Results", 
                                            command=self.clear_results)
        self.clear_results_btn.pack(fill=tk.X, pady=2)
    
    def start_camera(self):
        """Start camera feed with improved error handling."""
        try:
            # Try different camera backends and indices
            camera_backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
            camera_indices = [0, 1, 2]  # Try multiple camera indices
            
            self.camera = None
            
            for backend in camera_backends:
                for index in camera_indices:
                    try:
                        self.app.logger.debug(f"Trying camera index {index} with backend {backend}")
                        test_camera = cv2.VideoCapture(index, backend)
                        
                        if test_camera.isOpened():
                            # Test if we can actually read a frame
                            ret, frame = test_camera.read()
                            if ret and frame is not None:
                                self.camera = test_camera
                                self.app.logger.info(f"Camera opened successfully: index {index}, backend {backend}")
                                break
                            else:
                                test_camera.release()
                        else:
                            test_camera.release()
                            
                    except Exception as e:
                        self.app.logger.debug(f"Camera index {index} with backend {backend} failed: {e}")
                        continue
                
                if self.camera:
                    break
            
            if not self.camera or not self.camera.isOpened():
                messagebox.showerror("Camera Error", 
                                     "Could not open camera. Please check:\n"
                                     "• Camera is connected and not in use by another app\n"
                                     "• Camera permissions are granted\n"
                                     "• Try closing other camera applications")
                return
            
            # Configure camera settings
            try:
                # Set reasonable resolution
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                
                # Set buffer size to reduce latency
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
            except Exception as e:
                self.app.logger.warning(f"Could not set camera properties: {e}")
            
            # Test frame capture
            ret, test_frame = self.camera.read()
            if not ret or test_frame is None:
                self.camera.release()
                messagebox.showerror("Camera Error", "Camera opened but cannot capture frames")
                return
            
            self.is_scanning = True
            self.start_camera_btn.config(state=tk.DISABLED)
            self.stop_camera_btn.config(state=tk.NORMAL)
            self.capture_btn.config(state=tk.NORMAL)
            self.status_var.set("Camera started")
            
            # Start the camera feed update loop
            self.update_camera_feed()
            
        except Exception as e:
            self.app.logger.error(f"Failed to start camera: {e}")
            messagebox.showerror("Error", f"Failed to start camera: {e}")
    
    def stop_camera(self):
        """Stop camera feed."""
        self.is_scanning = False
        if self.camera:
            try:
                self.camera.release()
            except Exception as e:
                self.app.logger.error(f"Error releasing camera: {e}")
            finally:
                self.camera = None
        
        # Release any OpenCV resources
        cv2.destroyAllWindows()
        
        self.start_camera_btn.config(state=tk.NORMAL)
        self.stop_camera_btn.config(state=tk.DISABLED)
        self.capture_btn.config(state=tk.DISABLED)
        self.camera_label.config(image="", text="Camera stopped")
        self.status_var.set("Camera stopped")
    
    def update_camera_feed(self):
        """Update camera feed display with error handling."""
        if not self.is_scanning or not self.camera:
            return
        
        try:
            ret, frame = self.camera.read()
            if ret and frame is not None:
                self.current_frame = frame.copy()
                
                # Convert to RGB for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize for display
                height, width = frame_rgb.shape[:2]
                max_width = 400
                if width > max_width:
                    scale = max_width / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame_rgb = cv2.resize(frame_rgb, (new_width, new_height))
                
                # Convert to PhotoImage
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)
                
                self.camera_label.config(image=photo, text="")
                self.camera_label.image = photo
                
            else:
                # Handle frame read failure
                self.app.logger.warning("Failed to read camera frame")
                
        except Exception as e:
            self.app.logger.error(f"Error updating camera feed: {e}")
            # Don't stop the feed for minor errors, just log them
            
        # Schedule next update
        if self.is_scanning:
            self.window.after(50, self.update_camera_feed)  # Slightly slower update rate
    
    def capture_and_analyze(self):
        """Capture current frame and analyze with Ollama."""
        if self.current_frame is None:
            messagebox.showwarning("Warning", "No frame to capture")
            return
        
        if not self.ollama_client or not self.ollama_client.selected_model:
            messagebox.showerror("Error", "No AI model selected")
            return
        
        self.status_var.set("Analyzing with AI...")
        
        def analyze_thread():
            try:
                # Analyze card with Ollama
                card_data = self.ollama_client.analyze_card_image(self.current_frame)
                
                # Update UI in main thread
                self.window.after(0, lambda: self.process_analysis_result(card_data))
                
            except Exception as e:
                self.window.after(0, lambda: self.handle_analysis_error(e))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def load_image_file(self):
        """Load and scan an image file."""
        if not self.ollama_client or not self.ollama_client.selected_model:
            messagebox.showerror("Error", "No AI model selected")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Load image
            image = cv2.imread(file_path)
            if image is None:
                messagebox.showerror("Error", "Could not load image file")
                return
            
            self.current_frame = image
            
            # Display image
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width = image_rgb.shape[:2]
            max_width = 400
            if width > max_width:
                scale = max_width / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                image_rgb = cv2.resize(image_rgb, (new_width, new_height))
            
            photo = ImageTk.PhotoImage(Image.fromarray(image_rgb))
            self.camera_label.config(image=photo, text="")
            self.camera_label.image = photo
            
            self.status_var.set("Analyzing image...")
            
            def analyze_thread():
                try:
                    card_data = self.ollama_client.analyze_card_image(image)
                    self.window.after(0, lambda: self.process_analysis_result(card_data))
                except Exception as e:
                    self.window.after(0, lambda: self.handle_analysis_error(e))
            
            threading.Thread(target=analyze_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
    
    def process_analysis_result(self, card_data: Optional[dict]):
        """Process AI analysis result."""
        if not card_data:
            self.status_var.set("Analysis failed")
            self.analysis_text.delete('1.0', tk.END)
            self.analysis_text.insert('1.0', "AI analysis failed or returned no data.")
            self.matches_listbox.delete(0, tk.END)
            self.add_to_inventory_btn.config(state=tk.DISABLED)
            return
        
        # Display analysis results
        self.analysis_text.delete('1.0', tk.END)
        
        if 'name' in card_data:
            analysis_text = f"Card Name: {card_data['name']}\n\n"
            
            if 'mana_cost' in card_data:
                analysis_text += f"Mana Cost: {card_data['mana_cost']}\n"
            
            if 'type_line' in card_data:
                analysis_text += f"Type: {card_data['type_line']}\n"
            
            if 'power' in card_data and 'toughness' in card_data:
                analysis_text += f"P/T: {card_data['power']}/{card_data['toughness']}\n"
            
            if 'oracle_text' in card_data:
                analysis_text += f"\nText:\n{card_data['oracle_text']}\n"
            
            if 'set_code' in card_data:
                analysis_text += f"Set: {card_data['set_code'].upper()}\n"

            if 'collector_number' in card_data:
                analysis_text += f"Collector #: {card_data['collector_number']}\n"

            if 'confidence' in card_data:
                analysis_text += f"\nConfidence: {card_data['confidence']}/10"
            
            self.analysis_text.insert('1.0', analysis_text)
            self.status_var.set(f"Analyzed: {card_data['name']}")
            
            # Search for matching cards
            self.search_matching_cards(card_data) # Pass full card_data for better search
        else:
            # Show raw response if no structured data
            raw_text = card_data.get('raw_response', 'Unknown analysis result')
            self.analysis_text.insert('1.0', f"Raw AI Response:\n{raw_text}")
            self.status_var.set("Analysis completed - check results")
            self.matches_listbox.delete(0, tk.END)
            self.add_to_inventory_btn.config(state=tk.DISABLED)
    
    def search_matching_cards(self, card_data: dict):
        """Search for cards matching the detected name and other attributes."""
        def search_thread():
            try:
                card_name = card_data.get('name', '')
                set_code = card_data.get('set_code', '')
                collector_number = card_data.get('collector_number', '')

                query_parts = []
                if card_name:
                    query_parts.append(f'name:"{card_name}"')
                if set_code:
                    query_parts.append(f'set:"{set_code}"')
                if collector_number:
                    query_parts.append(f'cn:"{collector_number}"')
                
                search_query = " ".join(query_parts) if query_parts else card_name

                results = []
                if search_query:
                    # Try exact match first
                    exact_match_query = f'!"{card_name}"' if card_name else search_query
                    exact_results = self.app.scryfall_client.search_cards_in_cache(exact_match_query, limit=1)
                    if exact_results:
                        results = exact_results
                    else:
                        # Fallback to broader search if exact match isn't found
                        api_result = self.app.scryfall_client.search_cards(search_query)
                        if api_result and 'data' in api_result:
                            results = api_result['data'][:10] # Limit to top 10 results
                
                self.window.after(0, lambda: self.display_card_matches(results))
                
            except Exception as e:
                self.window.after(0, lambda: messagebox.showerror("Error", f"Search failed: {e}"))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def display_card_matches(self, cards: List[dict]):
        """Display matching cards in the listbox."""
        self.matches_listbox.delete(0, tk.END)
        self.card_matches = cards
        
        if not cards:
            self.matches_listbox.insert(tk.END, "No matching cards found")
            self.add_to_inventory_btn.config(state=tk.DISABLED)
            return
        
        for card in cards:
            display_text = f"{card['name']} ({card.get('set', '').upper()})"
            if card.get('collector_number'):
                display_text += f" #{card['collector_number']}"
            self.matches_listbox.insert(tk.END, display_text)
        
        self.add_to_inventory_btn.config(state=tk.NORMAL)
    
    def add_selected_match(self, event=None):
        """Add selected card match to inventory."""
        selection = self.matches_listbox.curselection()
        if not selection or not hasattr(self, 'card_matches') or not self.card_matches:
            return
        
        card_index = selection[0]
        if card_index >= len(self.card_matches):
            return
        
        selected_card = self.card_matches[card_index]
        
        # Open add to inventory dialog
        self.open_add_to_inventory_dialog(selected_card)
    
    def open_add_to_inventory_dialog(self, card_data: dict):
        """Open add to inventory dialog for selected card."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add to Inventory")
        dialog.geometry("350x250")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"350x250+{x}+{y}")
        
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Card info
        ttk.Label(main_frame, text=f"Add '{card_data['name']}' to inventory:", 
                  font=('TkDefaultFont', 10, 'bold')).pack(pady=(0, 15))
        
        # Quantity
        quantity_frame = ttk.Frame(main_frame)
        quantity_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(quantity_frame, text="Quantity:").pack(side=tk.LEFT)
        quantity_var = tk.IntVar(value=1)
        ttk.Spinbox(quantity_frame, from_=1, to=100, textvariable=quantity_var, width=10).pack(side=tk.RIGHT)
        
        # Foil
        foil_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Foil", variable=foil_var).pack(anchor=tk.W, pady=5)
        
        # Condition
        condition_frame = ttk.Frame(main_frame)
        condition_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(condition_frame, text="Condition:").pack(side=tk.LEFT)
        condition_var = tk.StringVar(value="Near Mint")
        ttk.Combobox(condition_frame, textvariable=condition_var,
                     values=["Mint", "Near Mint", "Lightly Played", "Moderately Played", "Heavily Played", "Damaged"],
                     state="readonly", width=15).pack(side=tk.RIGHT)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def add_card():
            try:
                success = self.app.inventory_manager.add_card_to_inventory(
                    self.app.current_collection_id,
                    card_data['name'],
                    quantity_var.get(),
                    foil_var.get(),
                    condition_var.get()
                )
                
                if success:
                    dialog.destroy()
                    self.app.inventory_view.refresh()
                    self.status_var.set(f"Added {quantity_var.get()}x {card_data['name']} to inventory")
                else:
                    messagebox.showerror("Error", "Failed to add card to inventory")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add card: {e}")
        
        ttk.Button(button_frame, text="Add", command=add_card).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
    
    def handle_analysis_error(self, error: Exception):
        """Handle AI analysis error."""
        self.status_var.set("Analysis failed")
        messagebox.showerror("Analysis Error", f"AI analysis failed: {error}")
        self.app.logger.error(f"AI analysis error: {error}")
    
    def clear_results(self):
        """Clear scan results."""
        self.analysis_text.delete('1.0', tk.END)
        self.matches_listbox.delete(0, tk.END)
        self.add_to_inventory_btn.config(state=tk.DISABLED)
        self.status_var.set("Results cleared")
    
    def close_window(self):
        """Close the scanner window."""
        self.stop_camera()
        self.window.destroy()