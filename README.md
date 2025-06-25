# MTG Collection Manager(Designed and built by AI, Super Alpha Build)

![image](https://github.com/user-attachments/assets/89b63b43-1040-4ea4-af79-4aa9d0780bb8)

A comprehensive desktop application for managing Magic: The Gathering card collections and deck building. Please note there might be a few things not working or 100% there. No gurantees use at your own risk. Proof of concept for me and trying to build something for myself.

- **Collection Management**: Organize cards in multiple named collections(only one collection at this time)
- **Deck Building**: Create and manage decks with commander and sideboard support
- **Scryfall Integration**: Powered by Scryfall API with offline caching
- **Import/Export**: Support for CSV and JSON formats
- **Trade Tracking**: Log and track card trades(Still being worked on)
- **Backup/Restore**: Local database backup and restore functionality(not fully tested)

### Prerequisites

- Python 3.8 or higher
- Windows 10/11 (primary support)
- Internet connection for initial card database download

🙏 Acknowledgments
- Scryfall for providing the comprehensive Magic: The Gathering API
- Wizards of the Coast for Magic: The Gathering
- Python Community for the excellent libraries used in this project

### Installation
**Clone the repository**:
- git clone
- cd mtgmanager/mtg_manager
- Create a folder called database under mtg_manager as well as a folder called assets under mtg_manager and create the following sub-folders under assets folder: cache,card_images,set_icons,styles
- Create a virtual environment(python -m venv venv(or .env or .venv or env)
- Activate virtual environment(venv\scripts\activate(windows) if you called the virtual environment venv
- pip install -r requirements.txt
- python main.py

### First-Time Setup

- Download Card Database: Go to Tools > Bulk Download to get the latest card data
- Create Collection: Start adding cards to your inventory
- Build Decks: Create and manage your deck lists

📖 Usage Guide

### Collection Management
- Add Cards: Use the search function or quick-add from toolbar
- Edit Inventory: Double-click items to edit quantity, condition, foil status
- Filter & Search: Find cards by name, set, color, or foil status
- Import/Export: Use CSV files to bulk import/export your collection
### Deck Building
- Create Decks: Support for all formats including Commander
- Manage Cards: Move cards between main deck, sideboard, and commander
- Statistics: View mana curves, color distribution, and deck analysis
- Export Decks: Export to text format for online platforms
### Data Management
- Backup: Create database backups for safety
- Import: Import from various formats
- Offline Mode: Works completely offline after initial setup
