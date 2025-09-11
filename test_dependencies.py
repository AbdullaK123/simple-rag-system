#!/usr/bin/env python3
"""
Test script for document dependencies validation
"""
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock
from fastapi import UploadFile
from io import BytesIO

# Add the app directory to the Python path
import sys
sys.path.append(str(Path(__file__).parent))

from app.dependencies.documents import validate_file, preprocess_uploaded_file
from app.dependencies.config import get_settings
from app.schemas.upload import UploadResult

async def test_validate_file():
    """Test the validate_file dependency function"""
    print("🧪 Testing validate_file function...")
    
    settings = get_settings()
    
    # Test 1: Valid file
    print("  ✓ Test 1: Valid text file")
    valid_content = "This is a test document with some content."
    file_mock = Mock(spec=UploadFile)
    file_mock.filename = "test.txt"
    file_mock.content_type = "text/plain"
    async def mock_read():
        return valid_content.encode('utf-8')
    async def mock_seek(pos):
        return None
    file_mock.read = mock_read
    file_mock.seek = mock_seek
    
    try:
        result = await validate_file(settings, file_mock)
        assert isinstance(result, UploadResult)
        assert result.source_file == "test.txt"
        assert result.content == valid_content
        assert result.content_type == "text/plain"
        print("    ✅ Valid file test passed")
    except Exception as e:
        print(f"    ❌ Valid file test failed: {e}")
        return False
    
    # Test 2: No filename
    print("  ✓ Test 2: File with no filename")
    file_mock_no_name = Mock(spec=UploadFile)
    file_mock_no_name.filename = ""
    
    try:
        result = await validate_file(settings, file_mock_no_name)
        print("    ❌ Should have raised HTTPException for no filename")
        return False
    except Exception as e:
        if "No file selected" in str(e):
            print("    ✅ No filename test passed")
        else:
            print(f"    ❌ Unexpected error: {e}")
            return False
    
    # Test 3: Invalid extension
    print("  ✓ Test 3: Invalid file extension")
    file_mock_invalid = Mock(spec=UploadFile)
    file_mock_invalid.filename = "test.exe"
    file_mock_invalid.content_type = "application/octet-stream"
    async def mock_read_invalid():
        return b"fake content"
    async def mock_seek_invalid(pos):
        return None
    file_mock_invalid.read = mock_read_invalid
    file_mock_invalid.seek = mock_seek_invalid
    
    try:
        result = await validate_file(settings, file_mock_invalid)
        print("    ❌ Should have raised HTTPException for invalid extension")
        return False
    except Exception as e:
        if "Invalid or missing file extension" in str(e):
            print("    ✅ Invalid extension test passed")
        else:
            print(f"    ❌ Unexpected error: {e}")
            return False
    
    # Test 4: File too large
    print("  ✓ Test 4: File too large")
    large_content = "x" * (settings.documents.max_file_size_bytes + 1)
    file_mock_large = Mock(spec=UploadFile)
    file_mock_large.filename = "large.txt"
    file_mock_large.content_type = "text/plain"
    async def mock_read_large():
        return large_content.encode('utf-8')
    async def mock_seek_large(pos):
        return None
    file_mock_large.read = mock_read_large
    file_mock_large.seek = mock_seek_large
    
    try:
        result = await validate_file(settings, file_mock_large)
        print("    ❌ Should have raised HTTPException for large file")
        return False
    except Exception as e:
        if "Upload is too big" in str(e):
            print("    ✅ Large file test passed")
        else:
            print(f"    ❌ Unexpected error: {e}")
            return False
    
    # Test 5: Non-UTF8 content
    print("  ✓ Test 5: Non-UTF8 content")
    binary_content = b'\x80\x81\x82\x83'  # Invalid UTF-8
    file_mock_binary = Mock(spec=UploadFile)
    file_mock_binary.filename = "binary.txt"
    file_mock_binary.content_type = "text/plain"
    async def mock_read_binary():
        return binary_content
    async def mock_seek_binary(pos):
        return None
    file_mock_binary.read = mock_read_binary
    file_mock_binary.seek = mock_seek_binary
    
    try:
        result = await validate_file(settings, file_mock_binary)
        print("    ❌ Should have raised HTTPException for non-UTF8 content")
        return False
    except Exception as e:
        if "File must be valid UTF-8" in str(e):
            print("    ✅ Non-UTF8 content test passed")
        else:
            print(f"    ❌ Unexpected error: {e}")
            return False
    
    return True

