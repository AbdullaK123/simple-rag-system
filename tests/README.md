# DocumentService Testing

This directory contains comprehensive unit tests for the `DocumentService` class.

## Test Structure

### Unit Tests (`TestDocumentService`)
- **Add Operations**: Tests for `add_document()` and `add_documents()` methods
- **Update Operations**: Tests for `update_document()` method  
- **Delete Operations**: Tests for `delete_document()`, `delete_documents()`, `delete_by_source()`, and `clear_collection()` methods
- **Search Operations**: Tests for `similarity_search()` with and without scores
- **Utility Operations**: Tests for `get_document_count()`, `list_sources()`, and `get_stats()` methods

### Integration Tests (`TestDocumentServiceIntegration`)
- Placeholder for integration tests that would use real Chroma instances
- Currently skipped as they require additional setup

## Running Tests

### Run All Tests
```bash
python3 -m pytest tests/test_document_service.py -v
```

### Run Only Unit Tests
```bash
python3 -m pytest tests/test_document_service.py::TestDocumentService -v
```

### Run Specific Test
```bash
python3 -m pytest tests/test_document_service.py::TestDocumentService::test_add_document_success -v
```

### Run Tests with Coverage (if coverage is installed)
```bash
python3 -m pytest tests/test_document_service.py --cov=app.services.documents --cov-report=html
```

## Test Categories

The tests use pytest markers to categorize different types of tests:

- `@pytest.mark.unit`: Unit tests that mock external dependencies
- `@pytest.mark.integration`: Integration tests that require real external services
- `@pytest.mark.slow`: Tests that take longer to run

### Filter by Category
```bash
# Run only unit tests
python3 -m pytest -m unit

# Run everything except slow tests  
python3 -m pytest -m "not slow"
```

## Test Dependencies

The following packages are required for testing:
- `pytest`: Main testing framework
- `pytest-asyncio`: Support for async/await tests
- `pytest-mock`: Enhanced mocking capabilities

Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-mock
```

## Mocking Strategy

The tests use comprehensive mocking to avoid dependencies on:
- OpenAI API calls (embedding generation)
- Chroma vector database operations
- File system operations

This ensures tests run fast and don't require external services or API keys.

## Test Coverage

The test suite covers:
- ✅ Success scenarios for all CRUD operations
- ✅ Error handling and exception scenarios  
- ✅ Edge cases (empty collections, missing documents, etc.)
- ✅ Data validation and type checking
- ✅ Async operation support
- ✅ Search functionality with and without scores
- ✅ Collection statistics and metadata operations

## Adding New Tests

When adding new functionality to `DocumentService`:

1. Add corresponding unit tests following the existing patterns
2. Mock external dependencies using `pytest.Mock` or `AsyncMock`
3. Test both success and failure scenarios
4. Use descriptive test names and docstrings
5. Add appropriate pytest markers

### Test Template
```python
@pytest.mark.unit
async def test_new_method_success(self, document_service):
    """Test successful execution of new method."""
    # Setup mocks
    document_service.store.new_method = AsyncMock(return_value="expected_result")
    
    # Execute
    result = await document_service.new_method("input")
    
    # Assert
    assert result.success is True
    assert result.data == "expected_result"
    document_service.store.new_method.assert_called_once_with("input")
```
