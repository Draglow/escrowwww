# Frontend Setup Guide

Quick guide to set up and run the Next.js frontend.

**Last Updated:** April 23, 2026

---

## Quick Fix for Missing Dependencies

### Error: `Cannot find module 'tailwindcss-animate'`

**Solution:**

The `tailwindcss-animate` package was missing. I've added it to `package.json`.

Now you just need to install dependencies:

**Windows (Command Prompt):**
```cmd
cd frontend
install_dependencies.bat
```

**Or manually:**
```cmd
cd frontend
npm install
```

**Mac/Linux:**
```bash
cd frontend
npm install
```

---

## Complete Frontend Setup

### Step 1: Navigate to Frontend Directory

```cmd
cd C:\Users\boob\Desktop\escrow\frontend
```

### Step 2: Install Dependencies

```cmd
npm install
```

This will install all required packages including:
- Next.js 14
- React 18
- Tailwind CSS
- Radix UI components
- Zustand (state management)
- React Query
- And more...

### Step 3: Configure Environment Variables

```cmd
copy .env.local.example .env.local
notepad .env.local
```

**Configure `.env.local`:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_TELEGRAM_BOT_NAME=YourBotName
```

### Step 4: Start Development Server

```cmd
npm run dev
```

You should see:
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully
```

### Step 5: Open in Browser

Open your browser and go to:
- **Frontend:** http://localhost:3000

---

## Troubleshooting

### Error: `npm: command not found`

Node.js is not installed or not in PATH.

**Solution:**
1. Download Node.js from https://nodejs.org/
2. Install it (make sure to check "Add to PATH")
3. Restart your terminal
4. Verify: `node --version`

### Error: `Cannot find module 'xxx'`

Missing dependencies.

**Solution:**
```cmd
# Delete node_modules and package-lock.json
rmdir /s /q node_modules
del package-lock.json

# Reinstall
npm install
```

### Error: `Port 3000 is already in use`

Another process is using port 3000.

**Solution:**

**Option 1 - Kill the process:**
```cmd
# Find process using port 3000
netstat -ano | findstr :3000

# Kill it (replace <PID> with actual PID)
taskkill /PID <PID> /F
```

**Option 2 - Use different port:**
```cmd
set PORT=3001
npm run dev
```

### Error: `Module build failed`

Build cache issue.

**Solution:**
```cmd
# Delete .next folder
rmdir /s /q .next

# Restart dev server
npm run dev
```

### Error: `Failed to compile`

TypeScript or ESLint errors.

**Solution:**
```cmd
# Check for errors
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix

# Type check
npx tsc --noEmit
```

---

## Development Workflow

### Making Changes

1. Edit files in `src/` directory
2. Next.js automatically reloads
3. Changes appear instantly in browser

### File Structure

```
frontend/
├── src/
│   ├── app/              # Next.js 14 App Router
│   │   ├── page.tsx      # Home page
│   │   ├── layout.tsx    # Root layout
│   │   ├── globals.css   # Global styles
│   │   ├── login/        # Login page
│   │   └── dashboard/    # Dashboard pages
│   ├── components/       # React components
│   │   ├── ui/          # UI components (buttons, cards, etc.)
│   │   ├── deals/       # Deal-related components
│   │   ├── wallet/      # Wallet components
│   │   └── profile/     # Profile components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utility functions
│   └── types/           # TypeScript types
├── public/              # Static files
├── package.json         # Dependencies
└── tailwind.config.ts   # Tailwind configuration
```

### Common Commands

```cmd
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Fix linting issues
npm run lint -- --fix

# Type check
npx tsc --noEmit
```

---

## Testing the Frontend

### 1. Check Home Page

Open: http://localhost:3000

You should see the landing page.

### 2. Check Login Page

Open: http://localhost:3000/login

You should see the Telegram login button.

### 3. Check Dashboard (requires login)

Open: http://localhost:3000/dashboard

You'll be redirected to login if not authenticated.

### 4. Check API Connection

Open browser console (F12) and check for:
- No CORS errors
- API requests to http://localhost:8000

---

## Production Build

### Build for Production

```cmd
npm run build
```

This creates an optimized production build in `.next/` folder.

### Test Production Build Locally

```cmd
npm start
```

This starts the production server on port 3000.

### Environment Variables for Production

Create `.env.production`:
```env
NEXT_PUBLIC_API_URL=https://api.escrow.example.com
NEXT_PUBLIC_WS_URL=wss://api.escrow.example.com
NEXT_PUBLIC_TELEGRAM_BOT_NAME=YourBotName
```

---

## Integration with Backend

### Make Sure Backend is Running

The frontend needs the backend API to work.

**Terminal 1 - Backend:**
```cmd
cd backend
venv\Scripts\activate
python manage.py runserver
```

**Terminal 2 - Frontend:**
```cmd
cd frontend
npm run dev
```

### Test API Connection

1. Open browser console (F12)
2. Go to http://localhost:3000
3. Check Network tab
4. You should see requests to http://localhost:8000

### CORS Configuration

The backend is configured to allow requests from:
- http://localhost:3000
- http://127.0.0.1:3000

If you use a different port, update `backend/.env`:
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## Dependencies Installed

### Core
- **Next.js 14** - React framework
- **React 18** - UI library
- **TypeScript** - Type safety

### UI Components
- **Tailwind CSS** - Styling
- **tailwindcss-animate** - Animations
- **Radix UI** - Accessible components
- **Lucide React** - Icons

### State Management
- **Zustand** - State management
- **React Query** - Server state

### Utilities
- **Axios** - HTTP client
- **clsx** - Class names utility
- **date-fns** - Date formatting
- **qrcode.react** - QR code generation

---

## Next Steps

After frontend is running:

1. ✅ **Test the application**
   - Create a test user in Django admin
   - Try logging in
   - Test wallet features
   - Test deal creation

2. ✅ **Configure Telegram Bot**
   - Create bot via @BotFather
   - Add token to backend `.env`
   - Update `NEXT_PUBLIC_TELEGRAM_BOT_NAME`

3. ✅ **Read documentation**
   - API_DOCUMENTATION.md - API reference
   - LOCAL_DEVELOPMENT.md - Development guide
   - ARCHITECTURE.md - System design

---

## Quick Reference

**Install dependencies:**
```cmd
cd frontend
npm install
```

**Start dev server:**
```cmd
npm run dev
```

**Build for production:**
```cmd
npm run build
npm start
```

**Fix issues:**
```cmd
# Delete cache
rmdir /s /q .next node_modules
npm install
npm run dev
```

---

## Complete Startup Sequence

To run the entire application:

**Terminal 1 - Backend:**
```cmd
cd backend
venv\Scripts\activate
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```cmd
cd backend
venv\Scripts\activate
celery -A config worker -l info --pool=solo
```

**Terminal 3 - Celery Beat:**
```cmd
cd backend
venv\Scripts\activate
celery -A config beat -l info
```

**Terminal 4 - Frontend:**
```cmd
cd frontend
npm run dev
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Admin: http://localhost:8000/admin

---

**Last Updated:** April 23, 2026  
**Version:** 1.0.0
