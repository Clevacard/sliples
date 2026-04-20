# Content Security Policy (CSP) Configuration for Sliples Recorder

## Overview

The Sliples recorder snippet requires external script loading from `https://sliples.agantis.in`. If your website has strict Content Security Policy (CSP) headers, you may see errors blocking the recorder from loading.

## Error Messages

You may see errors like:

```
Refused to connect because it violates the document's Content Security Policy
Fetch API cannot load https://sliples.agantis.in/api/v1/recorder/snippet.js
```

This means the website's CSP headers don't allow loading scripts from the Sliples domain.

## Solution: Update CSP Headers

### Required CSP Directives

Add `https://sliples.agantis.in` to your CSP headers:

```
script-src: 'self' https://sliples.agantis.in
connect-src: 'self' https://sliples.agantis.in
```

### Full Example

**Before (blocked):**
```
Content-Security-Policy: 
  default-src 'self'; 
  script-src 'self' https://www.google-analytics.com; 
  connect-src 'self' https://www.google-analytics.com;
```

**After (allows Sliples):**
```
Content-Security-Policy: 
  default-src 'self'; 
  script-src 'self' https://www.google-analytics.com https://sliples.agantis.in; 
  connect-src 'self' https://www.google-analytics.com https://sliples.agantis.in;
```

## Platform-Specific Configuration

### Apache (.htaccess)

```apache
<IfModule mod_headers.c>
  Header set Content-Security-Policy "script-src 'self' https://sliples.agantis.in; connect-src 'self' https://sliples.agantis.in;"
</IfModule>
```

### Nginx

```nginx
add_header Content-Security-Policy "script-src 'self' https://sliples.agantis.in; connect-src 'self' https://sliples.agantis.in;";
```

### Express.js / Node.js

```javascript
app.use((req, res, next) => {
  res.setHeader(
    'Content-Security-Policy',
    "script-src 'self' https://sliples.agantis.in; connect-src 'self' https://sliples.agantis.in;"
  );
  next();
});
```

### Python / Flask

```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = \
        "script-src 'self' https://sliples.agantis.in; connect-src 'self' https://sliples.agantis.in;"
    return response
```

### PHP

```php
header("Content-Security-Policy: script-src 'self' https://sliples.agantis.in; connect-src 'self' https://sliples.agantis.in;");
```

### Django

```python
# settings.py
SECURE_CONTENT_SECURITY_POLICY = "script-src 'self' https://sliples.agantis.in; connect-src 'self' https://sliples.agantis.in;"
```

## Testing Your CSP Configuration

### 1. Check Current CSP Headers

Open browser DevTools (F12) and go to the **Network** tab:

1. Reload the page
2. Click on the main document/page request
3. Go to **Response Headers** tab
4. Look for `Content-Security-Policy` header
5. Verify it includes `https://sliples.agantis.in`

### 2. Try Embedding the Snippet

Paste the Slipes snippet code into your page and reload:

```html
<script src="https://sliples.agantis.in/api/v1/recorder/snippet.js?api_key=..."></script>
<script>
  SliplesRecorder.init({...});
</script>
```

### 3. Check Browser Console

Open Developer Tools Console (F12 → Console) and verify:

- ✓ No CSP violation errors
- ✓ Sliples message: `[Sliples] Recorder loaded`
- ✓ Snippet initialized successfully

## Temporary Solutions

### For Development/Testing

**Disable CSP entirely (development only):**

```javascript
// Temporarily remove CSP for testing
// DO NOT use in production!
```

Or use browser extensions to disable CSP temporarily:

- Chrome: "Disable Content-Security Policy" extension
- Firefox: "Disable CSP" extension

### Use Incognito/Private Window

Some websites have different CSP policies for private browsing. Try:

1. Open an incognito window (Ctrl+Shift+N / Cmd+Shift+N)
2. Navigate to your website
3. Embed the snippet
4. Try recording

This helps test if CSP is the issue.

## Alternative: Inline Script Embedding

For websites with very strict CSP policies that don't allow inline scripts, contact Sliples support for alternative embedding options.

## Subdomain Configuration

If your website uses subdomains, you may need to allow them:

```
script-src: 'self' https://sliples.agantis.in https://*.yourdomain.com
connect-src: 'self' https://sliples.agantis.in https://*.yourdomain.com
```

## Best Practices

1. **Use HTTPS** - `https://sliples.agantis.in` (not `http://`)
2. **Be Specific** - List exact domains instead of wildcards when possible
3. **Test Thoroughly** - Verify snippets work after CSP changes
4. **Document Changes** - Track CSP modifications in your configuration
5. **Version Control** - Store CSP configs in git with other config
6. **Monitor** - Watch browser console for new CSP violations

## Troubleshooting

### Still seeing CSP errors after updating headers?

1. **Clear browser cache** - Cmd+Shift+R / Ctrl+Shift+R
2. **Verify headers were applied** - Check Network tab again
3. **Check multiple header locations** - Might be in multiple places:
   - Web server config (Apache, Nginx)
   - Application code (Express, Django, etc.)
   - CDN configuration
   - Load balancer configuration
4. **Reload the entire site** - Full browser refresh, not just page
5. **Test in different browser** - Rule out browser caching

### CSP header not being set?

1. Check if CSP is being overridden elsewhere
2. Verify file permissions and syntax
3. Restart your web server after changes
4. Check for multiple CSP headers (use first one or merge them)

## Examples by Framework

### React (Create React App)

Edit `public/index.html`:

```html
<head>
  <meta http-equiv="Content-Security-Policy" 
        content="script-src 'self' https://sliples.agantis.in; connect-src 'self' https://sliples.agantis.in;">
  <!-- Sliples Recorder -->
  <script src="https://sliples.agantis.in/api/v1/recorder/snippet.js?api_key=..."></script>
</head>
```

### Next.js

In `next.config.js`:

```javascript
const withCSP = require('next-csp');

module.exports = withCSP({
  csp: {
    directives: {
      scriptSrc: ["'self'", "https://sliples.agantis.in"],
      connectSrc: ["'self'", "https://sliples.agantis.in"],
    },
  },
});
```

### Vue.js

Use `vue.config.js` or configure in your web server.

## Support

If you're having trouble configuring CSP:

1. Check [Recording User Guide - Troubleshooting](./RECORDING_USER_GUIDE.md#troubleshooting)
2. Review the platform-specific examples above
3. Contact your website administrator or DevOps team
4. Reach out to Sliples support with:
   - Your current CSP headers
   - Error messages from browser console
   - Your web server/framework type

## References

- [MDN: Content-Security-Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy)
- [CSP Directive Reference](https://content-security-policy.com/)
- [OWASP CSP Guide](https://owasp.org/www-community/attacks/Content_Security_Policy)
