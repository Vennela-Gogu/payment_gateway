# FastAPI Docs Authentication Guide

## Issue: "Authorize" Button Not Showing

If you don't see the "Authorize" button in FastAPI docs (`http://localhost:8000/docs`), here's how to test authenticated endpoints:

## Method 1: Manual Headers in "Try it out"

1. **Open** http://localhost:8000/docs
2. **Click on an authenticated endpoint** (e.g., `POST /api/v1/orders`)
3. **Click "Try it out"**
4. **Scroll down** to find the request section
5. **Look for a way to add headers**:
   - Some FastAPI versions show a "Headers" section
   - Or you may need to use the "cURL" tab to see the full request
6. **Add these headers manually**:
   ```
   X-API-Key: key_test_abc123
   X-API-Secret: secret_test_xyz789
   ```

## Method 2: Use the "Authorize" Button (After Server Restart)

The code has been updated to add security schemes. **Restart your API server** to see the "Authorize" button:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd backend
uvicorn app.main:app --reload
```

After restarting, you should see:
- An "Authorize" button at the top right of the docs page
- Click it to enter your API credentials
- All authenticated endpoints will automatically use these credentials

## Method 3: Use Alternative Testing Tools

If the docs don't work well, use:

1. **Postman** - Import the OpenAPI schema from `http://localhost:8000/openapi.json`
2. **curl/PowerShell** - See `QUICK_TEST.md` for commands
3. **Python script** - Run `python test_manual_simple.py`

## Method 4: Check OpenAPI Schema

Verify the security schemes are included:

1. Open: http://localhost:8000/openapi.json
2. Search for `"securitySchemes"` - it should show:
```json
"securitySchemes": {
  "ApiKeyAuth": {
    "type": "apiKey",
    "in": "header",
    "name": "X-API-Key"
  },
  "ApiSecretAuth": {
    "type": "apiKey",
    "in": "header",
    "name": "X-API-Secret"
  }
}
```

If this is present, the "Authorize" button should appear after server restart.

## Quick Test Without "Authorize" Button

Even without the "Authorize" button, you can test endpoints:

1. Click on `POST /api/v1/orders`
2. Click "Try it out"
3. Fill in the request body:
```json
{
  "amount": 50000,
  "currency": "INR",
  "receipt": "test_001"
}
```
4. **Before clicking "Execute"**, check if there's a way to add headers
5. If not, use the **cURL** tab to see the full command with headers
6. Copy the cURL command and modify it to include:
   ```
   -H "X-API-Key: key_test_abc123" \
   -H "X-API-Secret: secret_test_xyz789"
   ```

## Troubleshooting

**If "Authorize" button still doesn't appear after restart:**

1. Check browser console for errors (F12)
2. Clear browser cache and refresh
3. Try a different browser
4. Check if the server logs show any errors
5. Verify the OpenAPI schema includes securitySchemes (see Method 4 above)
