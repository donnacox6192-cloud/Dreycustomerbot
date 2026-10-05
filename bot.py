import logging
import os
import re
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from pint import UnitRegistry, UndefinedUnitError

# ---------- SETUP ----------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ureg = UnitRegistry()

# ---------- BUSINESS INFO (edit these) ----------
BUSINESS_NAME = "Drey Customer Service"

OPENING_HOURS = {
    "Monday - Friday": "08:00 - 18:00",
    "Saturday": "09:00 - 15:00",
    "Sunday": "Closed",
}

PRODUCTS = (
    "🛍️ *Our Products & Services*\n\n"
    "*Products:*\n"
    "• Custom-designed T-shirts\n"
    "• Phone accessories\n"
    "• Home appliances\n\n"
    "*Services:*\n"
    "• Measurement consulting\n"
    "• Bulk order conversions for international clients\n"
    "• Delivery within 48 hrs (local)\n\n"
    "Use /price to see current prices."
)

PRICES = (
    "💰 *Price List*\n\n"
    "• T-shirt (custom): ₦8,000 / $12\n"
    "• Phone case: ₦3,500 / $5\n"
    "• Blender: ₦25,000 / $35\n"
    "• Measurement consulting (per hr): ₦5,000 / $7\n"
    "• Delivery: ₦1,500 flat (local)\n\n"
    "Prices include VAT. Bulk discounts available."
)

PAYMENT_INFO = (
    "💳 *Payment Methods Accepted:*\n\n"
    "• Bank Transfer: *Drey Enterprises* — Acct: 1234567890\n"
    "• Mobile Money: *+234 XXX XXX XXXX*\n"
    "• Crypto (USDT TRC20): `TXXXXXXXXXXXXXXXXXXXX`\n"
    "• Cash on delivery (local only)\n\n"
    "⚠️ Always request an official receipt after payment."
)

# ---------- KEYBOARD ----------
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🛍️ Products & Services", "💰 Price List"],
        ["🕒 Opening Hours", "💳 Payment Info"],
        ["📏 Unit Converter", "☎️ Contact"],
    ],
    resize_keyboard=True,
    input_field_placeholder="Choose an option or type a conversion…",
)

# ---------- UNIT CONVERSION ----------
ALIASES = {
    "inches": "inch", "in": "inch",
    "feet": "foot", "ft": "foot",
    "pounds": "pound", "lbs": "pound", "lb": "pound",
    "kgs": "kilogram", "kg": "kilogram",
    "cms": "centimeter", "cm": "centimeter",
    "mm": "millimeter", "m": "meter", "meters": "meter",
    "km": "kilometer", "miles": "mile",
    "f": "fahrenheit", "c": "celsius",
    "l": "liter", "ml": "milliliter",
    "g": "gram",
}

CONVERSION_RE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z°]+)\s*(?:to|in|->|=>)\s*([a-zA-Z°]+)\s*$"
)


def normalize_unit(u: str) -> str:
    return ALIASES.get(u.strip().lower(), u.strip().lower())


def parse_conversion(text: str):
    m = CONVERSION_RE.match(text)
    if not m:
        return None
    return float(m.group(1)), m.group(2), m.group(3)


def convert_units(value: float, from_u: str, to_u: str) -> str:
    from_u = normalize_unit(from_u)
    to_u = normalize_unit(to_u)
    try:
        qty = value * ureg(from_u)
        result = qty.to(to_u)
        return f"✅ {value} {from_u} = *{result.magnitude:.4g} {to_u}*"
    except UndefinedUnitError as e:
        raise ValueError(f"Unknown unit: {e}")
    except Exception as e:
        raise ValueError(f"Cannot convert: {e}")


# ---------- COMMAND HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (
        f"👋 Hello *{user.first_name}*!\n\n"
        f"Welcome to *{BUSINESS_NAME}* bot.\n"
        f"I can help you with:\n"
        f"• 🛍️ Products & services\n"
        f"• 💰 Prices\n"
        f"• 🕒 Opening hours\n"
        f"• 💳 Payment info\n"
        f"• 📏 Unit conversions (e.g. `10 kg to lbs`)\n\n"
        f"Pick an option below or type a conversion."
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MAIN_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "*Available commands:*\n"
        "/start — Main menu\n"
        "/products — Products & services\n"
        "/price — Price list\n"
        "/hours — Opening hours\n"
        "/payment — Payment info\n"
        "/convert `<value> <from> to <to>` — e.g. `/convert 10 kg to lbs`\n"
        "/help — This message\n\n"
        "You can also just type `5ft in cm`."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def products_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(PRODUCTS, parse_mode="Markdown")


async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(PRICES, parse_mode="Markdown")


async def hours_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ["🕒 *Opening Hours*\n"]
    for day, time in OPENING_HOURS.items():
        lines.append(f"• {day}: *{time}*")
    lines.append("\n📍 All times are local (WAT).")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def payment_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(PAYMENT_INFO, parse_mode="Markdown")


CONVERTER_HELP = (
    "📏 *Unit Converter*\n\n"
    "Send any of these formats:\n"
    "• `10 kg to lbs`\n"
    "• `5ft in cm`\n"
    "• `100 f to c`\n"
    "• `2.5 miles -> km`\n\n"
    "Or use: `/convert 10 kg to lbs`\n\n"
    "Supports length, weight, temperature, volume, and more."
)


async def convert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(CONVERTER_HELP, parse_mode="Markdown")
        return
    parsed = parse_conversion(" ".join(context.args))
    if not parsed:
        await update.message.reply_text(
            "❌ Couldn't parse. Try: `/convert 10 kg to lbs`",
            parse_mode="Markdown",
        )
        return
    value, from_u, to_u = parsed
    try:
        await update.message.reply_text(
            convert_units(value, from_u, to_u), parse_mode="Markdown"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")


async def contact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "☎️ *Contact Us*\n\n"
        "📞 Phone: +234 XXX XXX XXXX\n"
        "📧 Email: support@drey.example\n"
        "🌐 Website: https://drey.example",
        parse_mode="Markdown",
    )


# ---------- TEXT ROUTER ----------
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text

    if text == "🛍️ Products & Services":
        await products_cmd(update, context)
    elif text == "💰 Price List":
        await price_cmd(update, context)
    elif text == "🕒 Opening Hours":
        await hours_cmd(update, context)
    elif text == "💳 Payment Info":
        await payment_cmd(update, context)
    elif text == "📏 Unit Converter":
        await update.message.reply_text(CONVERTER_HELP, parse_mode="Markdown")
    elif text == "☎️ Contact":
        await contact_cmd(update, context)
    else:
        # Try to auto-convert
        parsed = parse_conversion(text)
        if parsed:
            value, from_u, to_u = parsed
            try:
                await update.message.reply_text(
                    convert_units(value, from_u, to_u), parse_mode="Markdown"
                )
                return
            except ValueError as e:
                await update.message.reply_text(f"❌ {e}")
                return
        await update.message.reply_text(
            "🤔 I didn't understand that.\n"
            "Use the menu below or try a conversion like `10 kg to lbs`.",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )


# ---------- ERROR HANDLER ----------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Something went wrong. Please try again."
            )
        except Exception:
            pass


# ---------- MAIN ----------
def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("products", products_cmd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("hours", hours_cmd))
    app.add_handler(CommandHandler("payment", payment_cmd))
    app.add_handler(CommandHandler("convert", convert_cmd))
    app.add_handler(CommandHandler("contact", contact_cmd))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_error_handler(error_handler)

    logger.info("🤖 DreyCustomerBot is starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
