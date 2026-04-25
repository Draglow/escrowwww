# Render Deployment Troubleshooting Guide

Common issues and solutions when deploying to Render.

## 🔴 Build Failures

### Issue: Python dependencies fail to install

**Error Message:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**
1. Check `requirements.txt` for version conflicts
2. Pin specific versions instead of using `>=`
3. Ensure Python version matches in `runtime.txt`
4. Try clearing build cache and redeploying

```bash
# In Render Dashboard:
Service → Manual Deploy → Clear build cache & deploy
```

### Issue: Node modules installation fails

**Error Message:**
```
npm ERR! code ENOTFOUND
npm ERR! network request failed
```

**Solutions:**
1. Check `package.json` for invalid dependencies
2. Verify Node version in environment variables
3. Clear build cache and retry
4. Check for private packages requiring authentication

### Issue: Static files not collected

**Error Message:**
```
django.core.exceptions.ImproperlyConfigured: You're using the staticfiles app without having set the STATIC_ROOT setting
```

**Solutions:**
1. Verify `STATIC_ROOT` is set in `settings.py`:
```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

2. Ensure build command includes:
```bash
python manage.py collectstatic --noinput
```

---

## 🔴 Runtime Errors

### Issue: DisallowedHost error

**Error Message:**
```
DisallowedHost at /
Invalid HTTP_HOST header: 'your-app.onrender.com'
```

**Solutions:**
1. Add your Render URL to `ALLOWED_HOSTS`:
```bash
ALLOWED_HOSTS=your-backend.onrender.com,your-frontend.onrender.com
```

2. Ensure no extra spaces in the environment variable
3. Include both backend and frontend URLs
4. Restart the service after updating

### Issue: Database connection refused

**Error Message:**
```
django.db.utils.OperationalError: could not connect to server
```

**Solutions:**
1. Verify `DATABASE_URL` is set correctly
2. Check PostgreSQL service is running
3. Ensure database is in same region as web service
4. Check database connection limit not exceeded

```bash
# Test connection in shell:
cd backend
python manage.py check --database default
```

### Issue: Redis connection failed

**Error Message:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**
1. Verify `REDIS_URL` is set correctly
2. Check Redis service is running
3. Ensure Redis is in same region as web service
4. Test connection:

```python
# In Django shell:
from django.core.cache import cache
cache.set('test', 'value')
print(cache.get('test'))
```

### Issue: Celery worker not processing tasks

**Error Message:**
```
No nodes replied within time constraint
```

**Solutions:**
1. Check Celery worker service is running
2. Verify `CELERY_BROKER_URL` matches `REDIS_URL`
3. Restart worker service
4. Check worker logs for errors

```bash
# Test Celery connection:
cd backend
celery -A config inspect ping
```

---

## 🔴 CORS Errors

### Issue: CORS policy blocking requests

**Error Message (in browser console):**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solutions:**
1. Add frontend URL to `CORS_ALLOWED_ORIGINS`:
```bash
CORS_ALLOWED_ORIGINS=https://your-frontend.onrender.com
```

2. Ensure using `https://` (not `http://`)
3. No trailing slashes in URLs
4. Restart backend service after updating

### Issue: Credentials not included in CORS

**Error Message:**
```
The value of the 'Access-Control-Allow-Credentials' header is '' which must be 'true'
```

**Solutions:**
1. Verify `CORS_ALLOW_CREDENTIALS = True` in settings
2. Ensure frontend sends credentials:
```javascript
axios.defaults.withCredentials = true;
```

---

## 🔴 WebSocket Errors

### Issue: WebSocket connection failed

**Error Message:**
```
WebSocket connection to 'wss://...' failed
```

**Solutions:**
1. Use `wss://` (not `ws://`) for production
2. Verify Daphne is running (not Gunicorn)
3. Check `ASGI_APPLICATION` is set correctly
4. Ensure Redis is running for channel layers

```python
# In settings.py:
ASGI_APPLICATION = 'config.asgi.application'
```

### Issue: WebSocket closes immediately

**Error Message:**
```
WebSocket is closed before the connection is established
```

**Solutions:**
1. Check CORS settings include WebSocket origin
2. Verify authentication is working
3. Check channel layer configuration
4. Review WebSocket consumer code for errors

---

## 🔴 Authentication Errors

### Issue: Telegram authentication fails

**Error Message:**
```
Invalid hash
```

**Solutions:**
1. Verify `TELEGRAM_BOT_TOKEN` is correct
2. Check token has no extra spaces
3. Ensure frontend sends correct auth data
4. Verify hash calculation matches backend

### Issue: Token expired

