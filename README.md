# Sheets2Anki

**Sheets2Anki** is an Anki add-on that synchronizes your Anki decks with Google Sheets CSV or Airtable databases. Your remote data source serves as the source of truth: when you sync, cards are created, updated, or removed in your Anki deck to reflect the remote content. This add-on is currently in **beta**, so features and behavior may still change.

## Features

- **Multiple Data Sources:**  
  Support for both Google Sheets (published as CSV) and Airtable databases.
- **Google Sheets as Source of Truth:**  
  Your published Google Sheet determines the cards present in Anki.  
- **Airtable Integration:**  
  Connect directly to Airtable bases using the API to sync your flashcards.
- **Supports Both Basic and Cloze Cards:**  
  Automatically detects Cloze formatting (`{{c1::...}}`) in the question field for Cloze cards. Other questions become Basic cards.  
- **Automatic Tag Assignment:**  
  If you have a `tags` column/field in your data source, those tags will be assigned to the cards in Anki.  
- **Deck Maintenance:**  
  - **Removed in Source → Removed in Anki:** If a card disappears from the data source, it is removed from Anki on the next sync.
  - **Removed in Anki → Not Removed in Source:** There is **no reverse sync**. Deleting a card in Anki does not affect the data source; the card may reappear if you sync again unless it's removed from the source.
  
**Important:** This add-on is in **beta** and currently supports only Basic and Cloze note types. Future updates may improve or extend functionality.

## No Reverse Sync & Deck Disconnection

- **No Reverse Sync:**  
  All changes flow from your data source (Google Sheets or Airtable) to Anki. If you delete or modify a card in Anki, it will not update the source. To permanently remove a card, remove it from the source before syncing again.
  
- **Syncing vs. Disconnecting a Remote Deck:**
  - **Sync Once and Disconnect:**  
    You can sync a deck once, and then if you prefer to manage cards locally without further remote updates, go to `Tools > Manage sheets2anki Decks > Disconnect a Remote Deck`. This "unlinks" Anki from the data source. The local deck remains and can be edited freely in Anki as a normal deck.
  - **Continuous Syncing:**  
    Alternatively, you can keep the deck connected and continue updating your data source. Upon each sync, Anki updates to match the source. If you want a card gone, you must remove it from the source, as deletions in Anki alone won't persist after a resync.

## Google Sheets Setup

Use this [example Google Sheets document](https://docs.google.com/spreadsheets/d/1S97fZkuw1DctJhBB1yaiWiSh5grmNmY9Gp8KVPCpMfU/edit?usp=sharing) as a starting template.  
![imagen](https://github.com/user-attachments/assets/a030ddd0-5dae-483b-bde2-32f20ed0e245)
- Just copy and paste: `question`, `answer`, and `tags` columns as needed.
- Add Cloze-formatted questions (e.g., `{{c1::essential}}`) for Cloze cards.
- After finalizing, publish the sheet as a CSV (File > Publish to the Web) and copy the CSV URL.

## Airtable Setup

For Airtable integration:

1. **Create an Airtable Base** with a table containing your flashcard data.

2. **Required Fields** (case-insensitive):
   - `question`, `front`, or `text`: The front/question side of the card
   - `answer`, `back`, or `extra`: The back/answer side of the card  
   - `tags` (optional): Comma-separated tags or array of tags

3. **Get Your API Credentials:**
   - **Base ID:** Found in your Airtable base URL (starts with `app...`)
   - **API Key:** Create a Personal Access Token in your Airtable account settings (starts with `pat...`) or use legacy API key (starts with `key...`)
   - **Table Name:** The name of your table containing the flashcard data
   - **View Name:** (Optional) Specify a view to filter which records to sync

4. **Example Airtable Structure:**
   ```
   | Question | Answer | Tags |
   |----------|--------|------|
   | What is the capital of France? | Paris | geography, capitals |
   | {{c1::Berlin}} is the capital of Germany | | geography, cloze |
   ```

## Installation

1. **Download the `.ankiaddon` File:**
   - Go to the [Releases](https://github.com/your-username/sheets2anki/releases) page of this repository.
   - Download the latest `.ankiaddon`.

2. **Install in Anki:**
   - In Anki, go to `Tools > Add-ons > Install from file...`.
   - Select the downloaded `.ankiaddon` file.
   - Restart Anki when prompted.

## Usage

### Google Sheets Decks

1. **Add a New Google Sheets Deck:**
   - `Tools > Manage sheets2anki Decks > Add New Google Sheets Deck`.
   - Paste the published CSV URL from your Google Sheet.
   - Enter a deck name and confirm.

### Airtable Decks

1. **Add a New Airtable Deck:**
   - `Tools > Manage sheets2anki Decks > Add New Airtable Deck`.
   - Enter your Airtable Base ID (starts with `app`).
   - Enter the table name.
   - Enter your API key (starts with `pat` or `key`).
   - Optionally enter a view name to filter records.
   - Enter a deck name and confirm.

### Syncing and Management

2. **Sync All Decks:**
   - `Tools > Manage sheets2anki Decks > Sync All Decks` to update Anki from all connected data sources.

3. **Disconnect a Remote Deck:**
   - `Tools > Manage sheets2anki Decks > Disconnect a Remote Deck`.
   - This unlinks the remote data source. The local deck remains, allowing you to manage it entirely in Anki going forward.

## Requirements

- **Anki Version:** Compatible with Anki 2.1.x.
- **Note Models Needed:**
  - **Basic:** Fields `Front` and `Back`.
  - **Cloze:** Fields `Text` and `Extra`.
- **For Airtable:** Internet connection and valid Airtable API credentials.

Confirm these models exist before syncing.

## Troubleshooting

### General Issues
- **No Cards Imported?**  
  Check field names (`question`/`front`, `answer`/`back`, `tags`) and ensure required note models exist.
- **Cloze Cards Not Forming?**  
  Ensure Cloze syntax (`{{c1::...}}`) is correct and the Cloze model has `Text` and `Extra` fields.
- **Cards Reappearing After Deletion in Anki?**  
  Remember there's no reverse sync. Remove the card from the data source if you want it gone permanently.

### Google Sheets Specific
- **Changes Not Updating?**  
  Wait a few minutes after editing the sheet or verify the correct published CSV URL.

### Airtable Specific  
- **API Connection Errors?**  
  - Verify your Base ID, API key, and table name are correct.
  - Ensure your API key has read permissions for the base.
  - Check that the table and view (if specified) exist.
- **No Records Found?**  
  - Check that your table has records with the required field names.
  - If using a view, ensure it contains the records you want to sync.

## Beta Status and Future Plans

Sheets2Anki is in beta. Basic and Cloze types are supported now, but more features and improvements may follow as the project evolves. Keep an eye on this repository for updates.

## Keyboard Shortcuts

- **Ctrl+Shift+A:** Add New Google Sheets Deck
- **Ctrl+Shift+T:** Add New Airtable Deck  
- **Ctrl+Shift+S:** Sync All Decks
- **Ctrl+Shift+D:** Disconnect a Remote Deck
