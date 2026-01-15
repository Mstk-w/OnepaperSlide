
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from layout_engine import process_layout

# Mock AI Output with invalid column index
mock_ai_output = {
    "recommended_template": "T1",
    "title": "Test Title",
    "subtitle": "Test Subtitle",
    "sections": [
        {
            "id": "valid_section",
            "column": 0,
            "type": "text_block",
            "content": {"text": "Valid"}
        },
        {
            "id": "invalid_section_extra",
            "column": 99,  # This should cause the crash
            "type": "text_block",
            "content": {"text": "Invalid"}
        }
    ],
    "footer_note": "Footer"
}

try:
    print("Attempting to process layout with invalid column...")
    layout = process_layout(mock_ai_output)
    print("Success (Unexpected)!")
except IndexError as e:
    print(f"Caught expected IndexError: {e}")
except Exception as e:
    print(f"Caught unexpected exception: {e}")
