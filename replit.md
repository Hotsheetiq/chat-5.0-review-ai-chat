# Property Management Voice Assistant

## Overview
This project is an advanced AI-powered voice assistant ("Chris") for property management companies. It handles incoming calls from tenants and prospects, processing maintenance requests, providing general property information, and logging calls. The system aims to provide ultra-low latency streaming responses and a human-like conversational experience. The business vision is to streamline property management communications, enhance tenant satisfaction, and leverage AI for efficient operations, with ambitions for market leadership in AI-driven property solutions.

## User Preferences
Preferred communication style: Simple, everyday language.
Voice system preference: ElevenLabs human-like voice only - no Polly fallback desired.
AI System: OpenAI three-mode system with real-time streaming capabilities and enhanced memory management.
Performance requirement: Sub-1-second response times with 500-700ms VAD timeout for ultra-fast interactions.

## System Architecture
The application is built with Flask and Flask-SocketIO, integrating various services to provide a comprehensive voice assistant.

**Core Architectural Decisions:**
- **Web Server**: Flask application with SocketIO for real-time WebSocket communication and OpenAI integration.
- **Voice Gateway**: Twilio ConversationRelay with ElevenLabs voice synthesis for human-like interaction and ultra-low latency streaming responses.
- **AI Engine**: OpenAI three-mode system with enhanced memory management, including default streaming (gpt-4o-mini), live real-time API with 500-700ms VAD for barge-in, and heavy reasoning (gpt-4o) for complex issues. Features session facts extraction (unit numbers, reported issues) and conversation context retention across mode switches.
- **Data Layer**: Integration with Rent Manager API for tenant data, service issues, and call logging.
- **Frontend Dashboard**: Real-time status monitoring with a responsive Bootstrap-based UI, dark theme support, and visual indicators for connectivity.
- **Voice Processing**: Real-time WebSocket audio streaming with ElevenLabs Flash voices and advanced VAD for natural conversation flow.
- **System Design Choices**: Asynchronous programming (`aiohttp`) for non-blocking API calls, containerization readiness, environment-based configuration, and stateless design for horizontal scalability. Includes robust logging, health check endpoints, and an intelligent system for dynamic greetings and anti-repetition in AI responses.

## External Dependencies
- **Twilio**: Used for voice communication, handling incoming calls, and streaming audio via WebSocket.
- **OpenAI**: Provides the conversational AI engine for natural language processing across its three modes (gpt-4o-mini, Realtime API, gpt-4.1/gpt-5.0).
- **ElevenLabs**: Utilized for natural, human-like voice synthesis with low latency.
- **Rent Manager**: Property management software integrated for tenant data lookup, service issue creation, and call logging.
- **SendGrid**: Used for sending email notifications, such as call transcripts.

## Recent Updates (August 8, 2025)
### Enhanced OpenAI Conversation System - OPERATIONAL
- **Performance**: Memory persistence across mode switches verified (0.432s response time in live mode)
- **Session Facts**: Automatic extraction of unit numbers and issues from user speech
- **Memory Management**: No repeated questions - system remembers provided information
- **VAD Optimization**: Reduced speechTimeout to 1 second for faster interaction detection
- **Three-Mode Operation**: Default (gpt-4o-mini streaming), Live (ultra-fast), Reasoning (gpt-4o) all functional
- **Context Retention**: Conversation history maintained across all modes with intelligent fact injection