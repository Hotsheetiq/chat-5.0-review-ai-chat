# Import intelligent conversational app (HTTP-based for gunicorn compatibility)
from intelligent_conversation_app import create_app
app = create_app()