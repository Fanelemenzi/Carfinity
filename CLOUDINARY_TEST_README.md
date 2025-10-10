# Cloudinary Integration Tests for Search Results

This directory contains comprehensive tests to verify that the `templates/search/search-results.html` template and its associated view can properly retrieve and display images from Cloudinary.

## Test Files

### 1. `search/tests/test_cloudinary_integration.py`
Comprehensive Django test suite covering:
- Cloudinary configuration validation
- Image upload and retrieval
- Template rendering with images
- Error handling scenarios
- Performance testing
- Security and access control

### 2. `test_cloudinary_search.py`
Standalone test runner that:
- Checks Cloudinary configuration
- Validates template integration
- Runs the full test suite
- Provides detailed reporting

### 3. `manual_cloudinary_test.py`
Quick manual test script for:
- Basic configuration checks
- Model validation
- Live upload testing
- Search functionality verification

### 4. `search/management/commands/test_cloudinary.py`
Django management command for:
- Configuration testing
- Test data creation
- Live integration testing
- Template validation

## How to Run the Tests

### Option 1: Full Test Suite (Recommended)
```bash
python test_cloudinary_search.py
```

### Option 2: Manual Quick Test
```bash
python manual_cloudinary_test.py
```

### Option 3: Django Management Command
```bash
python manage.py test_cloudinary --create-test-data --upload-test
```

### Option 4: Django Test Framework
```bash
python manage.py test search.tests.test_cloudinary_integration
```

## Prerequisites

### 1. Environment Setup
Ensure your `.env` file contains:
```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 2. Django Settings
Verify `carfinity/settings.py` includes:
```python
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

### 3. Required Packages
```bash
pip install cloudinary pillow django-cloudinary-storage
```

### 4. Database Migration
```bash
python manage.py migrate
```

## What the Tests Check

### ✅ Configuration Tests
- Cloudinary credentials are properly set
- Django settings are configured correctly
- Required packages are installed

### ✅ Model Tests
- `Vehicle` and `VehicleImage` models exist
- Required fields are present
- Relationships are properly defined

### ✅ Upload Tests
- Images can be uploaded to Cloudinary
- URLs are generated correctly
- Cleanup operations work

### ✅ View Tests
- Search results view is accessible
- VIN parameter handling works
- Response status is correct

### ✅ Template Tests
- Template renders without errors
- Image URLs are displayed correctly
- Error handling is implemented
- Modal functionality exists

### ✅ Integration Tests
- End-to-end search with images works
- Cloudinary URLs appear in rendered HTML
- Image metadata is displayed
- Multiple images are handled correctly

## Expected Test Results

### ✅ All Tests Pass
```
🎉 All tests passed! Cloudinary integration is working properly.
```

### ❌ Configuration Issues
```
❌ CLOUDINARY_CLOUD_NAME not set
❌ API key not configured
```
**Solution**: Check your `.env` file and Django settings.

### ❌ Model Issues
```
❌ Vehicle.vin field missing
❌ VehicleImage model not found
```
**Solution**: Run migrations and check model definitions.

### ❌ Template Issues
```
⚠️ Vehicle images loop not found
⚠️ Image modal functionality missing
```
**Solution**: Check template implementation in `search-results.html`.

### ❌ Upload Issues
```
❌ Cloudinary upload test failed: Invalid credentials
```
**Solution**: Verify Cloudinary account and API credentials.

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install cloudinary django-cloudinary-storage pillow
   ```

2. **Database Errors**
   ```bash
   python manage.py migrate
   python manage.py migrate vehicles
   python manage.py migrate search
   ```

3. **URL Resolution Errors**
   - Check `search/urls.py` exists
   - Verify URL patterns are correct
   - Ensure search app is in `INSTALLED_APPS`

4. **Template Not Found**
   - Check template path: `templates/search/search-results.html`
   - Verify template directories in settings
   - Ensure search app templates are configured

5. **Cloudinary Credentials**
   - Verify `.env` file exists and is loaded
   - Check Cloudinary dashboard for correct credentials
   - Ensure no typos in environment variable names

### Debug Mode

Run tests with verbose output:
```bash
python manage.py test search.tests.test_cloudinary_integration --verbosity=2
```

### Create Test Data

Generate test vehicle and images:
```bash
python manage.py test_cloudinary --create-test-data --vin=TEST123456789
```

## Test Coverage

The tests cover:
- ✅ Basic Cloudinary configuration
- ✅ Image upload and storage
- ✅ URL generation and access
- ✅ Template rendering with images
- ✅ Error handling and fallbacks
- ✅ Multiple image support
- ✅ Image metadata display
- ✅ Modal functionality
- ✅ Performance considerations
- ✅ Security and access control

## Next Steps

After running the tests:

1. **If all tests pass**: Your Cloudinary integration is working correctly!

2. **If tests fail**: 
   - Review the specific error messages
   - Check the troubleshooting section
   - Verify your configuration
   - Run individual test components

3. **For production deployment**:
   - Test with real vehicle data
   - Verify image upload workflows
   - Check performance with multiple images
   - Validate error handling scenarios

## Support

If you encounter issues not covered in this guide:
1. Check the Django and Cloudinary documentation
2. Verify your Cloudinary account status
3. Review the test output for specific error messages
4. Consider running tests in a clean virtual environment