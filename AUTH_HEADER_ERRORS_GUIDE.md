# Potential Errors with X-API-Key and X-API-Secret Headers

## Overview

This document outlines potential errors you might encounter with authentication headers during automatic testing and how to handle them.

---

## ✅ Current Implementation Analysis

**Code Location**: `backend/app/auth.py`

```python
def authenticate(
    x_api_key: str = Header(...),
    x_api_secret: str = Header(...)
):
```

**How FastAPI Handles Headers:**
- FastAPI automatically converts header names:
  - `X-API-Key` → `x_api_key` (parameter name)
  - `X-API-Secret` → `x_api_secret` (parameter name)
- Headers are case-insensitive in HTTP, but FastAPI expects the exact format

---

## Potential Errors and Solutions

### 1. ❌ Missing Headers (422 Unprocessable Entity)

**Error**: 
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["header", "x-api-key"],
      "msg": "Field required"
    }
  ]
}
```

**Cause**: One or both headers are missing from the request.

**Solution**:
```python
# ✅ Correct - Include both headers
headers = {
    "X-API-Key": "key_test_abc123",
    "X-API-Secret": "secret_test_xyz789"
}

# ❌ Wrong - Missing headers
headers = {}  # Will cause 422 error
```

**Prevention**: Always include both headers in test scripts.

---

### 2. ❌ Invalid Credentials (401 Unauthorized)

**Error**:
```json
{
  "detail": {
    "error": {
      "code": "AUTHENTICATION_ERROR",
      "description": "Invalid API credentials"
    }
  }
}
```

**Causes**:
- Wrong API key or secret
- Credentials not seeded in database
- Database connection issues
- Typo in credentials

**Solution**:
```python
# ✅ Correct credentials (from seed.py)
API_KEY = "key_test_abc123"
API_SECRET = "secret_test_xyz789"

# ❌ Wrong - Will cause 401
API_KEY = "wrong_key"
API_SECRET = "wrong_secret"
```

**Prevention**: 
- Run seed script before testing: `python -m app.seed`
- Verify credentials match seed data
- Check database connection

---

### 3. ⚠️ Header Name Case Sensitivity

**Potential Issue**: While HTTP headers are case-insensitive, some clients might send them differently.

**FastAPI Behavior**:
- FastAPI accepts: `X-API-Key`, `x-api-key`, `X-Api-Key` (all work)
- But parameter names must match: `x_api_key`, `x_api_secret`

**Solution**: Use consistent header names in tests:
```python
# ✅ All of these work:
headers = {"X-API-Key": "key", "X-API-Secret": "secret"}
headers = {"x-api-key": "key", "x-api-secret": "secret"}
headers = {"X-Api-Key": "key", "X-Api-Secret": "secret"}
```

**Best Practice**: Use `X-API-Key` and `X-API-Secret` (capitalized) for consistency.

---

### 4. ❌ Database Connection Errors

**Error**: 
```
Internal Server Error (500)
Database connection failed
```

**Causes**:
- Database not running
- Wrong DATABASE_URL
- Database not initialized
- Network issues

**Solution**:
```bash
# Check database is running
docker-compose ps

# Verify DATABASE_URL is set
echo $DATABASE_URL

# Seed database
python -m app.seed
```

**Prevention**: 
- Ensure database is running before tests
- Verify environment variables
- Add connection retry logic in tests

---

### 5. ⚠️ Header Value Encoding Issues

**Potential Issue**: Special characters in header values might cause problems.

**Current Values** (safe):
```python
API_KEY = "key_test_abc123"      # ✅ Alphanumeric + underscore
API_SECRET = "secret_test_xyz789" # ✅ Alphanumeric + underscore
```

**If you need special characters**:
- URL encode if necessary
- Avoid newlines, quotes, or control characters
- Test with various characters if needed

---

### 6. ❌ Content-Type Header Missing

**Error**: Request might fail if Content-Type is missing for POST requests.

**Solution**:
```python
# ✅ Correct - Include Content-Type
headers = {
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET,
    "Content-Type": "application/json"  # Important for POST
}

