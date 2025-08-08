# Property Management Voice Assistant

## Overview
This project is an advanced AI-powered voice assistant ("Chris") for property management companies. It handles incoming calls from tenants and prospects, processing maintenance requests, providing general property information, and logging calls. The system aims to provide ultra-low latency streaming responses and a human-like conversational experience. The business vision is to streamline property management communications, enhance tenant satisfaction, and leverage AI for efficient operations, with ambitions for market leadership in AI-driven property solutions.

## User Preferences
Preferred communication style: Simple, everyday language.
Voice system preference: ElevenLabs human-like voice only - no Polly fallback desired.
AI System: OpenAI three-mode system with real-time streaming capabilities.

## System Architecture
The application is built with Flask and Flask-SocketIO, integrating various services to provide a comprehensive voice assistant.

**Core Architectural Decisions:**
- **Web Server**: Flask application with SocketIO for real-time WebSocket communication and OpenAI integration.
- **Voice Gateway**: Twilio ConversationRelay with ElevenLabs voice synthesis for human-like interaction and ultra-low latency streaming responses.
- **AI Engine**: OpenAI three-mode system, including default streaming (gpt-4o-mini), live real-time API with Voice Activity Detection (VAD) for barge-in, and heavy reasoning (gpt-4.1/gpt-5.0) for complex issues.
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