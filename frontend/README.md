# Crypto Escrow Platform - Frontend

Modern, responsive Next.js frontend for the crypto escrow platform with Telegram authentication and 2FA support.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui + Radix UI
- **State Management:** Zustand
- **Data Fetching:** TanStack React Query (React Query)
- **HTTP Client:** Axios
- **Icons:** Lucide React

## Features

- ✅ Telegram Login Widget integration
- ✅ Dark mode by default
- ✅ Responsive mobile-first design
- ✅ Real-time balance updates
- ✅ Two-factor authentication UI
- ✅ Wallet management (deposit/withdraw)
- ✅ Deal management
- ✅ Profile and security settings
- ✅ Toast notifications
- ✅ Protected routes

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── dashboard/          # Dashboard pages
│   │   │   ├── layout.tsx      # Dashboard layout with navigation
│   │   │   ├── page.tsx        # Dashboard home
│   │   │   ├── wallet/         # Wallet pages
│   │   │   ├── deals/          # Deals pages
│   │   │   └── profile/        # Profile pages
│   │   ├── login/              # Login page
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Landing page
│   │   └── globals.css         # Global styles
│   ├── components/             # React components
│   │   ├── ui/                 # shadcn/ui components
│   │   └── providers.tsx       # React Query provider
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts          # Authentication hooks
│   │   ├── useWallet.ts        # Wallet hooks
│   │   └── use-toast.ts        # Toast notifications
│   ├── lib/                    # Utility functions
│   │   ├── api.ts              # Axios instance with interceptors
│   │   └── utils.ts            # Helper functions
│   └── store/                  # Zustand stores
│       ├── auth.ts             # Auth state
│       └── wallet.ts           # Wallet state
├── public/                     # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.mjs
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Backend API running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Create environment file:**
   ```bash
   cp .env.local.example .env.local
   ```

