from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import QAction, QMenu, QInputDialog, QLineEdit, QKeySequence

try:
    echo_mode_normal = QLineEdit.EchoMode.Normal
except AttributeError:
    echo_mode_normal = QLineEdit.Normal

import sys
import csv
import urllib.request

from .parseRemoteDeck import getRemoteDeck
from .parseAirtableDeck import getAirtableDeck

def syncDecks():
    col = mw.col
    config = mw.addonManager.getConfig(__name__)
    if not config:
        config = {"remote-decks": {}, "airtable-decks": {}}

    # Sync Google Sheets decks
    for deckKey in config.get("remote-decks", {}).keys():
        try:
            currentRemoteInfo = config["remote-decks"][deckKey]
            deckName = currentRemoteInfo["deckName"]
            remoteDeck = getRemoteDeck(currentRemoteInfo["url"])
            remoteDeck.deckName = deckName
            deck_id = get_or_create_deck(col, deckName)
            create_or_update_notes(col, remoteDeck, deck_id)
        except Exception as e:
            deckMessage = f"\nThe following Google Sheets deck failed to sync: {deckName}"
            showInfo(str(e) + deckMessage)
            raise

    # Sync Airtable decks
    for deckKey in config.get("airtable-decks", {}).keys():
        try:
            currentAirtableInfo = config["airtable-decks"][deckKey]
            deckName = currentAirtableInfo["deckName"]
            base_id = currentAirtableInfo["baseId"]
            table_name = currentAirtableInfo["tableName"]
            # Support both old 'apiKey' and new 'token' field names for backward compatibility
            api_key = currentAirtableInfo.get("token") or currentAirtableInfo.get("apiKey")
            view_name = currentAirtableInfo.get("viewName")
            
            remoteDeck = getAirtableDeck(base_id, table_name, api_key, view_name)
            remoteDeck.deckName = deckName
            deck_id = get_or_create_deck(col, deckName)
            create_or_update_notes(col, remoteDeck, deck_id)
        except Exception as e:
            deckMessage = f"\nThe following Airtable deck failed to sync: {deckName}"
            showInfo(str(e) + deckMessage)
            raise

    showInfo("Synchronization complete")

def get_or_create_deck(col, deckName):
    deck = col.decks.by_name(deckName)
    if deck is None:
        deck_id = col.decks.id(deckName)
    else:
        deck_id = deck["id"]
    return deck_id

def create_or_update_notes(col, remoteDeck, deck_id):
    # Dictionaries for existing notes
    existing_notes = {}
    existing_note_ids = {}

    # Fetch existing notes in the deck
    for nid in col.find_notes(f'deck:"{remoteDeck.deckName}"'):
        note = col.get_note(nid)
        # Determine the key based on available fields
        if "Text" in note:
            key = note["Text"]
        elif "Front" in note:
            key = note["Front"]
        else:
            continue  # Skip notes without 'Text' or 'Front' fields
        existing_notes[key] = note
        existing_note_ids[key] = nid

    # Set to keep track of keys from Google Sheets
    gs_keys = set()

    for question in remoteDeck.questions:
        card_type = question['type']
        fields = question['fields']
        tags = question.get('tags', [])

        if card_type == 'Cloze':
            key = fields['Text']
            gs_keys.add(key)
            extra = fields.get('Extra', '')

            if key in existing_notes:
                # Update existing note
                note = existing_notes[key]
                note["Text"] = key
                # Only set Extra field if it exists in the note type
                if "Extra" in note:
                    note["Extra"] = extra
                note.tags = tags
                note.flush()
            else:
                # Create new note
                model_name = "Cloze"
                model = col.models.by_name(model_name)
                if model is None:
                    showInfo("The 'Cloze' model does not exist. Please create a Cloze-type model in Anki.")
                    continue

                col.models.set_current(model)
                model['did'] = deck_id
                col.models.save(model)

                note = col.new_note(model)
                note["Text"] = key
                # Only set Extra field if it exists in the note type
                if "Extra" in note:
                    note["Extra"] = extra
                note.tags = tags
                col.add_note(note, deck_id)

        elif card_type == 'Basic':
            key = fields['Front']
            gs_keys.add(key)
            back = fields.get('Back', '')

            if key in existing_notes:
                # Update existing note
                note = existing_notes[key]
                if "Front" in note:
                    note["Front"] = key
                if "Back" in note:
                    note["Back"] = back
                note.tags = tags
                note.flush()
            else:
                # Create new note
                model_name = "Basic"
                model = col.models.by_name(model_name)
                if model is None:
                    showInfo("The 'Basic' model does not exist. Please create a Basic model in Anki.")
                    continue

                col.models.set_current(model)
                model['did'] = deck_id
                col.models.save(model)

                note = col.new_note(model)
                if "Front" in note:
                    note["Front"] = key
                if "Back" in note:
                    note["Back"] = back
                note.tags = tags
                col.add_note(note, deck_id)
        else:
            showInfo(f"Unknown card type '{card_type}' for card '{key}'. Skipping.")
            continue

    # Find notes that are in Anki but not in Google Sheets
    anki_keys = set(existing_notes.keys())
    notes_to_delete = anki_keys - gs_keys

    # Remove the corresponding notes
    if notes_to_delete:
        note_ids_to_delete = [existing_note_ids[key] for key in notes_to_delete]
        col.remove_notes(note_ids_to_delete)

    # Save changes
    col.save()

