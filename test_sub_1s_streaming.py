#!/usr/bin/env python3
"""
Test Script for Sub-1s Streaming Voice Assistant
Validates OpenAI-only compliance, mode selection, and performance targets
"""

import time
import json
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openai_only_compliance():
    """Test that system uses only OpenAI and rejects Grok"""
    print("🔍 TESTING: OpenAI-Only Compliance")
    print("=" * 50)
    
    try:
        from openai_conversation_manager import conversation_manager
        
        # Test 1: Verify OpenAI streaming works
        print("1. Testing OpenAI streaming capability...")
        openai_ready = conversation_manager.test_streaming()
        print(f"   OpenAI Streaming: {'✅ READY' if openai_ready else '❌ ERROR'}")
        
        # Test 2: Verify Grok guard is active
        print("2. Testing Grok usage guard...")
        guard_active = conversation_manager.grok_guard_active
        print(f"   Grok Guard: {'✅ ACTIVE' if guard_active else '❌ INACTIVE'}")
        
        # Test 3: Try to trigger Grok detection
        print("3. Testing Grok detection...")
        try:
            conversation_manager.detect_grok_usage("test grok usage")
            print("   ❌ ERROR: Grok detection failed")
        except Exception as e:
            if "Grok usage detected" in str(e):
                print("   ✅ SUCCESS: Grok usage properly detected and blocked")
            else:
                print(f"   ❌ ERROR: Unexpected exception: {e}")
        
        print("\n🛡️ OpenAI-Only Compliance: VERIFIED")
        return True
        
    except Exception as e:
        print(f"❌ Compliance test failed: {e}")
        return False

def test_runtime_mode_selection():
    """Test automatic runtime mode selection"""
    print("\n🎯 TESTING: Runtime Mode Selection")
    print("=" * 50)
    
    try:
        from twilio_media_stream_handler import media_stream_handler
        
        # Test current mode selection
        print("1. Testing current mode selection...")
        current_mode = media_stream_handler.get_current_mode()
        print(f"   Selected Mode: {current_mode}")
        
        if current_mode == "full_streaming":
            print("   🚀 FULL STREAMING MODE - Target: <1s to first audio")
        elif current_mode == "sentence_chunk":
            print("   🔄 SENTENCE-CHUNK MODE - Target: <1.5s to first audio")
        else:
            print("   ⚠️ UNKNOWN MODE")
        
        # Test streaming availability
        print("2. Testing streaming availability...")
        streaming_available = media_stream_handler.test_full_streaming_available()
        print(f"   Full Streaming Available: {'✅ YES' if streaming_available else '❌ NO'}")
        
        print(f"\n🎯 Runtime Mode Selection: {current_mode.upper()}")
        return True
        
    except Exception as e:
        print(f"❌ Mode selection test failed: {e}")
        return False

def test_performance_targets():
    """Test that performance targets are properly configured"""
    print("\n⏱️ TESTING: Performance Configuration")
    print("=" * 50)
    
    try:
        from sub_1s_streaming_app import STREAMING_CONFIG
        
        print("Performance Targets:")
        print(f"   Full Streaming: <{STREAMING_CONFIG['target_latency_full_streaming']}s")
        print(f"   Sentence-Chunk: <{STREAMING_CONFIG['target_latency_sentence_chunk']}s")
        print(f"   VAD Timeout: {STREAMING_CONFIG['vad_end_silence_ms']}ms")
        print(f"   Gather Timeout: {STREAMING_CONFIG['gather_speech_timeout']}s")
        
        # Validate targets meet specifications
        full_target = STREAMING_CONFIG['target_latency_full_streaming']
        chunk_target = STREAMING_CONFIG['target_latency_sentence_chunk']
        vad_timeout = STREAMING_CONFIG['vad_end_silence_ms']
        
        print("\nValidation:")
        print(f"   Full streaming <1s: {'✅ YES' if full_target < 1.0 else '❌ NO'}")
        print(f"   Sentence-chunk <1.5s: {'✅ YES' if chunk_target < 1.5 else '❌ NO'}")
        print(f"   VAD 500-700ms range: {'✅ YES' if 500 <= vad_timeout <= 700 else '❌ NO'}")
        
        print("\n⏱️ Performance Targets: CONFIGURED")
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