**Error Message:**
```
Token has expired
```

**Solutions:**
1. Check token expiration settings
2. Implement token refresh mechanism
3. Clear old tokens from database
4. Verify system time is correct

### Issue: WebAuthn/Passkey registration fails

**Error Message:**
```
The relying party ID is not a registrable domain suffix of, nor equal to the current domain
```

**Solutions:**
1. Verify `WEBAUTHN_RP_ID` matches frontend domain:
```bash
# Backend:
WEBAUTHN_RP_ID=your-frontend.onrender.com

# Frontend:
NEXT_PUBLIC_WEBAUTHN_RP_ID=your-frontend.onrender.com
```

2. Must be domain only (no `https://` or port)
3. Must match exactly between frontend and backend
4. Cannot use `localhost` in production

---

## 🔴 Migration Errors

### Issue: Migration conflicts

**Error Message:**
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**Solutions:**
1. Check migration files are committed to Git
2. Ensure migrations run in correct order
3. If needed, fake migrations:
```bash
python manage.py migrate --fake <app_name> <migration_name>
```

4. For fresh database, run:
```bash
python manage.py migrate --run-syncdb
```

### Issue: Migration fails with data error

**Error Message:**
```
django.db.utils.DataError: value too long for type character varying
```

**Solutions:**
1. Check field max_length in models
2. Update existing data before migration
3. Create data migration to fix values
4. Increase field length if appropriate

---

## 🔴 Performance Issues

### Issue: Slow response times

**Symptoms:**
- API requests taking >5 seconds
- Timeouts on frontend
- High CPU usage

**Solutions:**
1. Upgrade service plan (more CPU/RAM)
2. Add database indexes:
```python
class Meta:
    indexes = [
        models.Index(fields=['user', 'created_at']),
    ]
```

3. Enable query optimization:
```python
# Use select_related and prefetch_related
deals = Deal.objects.select_related('buyer', 'seller').all()
```

4. Add Redis caching:
```python
from django.core.cache import cache
result = cache.get('key')
if not result:
    result = expensive_operation()
    cache.set('key', result, 300)
```

### Issue: Memory leaks

**Symptoms:**
- Memory usage constantly increasing
- Service crashes with OOM error

**Solutions:**
1. Check for unclosed database connections
2. Review Celery task memory usage
3. Add connection pooling
4. Upgrade to higher memory plan
5. Monitor with:
```bash
# In shell:
import psutil
print(f"Memory: {psutil.virtual_memory().percent}%")
```

### Issue: Database connection pool exhausted

**Error Message:**
```
django.db.utils.OperationalError: FATAL: remaining connection slots are reserved
```

**Solutions:**
1. Reduce `CONN_MAX_AGE` in settings
2. Upgrade database plan (more connections)
3. Use connection pooling (PgBouncer)
4. Close connections explicitly:
```python
from django.db import connection
connection.close()
```

---

## 🔴 SSL/HTTPS Issues

### Issue: Mixed content warnings

**Error Message (in browser console):**
```
Mixed Content: The page was loaded over HTTPS, but requested an insecure resource
```

**Solutions:**
1. Ensure all URLs use `https://` and `wss://`
2. Update environment variables:
```bash
NEXT_PUBLIC_API_URL=https://backend.onrender.com  # not http://
NEXT_PUBLIC_WS_URL=wss://backend.onrender.com     # not ws://
```

3. Check for hardcoded HTTP URLs in code

### Issue: SSL certificate not provisioning

**Symptoms:**
- Custom domain shows "Not Secure"
- Certificate status shows "Pending"

**Solutions:**
1. Verify DNS records are correct
2. Wait up to 24 hours for propagation
3. Check domain is not behind Cloudflare (orange cloud)
4. Contact Render support if >24 hours

---

## 🔴 Environment Variable Issues

### Issue: Environment variable not updating

**Symptoms:**
- Changed variable but old value still used
- Service not reflecting new configuration

**Solutions:**
1. Manually redeploy after changing variables:
```bash
Dashboard → Service → Manual Deploy
```

2. Check for typos in variable names
3. Ensure no spaces around `=` sign
4. Verify variable is not overridden elsewhere

### Issue: Secret key rotation breaks sessions

**Symptoms:**
- All users logged out
- "Invalid token" errors

**Solutions:**
1. This is expected when rotating `SECRET_KEY`
2. Warn users before rotation
3. Consider using multiple keys temporarily
4. Clear old sessions:
```bash
python manage.py clearsessions
```

---

## 🔴 Deployment Issues

### Issue: Deploy stuck on "Building"

**Symptoms:**
- Build running for >30 minutes
- No progress in logs

