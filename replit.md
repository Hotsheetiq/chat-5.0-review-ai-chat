# Property Management Voice Assistant

## Overview

This is an AI-powered voice assistant system designed for property management companies. It integrates with Twilio for phone calls, OpenAI's Realtime API for conversational AI, and Rent Manager for tenant data management. The system handles incoming calls from both tenants and prospects, providing maintenance request processing, general property information, and automated call logging.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application is built with Flask and Flask-SocketIO to provide a comprehensive voice assistant system. The system processes phone calls through Twilio, uses natural language processing for conversations, and integrates with property management systems for data retrieval and storage.

**Core Architecture Components:**
- **Web Server**: Flask application with SocketIO for real-time communication
- **Voice Gateway**: Twilio Voice API for handling inbound phone calls with TwiML responses
- **AI Engine**: Supports OpenAI Realtime API integration for natural conversations (when API key provided)
- **Data Layer**: Rent Manager API integration for tenant lookup, service issues, and call logging
- **Static Frontend**: Responsive Bootstrap dashboard for system monitoring

## Key Components

### Voice Processing Pipeline
- **Twilio Voice Integration**: Handles incoming calls and streams audio via WebSocket
- **OpenAI Realtime API**: Processes voice input and generates natural language responses
- **Call Routing Logic**: Differentiates between tenant and prospect calls based on phone number lookup

### Data Management
- **RentManagerAPI Class**: Handles tenant lookups, service issue creation, and call logging
- **PropertyDataManager Class**: Manages static property information, amenities, and policies
- **Async HTTP Client**: Uses aiohttp for non-blocking API calls to external services

### User Interface
- **Dashboard**: Real-time status monitoring of system components
- **Responsive Design**: Bootstrap-based UI with dark theme support
- **Status Indicators**: Visual feedback for Twilio, AI, and Rent Manager connectivity

## Data Flow

1. **Incoming Call**: Phone call received through Twilio webhook
2. **Caller Identification**: Phone number lookup against Rent Manager tenant database
3. **AI Routing**: Call context (tenant/prospect status) sent to OpenAI assistant
4. **Conversation Handling**: AI processes voice input and generates appropriate responses
5. **Action Execution**: Based on conversation, system creates service issues or worker tasks
6. **Call Logging**: All interactions logged to Rent Manager for record keeping

## External Dependencies

### Required Services
- **Twilio**: Voice communication platform for call handling and audio streaming
- **OpenAI Realtime API**: Conversational AI engine for natural language processing
- **Rent Manager**: Property management software for tenant data and service tracking

### Environment Configuration
- `OPENAI_API_KEY`: Authentication for OpenAI services
- `RENT_MANAGER_API_KEY`: API access token for tenant data
- `TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN`: Twilio service credentials
- `PORT`: Application server port (defaults to 5000)

### Python Dependencies
- **FastAPI**: Modern web framework for API development
- **WebSockets**: Real-time communication for voice streaming
- **aiohttp**: Async HTTP client for external API calls
- **Jinja2**: Template engine for HTML rendering

## Deployment Strategy

The application is designed for cloud deployment with the following considerations:

**Containerization Ready**: Standard Python application structure suitable for Docker deployment

**Environment-Based Configuration**: All sensitive credentials managed through environment variables

**Scalability Considerations**: 
- Async/await pattern throughout for handling concurrent calls
- WebSocket connections for real-time voice streaming
- Stateless design allowing horizontal scaling

**Monitoring & Logging**: 
- Comprehensive logging throughout all components
- Dashboard interface for real-time system health monitoring
- Status indicators for all external service dependencies

**Production Requirements**:
- HTTPS/WSS for secure WebSocket connections
- Load balancer for handling multiple concurrent calls  
- Environment variable management for sensitive credentials
- Health check endpoints for container orchestration

## Recent Changes

### July 23, 2025 - Sarah Voice Assistant Optimization
- **Voice Enhancement**: Replaced robotic SSML tags with natural Polly.Kimberly-Neural American accent
- **Intelligent Conversation System**: Implemented conversation memory to eliminate repetitive responses
- **Context-Aware Responses**: Added smart fallback system that adapts based on caller questions and conversation history
- **Natural Language Processing**: Responses now use conversational patterns instead of formal business language
- **Greeting Standardization**: Implemented exact requested greeting: "It's a great day at Grinberg Management, this is Sarah! How can I help you today?"
- **AI Identity Handling**: Natural responses when asked about being human/AI, including recognition of "Siri" references
- **Maintenance Workflow**: Enhanced maintenance request processing with specific issue categorization (plumbing, electrical, HVAC)
- **Leasing Support**: Improved apartment inquiry handling with size and move-in date collection