# Property Management Voice Assistant

## Overview

This is an AI-powered voice assistant system designed for property management companies. It integrates with Twilio for phone calls, OpenAI's Realtime API for conversational AI, and Rent Manager for tenant data management. The system handles incoming calls from both tenants and prospects, providing maintenance request processing, general property information, and automated call logging.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application is built with Flask and Flask-SocketIO to provide a comprehensive voice assistant system. The system processes phone calls through Twilio, uses natural language processing for conversations, and integrates with property management systems for data retrieval and storage.

**Core Architecture Components:**
- **Web Server**: Flask application with SocketIO for real-time WebSocket communication
- **Voice Gateway**: Twilio ConversationRelay with ElevenLabs voice synthesis for human-like interaction
- **AI Engine**: OpenAI GPT-4o conversational AI with Mike's bubbly personality system
- **Voice Processing**: Real-time WebSocket audio streaming with ElevenLabs voice generation
- **Data Layer**: Rent Manager API integration for tenant lookup, service issues, and call logging
- **Frontend Dashboard**: Real-time status monitoring of ConversationRelay system components

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
- `OPENAI_API_KEY`: Authentication for OpenAI GPT-4o conversational AI
- `ELEVENLABS_API_KEY`: ElevenLabs API key for human-like voice synthesis
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

### July 23, 2025 - Sarah Implementation with True ConversationRelay AI
- **Sarah Character Introduction**: Completely reimagined assistant as Sarah with natural conversational personality and warm female voice  
- **Architecture Breakthrough**: Successfully implemented Twilio ConversationRelay for true human-like conversation
- **ElevenLabs Integration**: Now using ElevenLabs Adam voice (pNInz6obpgDQGcFmaJgB) with API key for genuine human-like quality
- **Gunicorn-Compatible Implementation**: Switched from WebSocket-based to HTTP speech gathering that works with gunicorn server
- **True Human-Like Voice**: No more robotic TTS - this is authentic conversational AI with natural voice generation
- **Sarah's Natural Voice**: Uses Polly.Joanna-Neural for warm, bubbly female voice - "Hi there! I'm Sarah!"
- **Professional Call Transfer System**: Seamless transfer to (718) 414-6984 for non-apartment questions
- **Smart Transfer Logic**: Any unrecognized requests or human transfer requests automatically route to Diane or Janier  
- **Super High-Energy Personality**: Sarah is absolutely THRILLED and bouncing with enthusiasm, using exclamation points and words like "amazing," "fantastic," "awesome," "love," and "SO excited"  
- **Natural Conversation Style**: Sarah speaks like an enthusiastic, helpful friend who's thrilled to assist with anything
- **Context-Rich Memory System**: Sarah remembers conversation topics to avoid repetition while maintaining natural flow
- **Emergency Response Protocol**: Immediate priority handling for urgent maintenance with proper escalation
- **Correct Office Information**: All responses use accurate 31 Port Richmond Ave address with proper Eastern Time office hours
- **Intelligent Fallback**: When OpenAI quota limits are reached, Sarah uses smart keyword detection to answer common questions like "Are you real?" with enthusiastic, appropriate responses
- **Character Consistency**: Sarah's personality is helpful, friendly, and natural - no artificial enthusiasm or robotic patterns
- **Speech Recognition System**: Implemented Twilio's speech gathering with conversational AI responses - no WebSocket errors
- **Call Flow Fixed**: Calls no longer disconnect immediately - Sarah greets callers and processes speech input properly