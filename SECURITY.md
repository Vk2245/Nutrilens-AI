# Security Policy — NutriLens AI

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Active |

## Reporting a Vulnerability

If you discover a security vulnerability in NutriLens AI, please report it responsibly:

1. **Do NOT** open a public GitHub issue.
2. Email: security@nutrilens.dev (or contact the team privately).
3. Include: description of the vulnerability, steps to reproduce, and potential impact.
4. We will acknowledge your report within 48 hours and provide a fix timeline.

## Security Architecture

### Data Protection
- All API keys stored in `.env` files — never committed to version control
- Firebase RTDB rules enforce `$uid === auth.uid` — users can only access their own data
- Image uploads validated with MIME type checking and Pillow.verify()
- All text inputs sanitized with HTML tag stripping (XSS prevention)

### API Security
- Rate limiting via `slowapi`: 10 requests/minute per user on AI endpoints
- Google reCAPTCHA v3 on food analysis endpoints (score threshold: 0.5)
- CORS restricted to explicit origins — no wildcard `*` in production
- Pydantic v2 validates all inputs before processing

### Firebase RTDB Rules
```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "$uid === auth.uid",
        ".write": "$uid === auth.uid"
      }
    }
  }
}
```

### Content Security Policy
Configured via Firebase Hosting headers and FastAPI middleware.