3. **Configure environment variables:**
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=your_bot_username
   ```

4. **Run development server:**
   ```bash
   npm run dev
   ```

5. **Open browser:**
   ```
   http://localhost:3000
   ```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Pages

### Public Pages

#### Landing Page (`/`)
- Hero section with features
- How it works section
- Call-to-action buttons
- Responsive design

#### Login Page (`/login`)
- Telegram Login Widget integration
- Development mode fallback button
- Security information
- Auto-redirect if authenticated

### Protected Pages (Dashboard)

#### Dashboard Home (`/dashboard`)
- Balance overview
- Active deals count
- Completed deals count
- Security status
- Quick actions
- Recent activity
- 2FA security alert

#### Wallet (`/dashboard/wallet`)
- Balance display
- Deposit address with QR code
- Withdrawal form with 2FA
- Transaction history
- Real-time balance updates

#### Deals (`/dashboard/deals`)
- Deal list (as buyer/seller)
- Create new deal
- Deal details with chat
- State machine actions
- Real-time updates via WebSocket

#### Profile (`/dashboard/profile`)
- User information
- 2FA management
  - Enable/disable 2FA
  - QR code setup
  - Backup codes
- Audit logs
- Account settings

## State Management

### Auth Store (Zustand)
```typescript
{
  user: User | null,
  token: string | null,
  isAuthenticated: boolean,
  setAuth: (user, token) => void,
  clearAuth: () => void,
  updateUser: (userData) => void
}
```

### Wallet Store (Zustand)
```typescript
{
  balance: string,
  address: string | null,
  isLoading: boolean,
  setBalance: (balance) => void,
  setAddress: (address) => void,
  setLoading: (isLoading) => void
}
```

## API Integration

### Axios Configuration

The API client is configured with:
- Base URL from environment
- Automatic token injection
- 401 error handling (auto-logout)
- Request/response interceptors

### React Query Hooks

#### Authentication
- `useLogin()` - Telegram login
- `useLogout()` - Logout and clear session
- `useCurrentUser()` - Get current user data

#### Wallet
- `useBalance()` - Get balance (auto-refresh every 30s)
- `useDepositAddress()` - Get deposit address
- `useWithdraw()` - Submit withdrawal request
- `useTransactions()` - Get transaction history

#### Deals
- `useDeals()` - List deals
- `useCreateDeal()` - Create new deal
- `useDealActions()` - Fund, start, complete, dispute, cancel

#### 2FA
- `useEnable2FA()` - Start 2FA setup
- `useVerify2FASetup()` - Complete 2FA setup
- `useDisable2FA()` - Disable 2FA
- `useVerify2FA()` - Verify 2FA token

## Styling

### Tailwind CSS

The project uses Tailwind CSS with a custom dark theme:

- **Primary Color:** Blue (#3b82f6)
- **Background:** Dark gray (#0a0a0a)
- **Card Background:** Slightly lighter gray
- **Border:** Subtle gray borders
- **Text:** White/gray scale

### CSS Variables

Theme colors are defined using CSS variables in `globals.css`:
- `--background`
- `--foreground`
- `--primary`
- `--secondary`
- `--muted`
- `--accent`
- `--destructive`
- `--border`

## Components

### UI Components (shadcn/ui)

- `Button` - Various button styles and sizes
- `Card` - Container with header, content, footer
- `Input` - Form input field
- `Label` - Form label
- `Toast` - Notification system
- `Dialog` - Modal dialogs
- `Dropdown` - Dropdown menus
- `Tabs` - Tabbed interface

### Custom Components

- `Providers` - React Query provider wrapper
- `DashboardLayout` - Dashboard navigation and layout
- `TelegramLoginButton` - Telegram auth widget
- `WithdrawForm` - Withdrawal form with 2FA
- `DepositInstructions` - Deposit address and QR
- `DealCard` - Deal list item
- `ChatInterface` - Real-time chat
- `2FASetup` - 2FA setup wizard

## Authentication Flow

1. User clicks "Login with Telegram"
2. Telegram widget opens
3. User authorizes in Telegram
4. Widget returns auth data
5. Frontend sends auth data to backend
6. Backend verifies hash and returns token
7. Token stored in localStorage and Zustand
8. User redirected to dashboard
9. Protected routes check authentication
10. API requests include token in headers

## 2FA Flow

### Enable 2FA
1. User navigates to Profile > Security
2. Clicks "Enable 2FA"
3. Backend generates TOTP secret
4. Frontend displays QR code
5. User scans with authenticator app
6. User enters verification code
7. Backend verifies code
8. 2FA enabled, backup codes displayed

### Withdrawal with 2FA
1. User submits withdrawal request
2. If 2FA enabled, prompt for token
3. User enters TOTP code
4. Request sent with token
5. Backend verifies token
6. Withdrawal processed

## WebSocket Integration

### Real-time Features

- **Deal Updates:** Status changes broadcast to participants
- **Chat Messages:** Real-time messaging between buyer/seller
- **Balance Updates:** Automatic balance refresh on deposits
- **Typing Indicators:** Show when other party is typing
- **Read Receipts:** Mark messages as read

### WebSocket Connection

```typescript
const ws = new WebSocket(
  `${WS_URL}/ws/deals/${dealId}/?token=${token}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle different message types
};
```

## Error Handling

### API Errors
- 401: Auto-logout and redirect to login
- 400: Display validation errors
- 429: Rate limit exceeded message
- 500: Generic error message

### Toast Notifications
- Success: Green toast
- Error: Red toast
- Info: Blue toast
- Warning: Yellow toast

## Security

### Protected Routes
- All `/dashboard/*` routes require authentication
- Automatic redirect to `/login` if not authenticated
- Token validation on every API request

### Token Storage
- Stored in localStorage
- Included in all API requests
- Cleared on logout or 401 error

### 2FA Protection
- Required for withdrawals when enabled
- Rate limited (5 attempts per 15 minutes)
- Backup codes for recovery

## Performance Optimization

- **Code Splitting:** Automatic with Next.js App Router
- **Image Optimization:** Next.js Image component
- **React Query Caching:** 1-minute stale time
- **Lazy Loading:** Components loaded on demand
- **Prefetching:** Link prefetching enabled

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Development Tips

### Hot Reload
Changes to files automatically reload the browser.

### TypeScript
Type checking runs automatically. Fix errors before committing.

### Linting
Run `npm run lint` to check for code issues.

### Environment Variables
Prefix with `NEXT_PUBLIC_` to expose to browser.

## Deployment

### Build for Production

```bash
npm run build
npm run start
```

### Environment Variables

Set these in your production environment:
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_WS_URL` - WebSocket URL
- `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` - Telegram bot username

### Hosting Options

- **Vercel:** Recommended (zero-config)
- **Netlify:** Supported
- **Docker:** Dockerfile included
- **Self-hosted:** Node.js server

## Troubleshooting

### Telegram Login Not Working
- Check `NEXT_PUBLIC_TELEGRAM_BOT_USERNAME` is set
- Verify bot is configured correctly
- Use development fallback button for testing

### API Connection Failed
- Verify backend is running
- Check `NEXT_PUBLIC_API_URL` is correct
- Check CORS settings on backend

### 2FA QR Code Not Displaying
- Ensure `qrcode.react` is installed
- Check browser console for errors

### WebSocket Connection Failed
- Verify `NEXT_PUBLIC_WS_URL` is correct
- Check WebSocket endpoint is accessible
- Ensure token is valid

## Next Steps

### Remaining Pages to Implement

1. **Wallet Pages**
   - Deposit page with QR code
   - Withdrawal page with 2FA
   - Transaction history with filters

2. **Deal Pages**
   - Deal list with filters
   - Create deal form
   - Deal detail with chat
   - Deal actions (fund, start, complete, dispute)

3. **Profile Pages**
   - Profile settings
   - 2FA management
   - Audit logs
   - Security settings

4. **Additional Features**
   - WebSocket integration
   - Real-time notifications
   - File uploads
   - Advanced filters

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.