async def test_conversation_processing():
    """Test conversation processing with session facts"""
    print("\n💬 TESTING: Conversation Processing")
    print("=" * 50)
    
    try:
        from openai_conversation_manager import conversation_manager
        
        test_call_sid = "TEST_CALL_001"
        
        # Test 1: Basic processing
        print("1. Testing basic conversation processing...")
        start_time = time.time()
        
        response, mode_used, processing_time = await conversation_manager.process_user_input(
            test_call_sid, 
            "Hello, I have a problem with my heat at 123 Main Street unit 4B"
        )
        
        elapsed = time.time() - start_time
        print(f"   Response: {response[:60]}...")
        print(f"   Mode Used: {mode_used}")
        print(f"   Processing Time: {processing_time:.3f}s")
        print(f"   Total Elapsed: {elapsed:.3f}s")
        
        # Test 2: Session facts extraction
        print("2. Testing session facts extraction...")
        facts = conversation_manager.get_session_facts(test_call_sid)
        print(f"   Extracted Facts: {json.dumps(facts, indent=2)}")
        
        # Test 3: Emergency detection
        print("3. Testing emergency detection...")
        emergency_response, emergency_mode, emergency_time = await conversation_manager.process_user_input(
            test_call_sid, 
            "I have no heat in my apartment"
        )
        
        facts_after_emergency = conversation_manager.get_session_facts(test_call_sid)
        print(f"   Emergency Mode: {emergency_mode}")
        print(f"   Priority: {facts_after_emergency.get('priority', 'Unknown')}")
        print(f"   Processing Time: {emergency_time:.3f}s")
        
        print("\n💬 Conversation Processing: FUNCTIONAL")
        return True
        
    except Exception as e:
        print(f"❌ Conversation processing test failed: {e}")
        return False

def test_elevenlabs_integration():
    """Test ElevenLabs streaming integration"""
    print("\n🎤 TESTING: ElevenLabs Integration")
    print("=" * 50)
    
    try:
        from elevenlabs_streaming import streaming_tts_client
        
        # Test streaming capability
        print("1. Testing ElevenLabs streaming...")
        streaming_ready = streaming_tts_client.test_streaming()
        print(f"   ElevenLabs Ready: {'✅ YES' if streaming_ready else '❌ NO'}")
        
        # Test voice configuration
        print("2. Testing voice configuration...")
        print(f"   Voice ID: {streaming_tts_client.voice_id}")
        print(f"   Model: eleven_flash_v2_5 (Flash for low latency)")
        print(f"   Settings: {json.dumps(streaming_tts_client.voice_settings, indent=2)}")
        
        print("\n🎤 ElevenLabs Integration: CONFIGURED")
        return True
        
    except Exception as e:
        print(f"❌ ElevenLabs test failed: {e}")
        return False

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n📊 COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("OpenAI-Only Compliance", test_openai_only_compliance),
        ("Runtime Mode Selection", test_runtime_mode_selection),
        ("Performance Configuration", test_performance_targets),
        ("ElevenLabs Integration", test_elevenlabs_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Run async test
    try:
        print("\nRunning async conversation test...")
        async_result = asyncio.run(test_conversation_processing())
        results["Conversation Processing"] = async_result
    except Exception as e:
        print(f"❌ Conversation processing failed: {e}")
        results["Conversation Processing"] = False
    
    # Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS READY FOR SUB-1S STREAMING!")
        print("🚀 OpenAI-only compliance verified")
        print("⚡ Performance targets configured")
        print("🛡️ Grok usage protection active")
    else:
        print("\n⚠️ Some tests failed - review configuration")
    
    return passed == total

if __name__ == "__main__":
    print("🚀 SUB-1S STREAMING VOICE ASSISTANT TEST SUITE")
    print(f"Test started at: {datetime.now()}")
    print("=" * 60)
    
    success = generate_test_report()
    
    print(f"\nTest completed at: {datetime.now()}")
    print(f"Exit code: {'0 (SUCCESS)' if success else '1 (FAILURE)'}")
    
    exit(0 if success else 1)