**Solutions:**
1. Cancel and retry deployment
2. Clear build cache
3. Check for infinite loops in build command
4. Contact Render support

### Issue: Deploy succeeds but service crashes

**Symptoms:**
- Build completes successfully
- Service shows "Unhealthy" status
- Logs show crash loop

**Solutions:**
1. Check logs for error messages
2. Verify start command is correct
3. Test start command locally
4. Check health check endpoint is accessible
5. Ensure all required environment variables are set

### Issue: Automatic deploys not triggering

**Symptoms:**
- Pushed to GitHub but no deploy
- Manual deploy works fine

**Solutions:**
1. Check auto-deploy is enabled:
```bash
Dashboard → Service → Settings → Auto-Deploy
```

2. Verify correct branch is configured
3. Check GitHub webhook is active
4. Re-connect repository if needed

---

## 🔴 Celery Issues

### Issue: Tasks not executing

**Symptoms:**
- Tasks queued but never run
- Worker shows no activity

**Solutions:**
1. Check worker service is running
2. Verify broker URL is correct
3. Restart worker service
4. Check for task routing issues:
```python
# In Django shell:
from celery import current_app
print(current_app.control.inspect().active())
```

### Issue: Tasks failing silently

**Symptoms:**
- Tasks marked as success but didn't execute
- No error logs

**Solutions:**
1. Add explicit error handling:
```python
@shared_task
def my_task():
    try:
        # task code
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise
```

2. Enable task result backend
3. Check task timeout settings
4. Review task logs in worker service

---

## 🔴 Frontend Issues

### Issue: Frontend shows blank page

**Symptoms:**
- White screen
- No errors in Render logs
- Browser console shows errors

**Solutions:**
1. Check browser console for JavaScript errors
2. Verify API URL is correct
3. Check CORS settings
4. Ensure environment variables are set
5. Test API endpoint directly:
```bash
curl https://your-backend.onrender.com/api/v1/health/
```

### Issue: API calls failing from frontend

**Error Message (in browser console):**
```
Failed to fetch
Network request failed
```

**Solutions:**
1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check backend is running and healthy
3. Verify CORS settings
4. Check network tab for actual error
5. Test with curl:
```bash
curl -v https://your-backend.onrender.com/api/v1/users/me/
```

---

## 🆘 Emergency Recovery

### Complete Service Failure

1. **Check Render Status:**
   - Visit https://status.render.com/
   - Check for platform-wide issues

2. **Review Recent Changes:**
   - Check recent deployments
   - Review environment variable changes
   - Look for code changes

3. **Rollback:**
   ```bash
   Dashboard → Service → Events → Previous Deploy → Rollback
   ```

4. **Restore Database:**
   ```bash
   Dashboard → Database → Backups → Select Backup → Restore
   ```

5. **Contact Support:**
   - Email: support@render.com
   - Include service ID and error logs

### Data Loss Prevention

1. **Regular Backups:**
   - Enable automatic database backups
   - Test restore procedures monthly
   - Keep backups for 30+ days

2. **Export Critical Data:**
   ```bash
   # In backend shell:
   python manage.py dumpdata > backup_$(date +%Y%m%d).json
   ```

3. **Monitor Disk Usage:**
   - Check database size regularly
   - Set up alerts for high usage
   - Plan for scaling

---

## 📞 Getting Help

### Before Contacting Support

1. Check this troubleshooting guide
2. Review Render documentation
3. Search Render community forum
4. Check service logs thoroughly
5. Try basic fixes (restart, clear cache)

### Information to Provide

When contacting support, include:
- Service ID
- Error messages (full text)
- Steps to reproduce
- Recent changes made
- Relevant log excerpts
- Screenshots if applicable

### Support Channels

- **Email:** support@render.com
- **Community:** https://community.render.com/
- **Status:** https://status.render.com/
- **Docs:** https://render.com/docs

---

## 🔍 Debugging Tools

### Check Service Health
```bash
curl https://your-backend.onrender.com/api/v1/health/detailed/
```

### Test Database Connection
```bash
# In backend shell:
python manage.py dbshell
\dt  # List tables
\q   # Quit
```

### Test Redis Connection
```bash
# In backend shell:
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

### Check Celery Status
```bash
# In worker shell:
celery -A config inspect stats
celery -A config inspect active
celery -A config inspect registered
```

### Monitor Resource Usage
```bash
# In service shell:
top
df -h
free -m
```

---

**Remember:** Most issues are configuration-related. Double-check environment variables, URLs, and service connections before assuming a code problem.

**Last Updated:** [Current Date]
