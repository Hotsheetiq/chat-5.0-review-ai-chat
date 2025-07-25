"""
Admin Training Interface for Chris
- Direct conversation with Chris using reasoning and learning
- Admin can provide instructions and corrections
- Chris can ask clarifying questions to improve responses
"""

from flask import Flask, request, render_template_string, jsonify, session
import os
import logging
from datetime import datetime
import json
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "admin_training_secret"

# Training conversation storage
training_conversations = {}
learning_database = {
    "instructions": [],
    "corrections": [],
    "patterns": {},
    "knowledge_base": {}
}

def save_learning_to_file():
    """Save learning database to persistent file"""
    try:
        with open('chris_learning.json', 'w') as f:
            json.dump(learning_database, f, indent=2, default=str)
        logger.info("✅ Learning database saved")
    except Exception as e:
        logger.error(f"Failed to save learning: {e}")

def load_learning_from_file():
    """Load learning database from file"""
    global learning_database
    try:
        with open('chris_learning.json', 'r') as f:
            learning_database = json.load(f)
        logger.info("✅ Learning database loaded")
    except FileNotFoundError:
        logger.info("No existing learning database found, starting fresh")
    except Exception as e:
        logger.error(f"Failed to load learning: {e}")

def get_chris_response_with_reasoning(user_input, session_id, is_admin=True):
    """Get intelligent response from Chris with reasoning capabilities"""
    try:
        if not openai_client:
            return "I need the OpenAI API key to use my reasoning capabilities."
        
        # Build comprehensive context
        messages = [
            {
                "role": "system",
                "content": f"""You are Chris, an intelligent AI assistant for Grinberg Management property company. 

CURRENT MODE: {"ADMIN TRAINING" if is_admin else "CUSTOMER SERVICE"}

In Admin Training Mode:
- You can think out loud and show your reasoning
- Ask clarifying questions to learn better responses
- Request specific instructions for improving your service
- Analyze patterns in customer interactions
- Suggest improvements to your conversation flow

Your learning database contains:
Instructions: {len(learning_database['instructions'])} entries
Corrections: {len(learning_database['corrections'])} entries  
Patterns: {len(learning_database['patterns'])} categories

Be conversational, intelligent, and eager to learn. Show your thought process and ask questions that will help you serve customers better.

Key responsibilities:
- Handle maintenance requests and create service tickets
- Provide office hours and property information
- Transfer calls when appropriate
- Maintain professional but friendly tone

Always be curious about improving your responses and understanding customer needs better."""
            }
        ]
        
        # Add conversation history
        if session_id in training_conversations:
            for entry in training_conversations[session_id][-10:]:  # Last 10 exchanges
                messages.append({
                    "role": entry['role'],
                    "content": entry['content']
                })
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Get response with reasoning
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500,  # More tokens for reasoning
            temperature=0.7,
            timeout=10.0
        )
        
        result = response.choices[0].message.content.strip()
        
        # Store conversation
        if session_id not in training_conversations:
            training_conversations[session_id] = []
        
        training_conversations[session_id].extend([
            {'role': 'user', 'content': user_input, 'timestamp': datetime.now()},
            {'role': 'assistant', 'content': result, 'timestamp': datetime.now()}
        ])
        
        return result
        
    except Exception as e:
        logger.error(f"Chris reasoning error: {e}")
        return f"I encountered an error with my reasoning: {e}. Could you help me understand what went wrong?"

def process_admin_instruction(instruction, session_id):
    """Process admin instruction and update learning database"""
    try:
        # Store instruction
        learning_database['instructions'].append({
            'instruction': instruction,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        })
        
        # Let Chris analyze the instruction
        analysis_prompt = f"""
        Analyze this admin instruction: "{instruction}"
        
        Extract:
        1. What specific behavior should change?
        2. What patterns should I learn?
        3. What knowledge should I store?
        4. How should this affect future conversations?
        
        Provide a structured analysis.
        """
        
        analysis = get_chris_response_with_reasoning(analysis_prompt, session_id + "_analysis")
        
        # Save learning
        save_learning_to_file()
        
        return analysis
        
    except Exception as e:
        logger.error(f"Instruction processing error: {e}")
        return f"I had trouble processing that instruction: {e}"

