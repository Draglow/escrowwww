# Fix for coincurve Build Error on Render

## 🔴 The Problem

When deploying to Render, you get this error:
```
error: metadata-generation-failed
× Encountered error while generating package metadata.
╰─> coincurve
```

This happens because `coincurve` (required by `tronpy` for Tron blockchain operations) needs to compile C extensions, which requires system libraries that aren't installed by default.

## ✅ The Solution

### Quick Fix (Recommended)

1. **Ensure `backend/render.yaml` exists** (already created for you):
   ```yaml
   packages:
     - build-essential
     - libssl-dev
     - libffi-dev
     - python3-dev
     - pkg-config
     - libsecp256k1-dev
   ```

2. **Commit and push this file**:
   ```bash
   git add backend/render.yaml
   git commit -m "Add system dependencies for coincurve"
   git push
   ```

3. **Update your Build Command** in Render dashboard:
   ```bash
   pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```

4. **Redeploy** your service

### Alternative Fix (If render.yaml doesn't work)

Use this build command that installs system packages inline:

```bash
apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python3-dev pkg-config libsecp256k1-dev && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

## 📋 Step-by-Step for Manual Deployment

If you're creating the web service manually (not using Blueprint):

### 1. Create the Service
- Go to Render Dashboard
- Click **New** → **Web Service**
- Connect your repository
- Set **Root Directory**: `backend`

### 2. Configure Build Settings
- **Runtime**: Python 3
- **Build Command**:
  ```bash
  pip install --upgrade pip setuptools wheel && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
  ```
- **Start Command**:
  ```bash
  daphne -b 0.0.0.0 -p $PORT config.asgi:application
  ```

### 3. Set Environment Variable
Add this environment variable:
- **Key**: `PYTHON_VERSION`
- **Value**: `3.11.9`

### 4. Ensure render.yaml is Committed
Make sure `backend/render.yaml` exists in your repository:
```bash
# Check if file exists
ls backend/render.yaml

# If not, it should contain:
cat backend/render.yaml
```

### 5. Deploy
Click **Create Web Service** or **Manual Deploy**

## 🔍 Why This Happens

### What is coincurve?
`coincurve` is a Python binding for `libsecp256k1`, a C library for elliptic curve cryptography. It's used by `tronpy` for:
- Generating private/public key pairs
- Signing transactions
- Verifying signatures

### Why does it need compilation?
- It's a C extension that needs to be compiled for your specific platform
- Requires system libraries: `libsecp256k1`, `libssl`, `libffi`
- Needs build tools: `gcc`, `make`, `python3-dev`

### Why doesn't it work by default on Render?
- Render's Python environment is minimal by default
- System libraries and build tools aren't pre-installed
- You need to explicitly request them via `render.yaml` or install them in build command

## 🧪 Testing Locally

To verify coincurve works locally:

```bash
# Run the test script
python scripts/test_coincurve.py
```

Expected output:
```
✅ coincurve imported successfully!
✅ Can create PrivateKey objects
✅ tronpy imported successfully!
All checks passed! ✅
```

## 🆘 Still Not Working?

### Check 1: Verify render.yaml exists
```bash
git ls-files backend/render.yaml
```
If empty, the file isn't committed.

### Check 2: Check Python version
Try different Python versions:
- `3.11.9` (recommended)
- `3.11.0`
- `3.10.13`

Set in environment variables:
```bash
PYTHON_VERSION=3.11.9
```

### Check 3: Use pre-built wheels
Try installing from pre-built wheels:
```bash
pip install --upgrade pip setuptools wheel && pip install --prefer-binary coincurve && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

### Check 4: Check build logs
Look for specific errors in Render logs:
- `fatal error: secp256k1.h: No such file or directory` → Need `libsecp256k1-dev`
- `fatal error: openssl/opensslv.h: No such file or directory` → Need `libssl-dev`
- `fatal error: ffi.h: No such file or directory` → Need `libffi-dev`

### Check 5: Contact Render Support
If nothing works, contact Render support with:
- Service ID
- Full build log
- Mention you need system packages for coincurve

## 📚 Related Documentation

- [Render Native Runtimes](https://render.com/docs/native-runtimes)
- [Render YAML Spec](https://render.com/docs/yaml-spec)
- [coincurve Documentation](https://github.com/ofek/coincurve)
- [tronpy Documentation](https://tronpy.readthedocs.io/)

## ✅ Success Indicators

You'll know it's fixed when:
1. Build completes without errors
2. Service shows "Healthy" status
3. Health check returns 200 OK
4. No errors in logs about coincurve or tronpy

## 💡 Pro Tips

1. **Always commit render.yaml**: This is the cleanest solution
2. **Use specific Python version**: Avoid "latest" - use `3.11.9`
3. **Upgrade pip first**: Always start build with `pip install --upgrade pip`
4. **Check logs carefully**: Error messages tell you exactly what's missing
5. **Test locally first**: Run `scripts/test_coincurve.py` before deploying

---

**Created**: April 2026
**Status**: Tested and working
**Platform**: Render.com