async def test_preprocess_uploaded_file():
    """Test the preprocess_uploaded_file dependency function"""
    print("\n🧪 Testing preprocess_uploaded_file function...")
    
    settings = get_settings()
    
    # Create a mock UploadResult
    upload_result = UploadResult(
        filename="test_uuid.txt",
        source_file="test.txt",
        content_type="text/plain",
        content="This is a long test document that should be split into multiple chunks. " * 50  # Make it long enough to split
    )
    
    try:
        documents = await preprocess_uploaded_file(settings, upload_result)
        
        # Verify the result
        assert isinstance(documents, list)
        assert len(documents) > 0
        
        print(f"  ✓ Created {len(documents)} document chunks")
        
        # Check first document structure
        first_doc = documents[0]
        assert hasattr(first_doc, 'page_content')
        assert hasattr(first_doc, 'metadata')
        
        # Check metadata structure
        metadata = first_doc.metadata
        assert 'uuid' in metadata
        assert 'source_file' in metadata
        assert 'filename' in metadata
        assert 'chunk_size' in metadata
        assert 'added_at' in metadata
        assert 'content_type' in metadata
        assert 'chunk_index' in metadata
        
        assert metadata['source_file'] == "test.txt"
        assert metadata['filename'] == "test_uuid.txt"
        assert metadata['content_type'] == "text/plain"
        assert metadata['chunk_index'] == 0
        
        print("  ✅ Document preprocessing test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Document preprocessing test failed: {e}")
        return False

async def test_file_upload_integration():
    """Test the integration between validate_file and preprocess_uploaded_file"""
    print("\n🧪 Testing file upload integration...")
    
    settings = get_settings()
    
    # Create a real text file for testing
    test_content = """
    This is a comprehensive test document for the RAG system.
    It contains multiple paragraphs and should be split into chunks.
    
    The document processing pipeline should handle this correctly,
    splitting it based on the configured chunk size and overlap.
    
    This allows us to test the complete flow from file upload
    through document preprocessing and chunking.
    """
    
    # Mock UploadFile
    file_mock = Mock(spec=UploadFile)
    file_mock.filename = "integration_test.txt"
    file_mock.content_type = "text/plain"
    async def mock_read_integration():
        return test_content.encode('utf-8')
    async def mock_seek_integration(pos):
        return None
    file_mock.read = mock_read_integration
    file_mock.seek = mock_seek_integration
    
    try:
        # Step 1: Validate and upload file
        upload_result = await validate_file(settings, file_mock)
        print(f"  ✓ File validated and uploaded: {upload_result.filename}")
        
        # Step 2: Preprocess the uploaded file
        documents = await preprocess_uploaded_file(settings, upload_result)
        print(f"  ✓ File preprocessed into {len(documents)} chunks")
        
        # Step 3: Verify the complete pipeline
        total_content = ''.join([doc.page_content for doc in documents])
        
        # The content should be preserved (minus whitespace normalization)
        original_words = set(test_content.split())
        processed_words = set(total_content.split())
        
        # Most words should be preserved
        word_preservation = len(original_words & processed_words) / len(original_words)
        assert word_preservation > 0.8, f"Word preservation too low: {word_preservation}"
        
        print(f"  ✓ Content preservation: {word_preservation:.2%}")
        print("  ✅ Integration test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting document dependencies tests...\n")
    
    tests = [
        test_validate_file(),
        test_preprocess_uploaded_file(),
        test_file_upload_integration()
    ]
    
    results = await asyncio.gather(*tests)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Document dependencies are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