# ⚠️ Might work but not recommended
headers = {
    "X-API-Key": API_KEY,
    "X-API-Secret": API_SECRET
    # Missing Content-Type
}
```

---

### 7. ⚠️ Multiple Header Values

**Potential Issue**: Sending multiple values for the same header.

**HTTP Behavior**: 
- Some clients might send: `X-API-Key: value1, value2`
- FastAPI will use the first value or might error

**Solution**: Ensure only one value per header:
```python
# ✅ Correct
headers = {"X-API-Key": "single_value"}

# ❌ Avoid
headers = {"X-API-Key": "value1, value2"}  # Might cause issues
```

---

### 8. ❌ Header Name Typos

**Common Mistakes**:
- `X-API-Key` vs `X-Api-Key` vs `X-API-KEY`
- `X-API-Secret` vs `X-Api-Secret` vs `X-API-SECRET`
- Missing hyphens: `XAPIKey` (won't work)

**Solution**: Use exact names from code:
```python
# ✅ Correct
"X-API-Key"
"X-API-Secret"

# ❌ Wrong
"X-Api-Key"      # Might work but inconsistent
"XAPIKey"        # Won't work
"x_api_key"      # Won't work (use in parameter, not header name)
```

---

## Testing Checklist

Before running automatic tests, verify:

- [ ] Database is running and accessible
- [ ] Database is seeded with test merchant
- [ ] Credentials match seed data:
  - Key: `key_test_abc123`
  - Secret: `secret_test_xyz789`
- [ ] Headers are included in all authenticated requests
- [ ] Header names are exactly: `X-API-Key` and `X-API-Secret`
- [ ] Content-Type is set for POST requests
- [ ] No typos in header values

---

## Error Handling in Tests

### Recommended Test Pattern

```python
def test_with_auth():
    headers = {
        "X-API-Key": "key_test_abc123",
        "X-API-Secret": "secret_test_xyz789",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=5
        )
        
        # Check for authentication errors
        if response.status_code == 401:
            print("ERROR: Authentication failed")
            print(f"Response: {response.json()}")
            return False
        
        # Check for missing headers
        if response.status_code == 422:
            print("ERROR: Missing required headers")
            print(f"Response: {response.json()}")
            return False
        
        return response.status_code == 201
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed - {e}")
        return False
```

---

## Common Test Failures

### Failure 1: "Field required" (422)
**Fix**: Add missing headers

### Failure 2: "Invalid API credentials" (401)
**Fix**: 
1. Check credentials are correct
2. Run seed script: `python -m app.seed`
3. Verify database connection

### Failure 3: "Internal Server Error" (500)
**Fix**:
1. Check database is running
2. Check database connection
3. Verify tables exist (run seed script)

### Failure 4: Connection timeout
**Fix**:
1. Verify API server is running
2. Check network connectivity
3. Increase timeout value

---

## Best Practices for Automatic Testing

1. **Validate Headers Before Tests**:
```python
def validate_auth_headers():
    required = ["X-API-Key", "X-API-Secret"]
    for header in required:
        if header not in AUTH_HEADERS:
            raise ValueError(f"Missing required header: {header}")
```

2. **Use Constants**:
```python
# ✅ Good
API_KEY = "key_test_abc123"
API_SECRET = "secret_test_xyz789"

# ❌ Bad - Hard to maintain
headers = {"X-API-Key": "key_test_abc123", ...}
```

3. **Add Retry Logic**:
```python
def make_request_with_retry(url, headers, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 401:  # Don't retry auth errors
                return response
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
    return response
```

4. **Test Error Cases**:
```python
# Test missing headers
# Test invalid credentials
# Test database connection failures
```

---

## Summary

**Most Common Errors**:
1. Missing headers → 422 error
2. Invalid credentials → 401 error
3. Database not seeded → 401 error
4. Database connection issues → 500 error

**Prevention**:
- Always include both headers
- Verify credentials match seed data
- Ensure database is running and seeded
- Use consistent header names
- Add proper error handling in tests
