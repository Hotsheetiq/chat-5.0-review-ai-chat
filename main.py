# Import both apps - user can choose which to deploy
try:
    # Try new real-time app first (if user wants OpenAI + ElevenLabs streaming)
    from realtime_voice_app import create_app as create_realtime_app
    app = create_realtime_app()
    print("🎙️ Using Real-time Voice Assistant (OpenAI + ElevenLabs Streaming)")
except ImportError as e:
    # Fallback to existing app
    print(f"Real-time app import failed: {e}")
    from fixed_conversation_app import create_app
    app = create_app()
    print("📞 Using Legacy Voice Assistant (Grok + Standard TTS)")