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

### Critical Voice and Business Logic Fixes - August 8, 7:45 PM ET
- **ElevenLabs Voice Quality**: Upgraded to Flash model (eleven_flash_v2_5) with optimized natural speech settings
- **Contact Information Collection**: Chris now systematically collects: name, phone, address, unit number without repetition
- **Business Hours Accuracy**: Correctly identifies after-hours calls (office closed 5 PM-9 AM) and sets proper expectations
- **False Promise Prevention**: Eliminated 24/7 service claims and "tonight" repair promises - now says accurate business hours
- **Memory Enhancement**: Chris remembers all provided information and never asks for same details twice
- **Plain Language**: Uses contractions, simple words, and natural conversation patterns instead of robotic speech
- **Silent Response Fix**: Changed "I didn't catch that" to "Is there anything else I can help you with?"
- **Time-Based Greetings**: Proper good morning/afternoon/evening based on Eastern Time, only introduces himself once per call

### Official Business Rules Integration - August 8, 11:52 PM ET
- **Authoritative Policies**: Chris now follows only verified business rules from official company document
- **Emergency Detection**: Correctly identifies true emergencies (no heat, flooding, sewer backup) for 24/7 handling
- **Life-Threatening Protocol**: Immediately directs callers to call 911 for fire or life-threatening situations
- **Non-Emergency Handling**: Uses proper after-hours script for non-emergency issues during closed hours
- **Refusal Template**: Uses official company language when unable to make promises about services or timelines
- **Memory Fields**: Tracks unitNumber, reportedIssue, contactName, callbackNumber, and accessInstructions per business rules
- **No Unauthorized Promises**: Prevents Chris from making service commitments beyond authorized policies

### Automated Email Call Summaries - August 8, 11:58 PM ET
- **Call End Detection**: Automatically sends comprehensive email summaries when calls end via Twilio webhook
- **Priority Classification**: Intelligently labels calls as EMERGENCY, URGENT, or STANDARD based on reported issues
- **Comprehensive Details**: Includes caller info, property details, issue description, business hours context, and conversation transcript
- **Emergency Alerts**: Sends immediate alerts for true emergencies (no heat, flooding, sewer backup) with 🚨 priority marking
- **Professional Format**: Uses structured email format with sections for quick management review and follow-up actions
- **Truthful Reporting**: Only includes confirmed data, marks unknown fields as "unknown" rather than guessing
- **SendGrid Integration**: Reliable email delivery with proper error handling and logging