"""
Django management command to run the Telegram bot
"""
from django.core.management.base import BaseCommand
from apps.telegram_bot.bot import bot


class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Telegram bot...'))
        try:
            bot.run()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nBot stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Bot error: {e}'))