def addNewDeck():
    url, okPressed = QInputDialog.getText(
        mw, "Add New Remote Deck", "URL of published CSV:", echo_mode_normal, ""
    )
    if not okPressed or not url.strip():
        return

    url = url.strip()

    deckName, okPressed = QInputDialog.getText(
        mw, "Deck Name", "Enter the name of the deck:", echo_mode_normal, ""
    )
    if not okPressed or not deckName.strip():
        deckName = "Deck from CSV"

    if "output=csv" not in url:
        showInfo("The provided URL does not appear to be a published CSV from Google Sheets.")
        return

    config = mw.addonManager.getConfig(__name__)
    if not config:
        config = {"remote-decks": {}}

    if url in config["remote-decks"]:
        showInfo(f"The deck has already been added before: {url}")
        return

    try:
        deck = getRemoteDeck(url)
        deck.deckName = deckName
    except Exception as e:
        showInfo(f"Error fetching the remote deck:\n{e}")
        return

    config["remote-decks"][url] = {"url": url, "deckName": deckName}
    mw.addonManager.writeConfig(__name__, config)
    syncDecks()

def addNewAirtableDeck():
    # Get Base ID
    base_id, okPressed = QInputDialog.getText(
        mw, "Add New Airtable Deck", "Airtable Base ID (starts with 'app'):", echo_mode_normal, ""
    )
    if not okPressed or not base_id.strip():
        return
    
    base_id = base_id.strip()
    if not base_id.startswith('app'):
        showInfo("Base ID should start with 'app'. Please check your Base ID.")
        return

    # Get Table Name
    table_name, okPressed = QInputDialog.getText(
        mw, "Table Name", "Table name in Airtable:", echo_mode_normal, ""
    )
    if not okPressed or not table_name.strip():
        return
    
    table_name = table_name.strip()

    # Get Personal Access Token
    api_key, okPressed = QInputDialog.getText(
        mw, "Personal Access Token", "Airtable Personal Access Token (recommended: starts with 'pat'):", QLineEdit.EchoMode.Password, ""
    )
    if not okPressed or not api_key.strip():
        return
    
    api_key = api_key.strip()
    if not (api_key.startswith('key') or api_key.startswith('pat')):
        showInfo("Token should start with 'pat' (recommended) or 'key' (legacy). Please check your token.")
        return

    # Get View Name (optional)
    view_name, okPressed = QInputDialog.getText(
        mw, "View Name (Optional)", "View name (leave empty for default view):", echo_mode_normal, ""
    )
    if not okPressed:
        return
    
    view_name = view_name.strip() if view_name else None

    # Get Deck Name
    deckName, okPressed = QInputDialog.getText(
        mw, "Deck Name", "Enter the name of the deck:", echo_mode_normal, ""
    )
    if not okPressed or not deckName.strip():
        deckName = "Deck from Airtable"

    config = mw.addonManager.getConfig(__name__)
    if not config:
        config = {"remote-decks": {}, "airtable-decks": {}}
    
    if "airtable-decks" not in config:
        config["airtable-decks"] = {}

    # Create a unique key for this Airtable deck
    deck_key = f"{base_id}_{table_name}_{view_name or 'default'}"
    
    if deck_key in config["airtable-decks"]:
        showInfo(f"This Airtable deck has already been added: {deckName}")
        return

    try:
        deck = getAirtableDeck(base_id, table_name, api_key, view_name)
        deck.deckName = deckName
    except Exception as e:
        showInfo(f"Error fetching the Airtable deck:\n{e}")
        return

    config["airtable-decks"][deck_key] = {
        "baseId": base_id,
        "tableName": table_name,
        "token": api_key,
        "viewName": view_name,
        "deckName": deckName
    }
    
    mw.addonManager.writeConfig(__name__, config)
    syncDecks()

def removeRemoteDeck():
    # Get the add-on configuration
    config = mw.addonManager.getConfig(__name__)
    if not config:
        config = {"remote-decks": {}, "airtable-decks": {}}

    remoteDecks = config.get("remote-decks", {})
    airtableDecks = config.get("airtable-decks", {})

    # Get all deck names from both sources
    deckNames = []
    deck_sources = {}  # Map deck name to source type
    
    for key in remoteDecks:
        deck_name = remoteDecks[key]["deckName"]
        deckNames.append(f"{deck_name} (Google Sheets)")
        deck_sources[f"{deck_name} (Google Sheets)"] = ("sheets", key)
    
    for key in airtableDecks:
        deck_name = airtableDecks[key]["deckName"]
        deckNames.append(f"{deck_name} (Airtable)")
        deck_sources[f"{deck_name} (Airtable)"] = ("airtable", key)

    if len(deckNames) == 0:
        showInfo("There are currently no remote decks.")
        return

    # Ask the user to select a deck
    selection, okPressed = QInputDialog.getItem(
        mw,
        "Select a Deck to Unlink",
        "Select a deck to unlink:",
        deckNames,
        0,
        False
    )

    # Remove the deck
    if okPressed:
        source_type, deck_key = deck_sources[selection]
        if source_type == "sheets":
            del config["remote-decks"][deck_key]
        elif source_type == "airtable":
            del config["airtable-decks"][deck_key]

        # Save the updated configuration
        mw.addonManager.writeConfig(__name__, config)
        showInfo(f"The deck '{selection}' has been unlinked.")
