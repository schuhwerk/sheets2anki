import json
import requests
import re
from .parseRemoteDeck import RemoteDeck

def getAirtableDeck(base_id, table_name, api_key, view_name=None):
    """
    Fetch data from Airtable and return a RemoteDeck object
    
    Args:
        base_id: Airtable base ID (starts with 'app')
        table_name: Name of the table to fetch
        api_key: Airtable Personal Access Token (recommended: starts with 'pat') or legacy API key (starts with 'key')
        view_name: Optional view name to filter records
    """
    try:
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        
        # Handle different authentication methods
        if api_key.startswith('pat'):
            # Personal Access Token - use Bearer authentication
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        else:
            # Legacy API Key - use Bearer authentication (both work the same way)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        
        params = {}
        if view_name:
            params["view"] = view_name
        
        # Fetch all records (handle pagination)
        all_records = []
        offset = None
        
        while True:
            if offset:
                params["offset"] = offset
                
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            all_records.extend(data.get("records", []))
            
            offset = data.get("offset")
            if not offset:
                break
        
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_msg = error_details.get('error', {}).get('message', str(e))
                raise Exception(f"Airtable API Error: {error_msg}. Please check your token permissions and base access.")
            except (ValueError, KeyError):
                pass
        
        # Handle specific authentication errors
        if "401" in str(e) or "Unauthorized" in str(e):
            if api_key.startswith('pat'):
                raise Exception(f"Authentication failed with Personal Access Token. Please verify:\n"
                              f"1. Token is correct and starts with 'pat'\n"
                              f"2. Token has 'data:records:read' permission\n"
                              f"3. Token has access to base {base_id}\n"
                              f"4. Table name '{table_name}' is correct\n"
                              f"Original error: {e}")
            else:
                raise Exception(f"Authentication failed with API key. Please verify:\n"
                              f"1. API key is correct\n"
                              f"2. Base ID {base_id} is correct\n"
                              f"3. Table name '{table_name}' is correct\n"
                              f"Note: Consider switching to Personal Access Token (PAT) for better security\n"
                              f"Original error: {e}")
        
        raise Exception(f"Error connecting to Airtable API: {e}")
    except Exception as e:
        raise Exception(f"Error processing Airtable data: {e}")

    remoteDeck = build_remote_deck_from_airtable(all_records)
    return remoteDeck

def build_remote_deck_from_airtable(records):
    """
    Build a RemoteDeck object from Airtable records
    
    Expected field names in Airtable (case-insensitive):
    - question, front, or text: The front/question side of the card
    - answer, back, or extra: The back/answer side of the card  
    - tags: Comma-separated or array of tags
    """
    questions = []
    
    for record_num, record in enumerate(records, start=1):
        fields = record.get("fields", {})
        
        # Skip empty records
        if not fields:
            print(f"Record {record_num} skipped because it has no fields")
            continue
            
        # Find question field (case-insensitive)
        question_text = None
        answer_text = None
        tags_data = None
        
        # Look for question/front field
        for field_name, field_value in fields.items():
            field_name_lower = field_name.lower().strip()
            
            if field_name_lower in ['question', 'front', 'text'] and not question_text:
                question_text = str(field_value).replace('\n', '<br>') if field_value else ""
            elif field_name_lower in ['answer', 'back', 'extra'] and not answer_text:
                answer_text = str(field_value).replace('\n', '<br>') if field_value else ""
            elif field_name_lower == 'tags' and not tags_data:
                tags_data = field_value
        
        # Skip if no question found
        if not question_text:
            print(f"Record {record_num} skipped because no question/front/text field found")
            continue
            
        # Ensure answer is not None
        if not answer_text:
            answer_text = ""
        
        # Process tags
        tags = []
        if tags_data:
            if isinstance(tags_data, list):
                # Tags are already in array format
                tags = [str(tag).strip() for tag in tags_data if tag]
            else:
                # Tags are in string format, split by comma or ::
                tag_string = str(tags_data)
                if '::' in tag_string:
                    tags = tag_string.split('::')
                else:
                    tags = tag_string.split(',')
                tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Detect if it's a Cloze deletion
        if re.search(r'{{c\d+::.*?}}', question_text):
            card_type = 'Cloze'
            fields_dict = {
                'Text': question_text,
                'Extra': answer_text
            }
        else:
            card_type = 'Basic'
            fields_dict = {
                'Front': question_text,
                'Back': answer_text
            }
        
        print(f"Detected card type: {card_type} for record {record_num}")
        
        # Create question dictionary
        question = {
            'type': card_type,
            'fields': fields_dict,
            'tags': tags
        }
        questions.append(question)
        print(f"Added question: {question_text[:50]}...")
    
    remoteDeck = RemoteDeck()
    remoteDeck.deckName = "Deck from Airtable"
    remoteDeck.questions = questions
    
    print(f"Total questions added: {len(questions)}")
    
    return remoteDeck
