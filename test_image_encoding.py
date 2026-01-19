#!/usr/bin/env python3
"""
Test script to verify image encoding is working correctly
"""

import os
import base64
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini_image_generation():
    """Test Gemini image generation and encoding"""
    
    print("🧪 Testing Gemini Image Generation & Encoding\n")
    print("=" * 60)
    
    # Configure Gemini
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found in environment")
        return
    
    print(f"✅ API key found: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    
    # Test prompt
    prompt = "A simple red circle on a white background"
    model_name = "gemini-2.5-flash-image"
    
    print(f"\n📝 Prompt: {prompt}")
    print(f"🤖 Model: {model_name}")
    print("\n⏳ Generating image...")
    
    try:
        # Generate image
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        print("✅ Response received!")
        
        # Inspect response structure
        print("\n🔍 Response Structure:")
        print(f"   - Has candidates: {hasattr(response, 'candidates')}")
        if hasattr(response, 'candidates') and response.candidates:
            print(f"   - Number of candidates: {len(response.candidates)}")
            
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
                print(f"   - Number of parts: {len(parts)}")
                
                for idx, part in enumerate(parts):
                    print(f"\n   Part {idx}:")
                    
                    # Check for text
                    if hasattr(part, 'text') and part.text:
                        print(f"      - Type: TEXT")
                        print(f"      - Content: {part.text[:100]}...")
                    
                    # Check for inline_data
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"      - Type: INLINE_DATA")
                        
                        mime_type = getattr(part.inline_data, 'mime_type', 'unknown')
                        print(f"      - MIME type: {mime_type}")
                        
                        if mime_type.startswith('image/'):
                            print(f"\n   🎨 IMAGE FOUND!")
                            
                            # Get the data
                            image_data = part.inline_data.data
                            print(f"\n   📊 Data Analysis:")
                            print(f"      - Data type: {type(image_data)}")
                            print(f"      - Data type name: {type(image_data).__name__}")
                            
                            # Check if bytes or string
                            if isinstance(image_data, bytes):
                                print(f"      - ✅ Data is BYTES")
                                print(f"      - Length: {len(image_data):,} bytes")
                                print(f"      - First 20 bytes: {image_data[:20]}")
                                print(f"      - PNG header valid: {image_data[:8] == b'\\x89PNG\\r\\n\\x1a\\n'}")
                                
                                image_bytes = image_data
                                
                            elif isinstance(image_data, str):
                                print(f"      - ⚠️ Data is STRING (base64)")
                                print(f"      - Length: {len(image_data):,} chars")
                                print(f"      - First 50 chars: {image_data[:50]}")
                                
                                # Try to decode
                                try:
                                    image_bytes = base64.b64decode(image_data)
                                    print(f"      - ✅ Decoded to {len(image_bytes):,} bytes")
                                    print(f"      - PNG header valid: {image_bytes[:8] == b'\\x89PNG\\r\\n\\x1a\\n'}")
                                except Exception as e:
                                    print(f"      - ❌ Failed to decode: {e}")
                                    return
                            else:
                                print(f"      - ❌ Unknown data type: {type(image_data)}")
                                return
                            
                            # Now encode to base64 and create data URI
                            print(f"\n   🔧 Encoding to base64...")
                            base64_string = base64.b64encode(image_bytes).decode('utf-8')
                            print(f"      - Base64 length: {len(base64_string):,} chars")
                            print(f"      - First 100 chars: {base64_string[:100]}")
                            print(f"      - Last 50 chars: ...{base64_string[-50:]}")
                            
                            # Validate base64
                            if re.match(r'^[A-Za-z0-9+/]*={0,2}$', base64_string):
                                print(f"      - ✅ Valid base64 (only contains A-Z, a-z, 0-9, +, /, =)")
                            else:
                                print(f"      - ❌ INVALID base64! Contains illegal characters!")
                                # Find illegal characters
                                illegal = set(re.findall(r'[^A-Za-z0-9+/=]', base64_string))
                                print(f"      - Illegal characters found: {illegal}")
                                return
                            
                            # Create data URI
                            data_uri = f"data:image/png;base64,{base64_string}"
                            print(f"\n   🖼️ Data URI:")
                            print(f"      - Total length: {len(data_uri):,} chars")
                            print(f"      - Preview: {data_uri[:100]}...")
                            
                            # Save to file
                            print(f"\n   💾 Saving test image...")
                            with open('test_gemini_image.png', 'wb') as f:
                                f.write(image_bytes)
                            print(f"      - ✅ Saved to: test_gemini_image.png")
                            print(f"      - Try opening it to verify it's valid!")
                            
                            # Save data URI
                            with open('test_data_uri.txt', 'w') as f:
                                f.write(data_uri)
                            print(f"      - ✅ Saved data URI to: test_data_uri.txt")
                            print(f"      - Try using it in an <img> tag!")
                            
                            print(f"\n✅ SUCCESS! Image encoding is working correctly!")
                            return
        
        print("\n❌ No image found in response")
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_image_generation()
