"""
Telegram Bot for Crypto Escrow Platform
Handles all user interactions via Telegram
"""
import logging
import traceback
from decimal import Decimal

from django.conf import settings
from django.db import models  # ← must be at top, not bottom
from asgiref.sync import sync_to_async

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from apps.users.models import User, WebAuthnCredential
from apps.users.bridge_token import generate as bridge_generate
from apps.wallets.models import Wallet
from apps.deals.models import Deal
from apps.deals.services import DealService
from apps.wallets.services import WalletService

logger = logging.getLogger(__name__)

# Conversation states
(
    AWAITING_DEAL_SELLER,
    AWAITING_DEAL_TITLE,
    AWAITING_DEAL_DESCRIPTION,
    AWAITING_DEAL_AMOUNT,
    AWAITING_WITHDRAWAL_ADDRESS,
    AWAITING_WITHDRAWAL_AMOUNT,
    AWAITING_2FA_TOKEN,
) = range(7)


class EscrowBot:
    def __init__(self):
        self.application = None

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _close_old_db_connections():
        """Close stale DB connections before each sync DB call.

        Django connections are thread-local. sync_to_async dispatches to a
        thread-pool thread that may hold a connection that was closed by the
        database server (e.g. due to idle timeout). Closing it here forces
        Django to open a fresh connection on the next query.
        """
        from django.db import connections
        for conn in connections.all():
            conn.close_if_unusable_or_obsolete()

    @sync_to_async
    def get_or_create_user(self, telegram_user):
        """Get or create user from Telegram data, ensuring wallet exists."""
        self._close_old_db_connections()
        user, created = User.objects.get_or_create(
            telegram_id=telegram_user.id,
            defaults={
                "username": telegram_user.username or "",
                "first_name": telegram_user.first_name or "",
                "last_name": telegram_user.last_name or "",
            },
        )
        if created:
            WalletService.create_wallet(user)
        else:
            if not Wallet.objects.filter(user=user).exists():
                WalletService.create_wallet(user)
        return user

    @sync_to_async
    def get_user_wallet(self, user):
        """Safely fetch the user's wallet."""
        self._close_old_db_connections()
        try:
            return Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            return WalletService.create_wallet(user)

    @sync_to_async
    def get_available_balance(self, user):
        """Return available balance (balance minus locked funds)."""
        self._close_old_db_connections()
        # Re-fetch user to get fresh balance from DB
        user = User.objects.get(pk=user.pk)
        return user.get_available_balance()

    @sync_to_async
    def get_active_credential_count(self, user):
        """Return the number of active WebAuthn credentials for the user.

        Used by start_command to decide whether to show the Passkey setup
        button (first-time) or the Open Web App button (returning user).

        Requirements: 7.1, 8.1
        """
        self._close_old_db_connections()
        return WebAuthnCredential.objects.filter(user=user, is_active=True).count()

    @sync_to_async
    def get_user_deals(self, user):
        """Return the 10 most recent deals for this user."""
        self._close_old_db_connections()
        return list(
            Deal.objects.filter(
                models.Q(buyer=user) | models.Q(seller=user)
            )
            .select_related("buyer", "seller")
            .order_by("-created_at")[:10]
        )

    @sync_to_async
    def get_deal(self, deal_id):
        self._close_old_db_connections()
        return Deal.objects.select_related("buyer", "seller").get(id=deal_id)

    # ── /start ─────────────────────────────────────────────────────────────

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command.

        First-time users (no active Passkey) see a "Set Up Passkey" button
        that carries a Bridge Token deep link to /auth/passkey-setup.

        Returning users (at least one active Passkey) see an "Open Web App"
        button that carries a Bridge Token deep link to /auth/passkey-login,
        which initiates the Passkey authentication flow in the browser.

        Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3
        """
        try:
            user = await self.get_or_create_user(update.effective_user)
            available = await self.get_available_balance(user)
            active_credential_count = await self.get_active_credential_count(user)

            frontend_url = settings.FRONTEND_URL.rstrip("/")

            # Determine whether the URL scheme is valid for Telegram inline buttons
            # (Telegram rejects localhost / 127.0.0.1 URLs in InlineKeyboardButton)
            def _is_valid_telegram_url(url: str) -> bool:
                return url.startswith("https://") or (
                    url.startswith("http://")
                    and "localhost" not in url
                    and "127.0.0.1" not in url
                )

            keyboard = []

            if active_credential_count == 0:
                # ── First-time user: offer Passkey setup ──────────────────
                # Generate a Bridge Token for the register flow (Req 7.2)
                bridge_token = bridge_generate(user, "register")
                setup_url = f"{frontend_url}/auth/passkey-setup?bridge_token={bridge_token}"

                if _is_valid_telegram_url(setup_url):
                    keyboard.append([
                        InlineKeyboardButton("🔑 Set Up Passkey", url=setup_url)
                    ])
                else:
                    # Dev / localhost: show the URL as plain text in the message
                    pass  # handled below in the message body
            else:
                # ── Returning user: open web app via Passkey auth ─────────
                # Generate a Bridge Token for the authenticate flow (Req 8.3)
                bridge_token = bridge_generate(user, "authenticate")
                webapp_url = f"{frontend_url}/auth/passkey-login?bridge_token={bridge_token}"

                if _is_valid_telegram_url(webapp_url):
                    keyboard.append([
                        InlineKeyboardButton("🌐 Open Web App", url=webapp_url)
                    ])
                else:
                    pass  # handled below in the message body

            keyboard += [
                [InlineKeyboardButton("💰 My Wallet", callback_data="wallet")],
                [InlineKeyboardButton("📋 My Deals", callback_data="deals")],
                [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
            ]

            name = user.first_name or user.username or str(user.telegram_id)
            text = (
                f"🔐 *Welcome to Crypto Escrow!*\n\n"
                f"Hello {name}! 👋\n\n"
                f"*Balance:* `{user.balance} USDT`\n"
                f"*Available:* `{available} USDT`\n\n"
            )

            # For dev environments where Telegram rejects the URL, show it inline
            if active_credential_count == 0:
                if not _is_valid_telegram_url(setup_url):
                    text += f"🔑 Set Up Passkey: {setup_url}\n\n"
            else:
                if not _is_valid_telegram_url(webapp_url):
                    text += f"🌐 Web App: {webapp_url}\n\n"

            text += "What would you like to do?"

            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"start_command error: {e}\n{traceback.format_exc()}")
            await update.message.reply_text(
                "❌ Something went wrong. Please try again in a moment."
            )

    # ── Wallet ─────────────────────────────────────────────────────────────

    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /wallet command or wallet button."""
        query = update.callback_query
        if query:
            await query.answer()

        try:
            user = await self.get_or_create_user(update.effective_user)
            wallet = await self.get_user_wallet(user)
            available = await self.get_available_balance(user)

            keyboard = [
                [InlineKeyboardButton("💳 Deposit", callback_data="deposit")],
                [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("🔙 Back", callback_data="start")],
            ]

            text = (
                f"💰 *Your Wallet*\n\n"
                f"*Balance:* `{user.balance} USDT`\n"
                f"*Available:* `{available} USDT`\n\n"
                f"*Deposit Address (TRC20):*\n`{wallet.address}`"
            )

            if query:
                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.error(f"wallet_command error: {e}\n{traceback.format_exc()}")
            msg = "❌ Could not load wallet. Please try again."
            if query:
                await query.edit_message_text(msg)
            else:
                await update.message.reply_text(msg)

    async def deposit_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show deposit information."""
        query = update.callback_query
        await query.answer()

        try:
            user = await self.get_or_create_user(update.effective_user)
            wallet = await self.get_user_wallet(user)

            text = (
                f"💳 *Deposit USDT (TRC20)*\n\n"
                f"*Your Address:*\n`{wallet.address}`\n\n"
                f"*Instructions:*\n"
                f"1. Copy the address above\n"
                f"2. Send USDT on the TRC20 network\n"
                f"3. Balance updates automatically\n\n"
                f"⚠️ Only send USDT on TRC20 — other tokens will be lost."
            )

            keyboard = [[InlineKeyboardButton("🔙 Back to Wallet", callback_data="wallet")]]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"deposit_info error: {e}\n{traceback.format_exc()}")
            await query.edit_message_text("❌ Could not load deposit info. Please try again.")

    # ── Withdrawal conversation ────────────────────────────────────────────

    async def start_withdrawal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "💸 *Withdraw USDT*\n\nEnter the TRC20 destination address:",
            parse_mode="Markdown",
        )
        return AWAITING_WITHDRAWAL_ADDRESS

    async def receive_withdrawal_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        address = update.message.text.strip()
        if not address.startswith("T") or len(address) != 34:
            await update.message.reply_text(
                "❌ Invalid TRC20 address. Please try again or /cancel"
            )
            return AWAITING_WITHDRAWAL_ADDRESS

        context.user_data["withdrawal_address"] = address
        user = await self.get_or_create_user(update.effective_user)
        available = await self.get_available_balance(user)

        await update.message.reply_text(
            f"💸 *Withdraw to:* `{address}`\n\n"
            f"*Available:* `{available} USDT`\n\n"
            f"How much USDT do you want to withdraw?",
            parse_mode="Markdown",
        )
        return AWAITING_WITHDRAWAL_AMOUNT

    async def receive_withdrawal_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            amount = Decimal(update.message.text.strip())
        except Exception:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a number or /cancel"
            )
            return AWAITING_WITHDRAWAL_AMOUNT

        user = await self.get_or_create_user(update.effective_user)
        available = await self.get_available_balance(user)

        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0.")
            return AWAITING_WITHDRAWAL_AMOUNT
        if amount > available:
            await update.message.reply_text(
                f"❌ Insufficient balance. Available: {available} USDT"
            )
            return AWAITING_WITHDRAWAL_AMOUNT

        context.user_data["withdrawal_amount"] = str(amount)

        if user.is_2fa_enabled:
            await update.message.reply_text(
                "🔐 *2FA Required*\n\nEnter your 6-digit authenticator code:",
                parse_mode="Markdown",
            )
            return AWAITING_2FA_TOKEN

        return await self.process_withdrawal(update, context, user)

    async def receive_2fa_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        token = update.message.text.strip()
        user = await self.get_or_create_user(update.effective_user)

        from apps.users.two_factor import verify_totp_token

        valid = await sync_to_async(verify_totp_token)(user, token)
        if not valid:
            await update.message.reply_text(
                "❌ Invalid 2FA code. Please try again or /cancel"
            )
            return AWAITING_2FA_TOKEN

        return await self.process_withdrawal(update, context, user)

    async def process_withdrawal(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user):
        address = context.user_data.get("withdrawal_address")
        amount = context.user_data.get("withdrawal_amount")

        await update.message.reply_text("⏳ Processing your withdrawal…")

        try:
            from apps.wallets.tasks import process_withdrawal as withdrawal_task

            await sync_to_async(withdrawal_task.delay)(str(user.id), address, amount)
            await update.message.reply_text(
                f"✅ *Withdrawal Submitted!*\n\n"
                f"*Amount:* `{amount} USDT`\n"
                f"*To:* `{address}`\n\n"
                f"You'll be notified once it's confirmed.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"process_withdrawal error: {e}\n{traceback.format_exc()}")
            await update.message.reply_text(f"❌ Withdrawal failed: {e}")

        context.user_data.clear()
        return ConversationHandler.END

    # ── Deals ──────────────────────────────────────────────────────────────

    async def show_deals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query:
            await query.answer()

        try:
            user = await self.get_or_create_user(update.effective_user)
            deals = await self.get_user_deals(user)

            if not deals:
                text = "📋 *Your Deals*\n\nNo deals yet. Create one to get started!"
                keyboard = [
                    [InlineKeyboardButton("🔙 Back", callback_data="start")],
                ]
            else:
                text = "📋 *Your Deals*\n\nSelect a deal:"
                keyboard = []
                status_emoji = {
                    "DRAFT": "📝", "FUNDED": "💰", "IN_PROGRESS": "⚙️",
                    "COMPLETED": "✅", "DISPUTED": "⚠️", "CANCELLED": "❌",
                }
                for deal in deals:
                    role = "🛒" if deal.buyer_id == user.id else "💼"
                    emoji = status_emoji.get(deal.status, "📋")
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{emoji} {role} {deal.title[:28]}",
                            callback_data=f"deal_{deal.id}",
                        )
                    ])
                keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="start")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            if query:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"show_deals error: {e}\n{traceback.format_exc()}")
            msg = "❌ Could not load deals. Please try again."
            if query:
                await query.edit_message_text(msg)
            else:
                await update.message.reply_text(msg)

    async def show_deal_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        deal_id = query.data.split("_", 1)[1]
        user = await self.get_or_create_user(update.effective_user)

        try:
            deal = await self.get_deal(deal_id)
        except Deal.DoesNotExist:
            await query.edit_message_text("❌ Deal not found.")
            return

        if deal.buyer_id != user.id and deal.seller_id != user.id:
            await query.edit_message_text("❌ You are not a participant in this deal.")
            return

        role = "Buyer" if deal.buyer_id == user.id else "Seller"
        other = deal.seller if role == "Buyer" else deal.buyer
        status_label = {
            "DRAFT": "📝 Draft", "FUNDED": "💰 Funded",
            "IN_PROGRESS": "⚙️ In Progress", "COMPLETED": "✅ Completed",
            "DISPUTED": "⚠️ Disputed", "CANCELLED": "❌ Cancelled",
        }.get(deal.status, deal.status)

        text = (
            f"📋 *{deal.title}*\n\n"
            f"{deal.description}\n\n"
            f"*Amount:* `{deal.amount} USDT`\n"
            f"*Fee:* `{deal.fee} USDT`\n"
            f"*Status:* {status_label}\n"
            f"*Your role:* {role}\n"
            f"*Other party:* @{other.username or other.telegram_id}\n"
            f"*Created:* {deal.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

        keyboard = []
        if deal.status == "DRAFT" and role == "Seller":
            keyboard.append([InlineKeyboardButton("💰 Fund Deal", callback_data=f"fund_{deal.id}")])
        elif deal.status == "FUNDED" and role == "Buyer":
            keyboard.append([InlineKeyboardButton("▶️ Start Deal", callback_data=f"startdeal_{deal.id}")])
        elif deal.status == "IN_PROGRESS":
            if role == "Buyer":
                keyboard.append([InlineKeyboardButton("✅ Complete", callback_data=f"complete_{deal.id}")])
            keyboard.append([InlineKeyboardButton("⚠️ Dispute", callback_data=f"dispute_{deal.id}")])
        if deal.status in ("DRAFT", "FUNDED"):
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data=f"canceldeal_{deal.id}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Deals", callback_data="deals")])

        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    async def fund_deal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        deal_id = query.data.split("_", 1)[1]
        user = await self.get_or_create_user(update.effective_user)
        try:
            @sync_to_async
            def _fund():
                self._close_old_db_connections()
                deal = Deal.objects.get(id=deal_id)
                DealService.fund_deal(deal, user)
                return deal
            deal = await _fund()
            await query.edit_message_text(
                f"✅ *Deal Funded!*\n\n`{deal.amount} USDT` locked in escrow.\nWaiting for buyer to start.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"fund_deal error: {e}\n{traceback.format_exc()}")
            await query.edit_message_text(f"❌ Error: {e}")

    async def start_deal_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        deal_id = query.data.split("_", 1)[1]
        user = await self.get_or_create_user(update.effective_user)
        try:
            @sync_to_async
            def _start():
                self._close_old_db_connections()
                deal = Deal.objects.get(id=deal_id)
                DealService.start_deal(deal, user)
                return deal
            await _start()
            await query.edit_message_text(
                "▶️ *Deal Started!*\n\nSeller can now begin work.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"start_deal_action error: {e}\n{traceback.format_exc()}")
            await query.edit_message_text(f"❌ Error: {e}")

    async def complete_deal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        deal_id = query.data.split("_", 1)[1]
        user = await self.get_or_create_user(update.effective_user)
        try:
            @sync_to_async
            def _complete():
                self._close_old_db_connections()
                deal = Deal.objects.get(id=deal_id)
                DealService.complete_deal(deal, user)
                return deal
            deal = await _complete()
            await query.edit_message_text(
                f"✅ *Deal Completed!*\n\nFunds released. Fee: `{deal.fee} USDT`",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"complete_deal error: {e}\n{traceback.format_exc()}")
            await query.edit_message_text(f"❌ Error: {e}")

    async def cancel_deal_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        deal_id = query.data.split("_", 1)[1]
        user = await self.get_or_create_user(update.effective_user)
        try:
            @sync_to_async
            def _cancel():
                self._close_old_db_connections()
                deal = Deal.objects.get(id=deal_id)
                DealService.cancel_deal(deal, user)
            await _cancel()
            await query.edit_message_text(
                "❌ *Deal Cancelled*\n\nAny locked funds have been refunded.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"cancel_deal_action error: {e}\n{traceback.format_exc()}")
            await query.edit_message_text(f"❌ Error: {e}")

    # ── Help / Cancel ──────────────────────────────────────────────────────

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query:
            await query.answer()

        text = (
            "📖 *Help*\n\n"
            "*Commands:*\n"
            "/start — Main menu\n"
            "/wallet — Your wallet\n"
            "/deals — Your deals\n"
            "/cancel — Cancel current action\n\n"
            "*How it works:*\n"
            "1️⃣ Deposit USDT to your wallet address\n"
            "2️⃣ Create or join a deal\n"
            "3️⃣ Seller funds escrow → Buyer starts → Buyer completes\n"
            "4️⃣ Funds released automatically on completion"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]

        if query:
            await query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Cancelled. Use /start to return to the main menu."
        )
        return ConversationHandler.END

    # ── Button router ──────────────────────────────────────────────────────

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data

        try:
            if data == "start":
                await self.start_command(update, context)
            elif data == "wallet":
                await self.wallet_command(update, context)
            elif data == "deposit":
                await self.deposit_info(update, context)
            elif data == "help":
                await self.help_command(update, context)
            elif data == "deals":
                await self.show_deals(update, context)
            elif data.startswith("deal_"):
                await self.show_deal_detail(update, context)
            elif data.startswith("fund_"):
                await self.fund_deal(update, context)
            elif data.startswith("startdeal_"):
                await self.start_deal_action(update, context)
            elif data.startswith("complete_"):
                await self.complete_deal(update, context)
            elif data.startswith("canceldeal_"):
                await self.cancel_deal_action(update, context)
            else:
                await query.answer("Unknown action.", show_alert=True)
        except Exception as e:
            logger.error(f"button_handler error [{data}]: {e}\n{traceback.format_exc()}")
            await query.answer("❌ An error occurred. Please try again.", show_alert=True)

    # ── Error handler ──────────────────────────────────────────────────────

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(
            f"Unhandled exception: {context.error}\n{traceback.format_exc()}"
        )
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again or use /help."
            )

    # ── Setup & run ────────────────────────────────────────────────────────

    def setup_handlers(self):
        withdrawal_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_withdrawal, pattern="^withdraw$")],
            states={
                AWAITING_WITHDRAWAL_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_withdrawal_address)
                ],
                AWAITING_WITHDRAWAL_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_withdrawal_amount)
                ],
                AWAITING_2FA_TOKEN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_2fa_token)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )

        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("wallet", self.wallet_command))
        self.application.add_handler(CommandHandler("deals", self.show_deals))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel_command))
        self.application.add_handler(withdrawal_conv)
        # General button handler — must be last
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_error_handler(self.error_handler)

    def run(self):
        self.application = (
            Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        )
        self.setup_handlers()
        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


# Bot instance (imported by management command)
bot = EscrowBot()
