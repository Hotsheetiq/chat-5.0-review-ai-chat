# Property Management Voice Assistant

## Overview
This project is an AI-powered voice assistant, "Chris," designed for property management companies. It integrates with Twilio for phone calls, OpenAI's GPT-4o for conversational AI, ElevenLabs for natural voice synthesis, and Rent Manager for tenant data management. The system automates handling incoming calls from tenants and prospects, providing maintenance request processing, general property information, and automated call logging. The vision is to streamline property management communications, reduce manual workload, and enhance tenant and prospect experience through intelligent, human-like interactions.

## User Preferences
Preferred communication style: Simple, everyday language.
Voice system preference: ElevenLabs human-like voice only - no Polly fallback desired.

## System Architecture
The application is built with Flask and Flask-SocketIO, providing a comprehensive voice assistant. It processes phone calls via Twilio, uses natural language processing for conversations, and integrates with property management systems for data retrieval and storage.

**Core Architecture Components:**
- **Real-time Voice Engine**: OpenAI Realtime API with streaming token responses and voice activity detection
- **Streaming TTS**: ElevenLabs Flash voices for ultra-low latency (sub-second) audio generation  
- **Smart Model Switching**: GPT-4o-mini default, auto-switch to GPT-4.1/5.0 for complex reasoning
- **Voice Gateway**: Twilio Media Streams with WebSocket audio streaming and barge-in support
- **Interruption Handling**: Real-time voice activity detection with immediate response stopping
- **Property Management**: Integrated Rent Manager API for tenant verification and service requests
- **Real-time Dashboard**: Live call monitoring with OpenAI + ElevenLabs streaming status

**Key Features:**
- **Dynamic Greeting System**: Provides varied, enthusiastic greetings for each caller.
- **Complaint Confirmation System**: Chris repeats back complaints to confirm understanding.
- **Anti-Repetition System**: Prevents Chris from repeating exact phrases during a call.
- **Comprehensive Tenant Assistance**: Handles maintenance, rent questions, building amenities, general inquiries, and complaints.
- **Address Verification**: Verifies addresses against the Rent Manager API, with intelligent numerical proximity matching and fallback for unverified properties.
- **Call Flow System**: Immediate hold messages with parallel AI processing for complex requests.
- **Conversation Memory**: Maintains full conversation context throughout a call for intelligent, non-repetitive responses.
- **Automated Service Warm-Up**: Eliminates cold start delays for all integrated services.
- **Real-time Call Monitoring**: Dashboard for live call transcription, status, and analytics.
- **Admin Training System**: Allows administrators to train Chris via direct phone conversation.

**Technical Implementations:**
- Uses `aiohttp` for non-blocking API calls.
- Integrates `ThreadPoolExecutor` for parallel processing (e.g., ElevenLabs generation).
- Employs response caching for AI and voice generation.
- Designed for containerization and environment-based configuration.
- Features comprehensive logging and health check endpoints.

## External Dependencies
- **Twilio**: Voice communication platform for call handling and audio streaming.
- **OpenAI Realtime API**: Conversational AI engine (GPT-4o, with Grok 2 fallback) for natural language processing.
- **ElevenLabs**: Voice synthesis for natural, human-like audio responses.
- **Rent Manager**: Property management software for tenant data, service issue tracking, and call logging.
- **SendGrid**: Email service for sending call transcripts and notifications.
- **Python Libraries**: Flask, Flask-SocketIO, aiohttp, Jinja2, WebSockets, pytz.