@app.route("/admin-training")
def admin_training_interface():
    """Admin training interface"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Chris Admin Training Interface</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        .conversation-container { max-height: 60vh; overflow-y: auto; }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .admin-message { background-color: var(--bs-primary-bg-subtle); border-left: 4px solid var(--bs-primary); }
        .chris-message { background-color: var(--bs-secondary-bg-subtle); border-left: 4px solid var(--bs-secondary); }
        .reasoning { font-style: italic; color: var(--bs-secondary); font-size: 0.9em; }
        .learning-stats { font-size: 0.85em; color: var(--bs-info); }
    </style>
</head>
<body data-bs-theme="dark">
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8">
                <h2>🧠 Chris Admin Training Interface</h2>
                <p class="text-secondary">Train Chris through conversation. He can reason, ask questions, and learn from your instructions.</p>
                
                <div class="card">
                    <div class="card-body">
                        <h5>Current Learning Status</h5>
                        <div class="learning-stats">
                            <div>📚 Instructions Learned: <span id="instruction-count">0</span></div>
                            <div>🔧 Corrections Applied: <span id="correction-count">0</span></div>
                            <div>🧩 Patterns Recognized: <span id="pattern-count">0</span></div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-header">
                        <h5>Conversation with Chris</h5>
                    </div>
                    <div class="card-body">
                        <div class="conversation-container" id="conversation">
                            <div class="chris-message message">
                                <strong>Chris:</strong> Hi! I'm ready for training. You can ask me questions, give me instructions, or test my responses. I'll show my reasoning and ask questions to learn better. What would you like to work on?
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <div class="input-group">
                                <input type="text" class="form-control" id="admin-input" placeholder="Type your instruction or question for Chris..." onkeypress="if(event.key==='Enter') sendMessage()">
                                <button class="btn btn-primary" onclick="sendMessage()">Send</button>
                            </div>
                            <small class="text-secondary">Examples: "When customers ask about office hours, be more specific about Eastern Time" or "Test: How do you handle electrical emergencies?"</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h6>Training Commands</h6>
                    </div>
                    <div class="card-body">
                        <div class="mb-2">
                            <button class="btn btn-outline-info btn-sm w-100" onclick="sendQuickCommand('Test customer service skills')">Test Customer Service</button>
                        </div>
                        <div class="mb-2">
                            <button class="btn btn-outline-warning btn-sm w-100" onclick="sendQuickCommand('Explain your maintenance request process')">Review Maintenance Process</button>
                        </div>
                        <div class="mb-2">
                            <button class="btn btn-outline-success btn-sm w-100" onclick="sendQuickCommand('What have you learned so far?')">Review Learning</button>
                        </div>
                        <div class="mb-2">
                            <button class="btn btn-outline-secondary btn-sm w-100" onclick="sendQuickCommand('Show me your reasoning for office hours questions')">Test Reasoning</button>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-3">
                    <div class="card-header">
                        <h6>Quick Instructions</h6>
                    </div>
                    <div class="card-body">
                        <small class="text-secondary">
                        • "Be more specific about..."<br>
                        • "When customers say X, respond with..."<br>
                        • "Always ask for clarification when..."<br>
                        • "Improve your response to..."<br>
                        • "Remember that customers often..."
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let sessionId = 'admin_' + Date.now();
        
        function sendMessage() {
            const input = document.getElementById('admin-input');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage('Admin', message, 'admin-message');
            input.value = '';
            
            // Send to Chris
            fetch('/admin-chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message, session_id: sessionId})
            })
            .then(response => response.json())
            .then(data => {
                addMessage('Chris', data.response, 'chris-message');
                updateLearningStats(data.learning_stats);
            })
            .catch(err => {
                addMessage('System', 'Error: ' + err, 'chris-message');
            });
        }
        
        function sendQuickCommand(command) {
            document.getElementById('admin-input').value = command;
            sendMessage();
        }
        
        function addMessage(sender, content, className) {
            const conversation = document.getElementById('conversation');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + className;
            messageDiv.innerHTML = `<strong>${sender}:</strong> ${content}`;
            conversation.appendChild(messageDiv);
            conversation.scrollTop = conversation.scrollHeight;
        }
        
        function updateLearningStats(stats) {
            if (stats) {
                document.getElementById('instruction-count').textContent = stats.instructions || 0;
                document.getElementById('correction-count').textContent = stats.corrections || 0;
                document.getElementById('pattern-count').textContent = stats.patterns || 0;
            }
        }
        
        // Load initial stats
        fetch('/learning-stats')
            .then(response => response.json())
            .then(data => updateLearningStats(data));
    </script>
</body>
</html>
    """)

@app.route("/admin-chat", methods=["POST"])
def admin_chat():
    """Handle admin chat with Chris"""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Get Chris's response with reasoning
        chris_response = get_chris_response_with_reasoning(message, session_id, is_admin=True)
        
        # If this looks like an instruction, process it
        if any(word in message.lower() for word in ['should', 'must', 'always', 'never', 'remember', 'when customers', 'instruction']):
            instruction_analysis = process_admin_instruction(message, session_id)
            chris_response += f"\n\n*Analysis: {instruction_analysis}*"
        
        return jsonify({
            'response': chris_response,
            'learning_stats': {
                'instructions': len(learning_database['instructions']),
                'corrections': len(learning_database['corrections']),
                'patterns': len(learning_database['patterns'])
            }
        })
        
    except Exception as e:
        logger.error(f"Admin chat error: {e}")
        return jsonify({'response': f'Error in training interface: {e}'})

@app.route("/learning-stats")
def learning_stats():
    """Get current learning statistics"""
    return jsonify({
        'instructions': len(learning_database['instructions']),
        'corrections': len(learning_database['corrections']),
        'patterns': len(learning_database['patterns'])
    })

@app.route("/export-learning")
def export_learning():
    """Export learning database"""
    return jsonify(learning_database)

if __name__ == "__main__":
    load_learning_from_file()
    app.run(host="0.0.0.0", port=5001, debug=True)