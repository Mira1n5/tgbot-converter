import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
BOT_TOKEN=os.getenv("BOT_TOKEN")
CURRENCY_API_KEY=os.getenv("CURRENCY_API_KEY")
bot=Bot(token=BOT_TOKEN)  
dp=Dispatcher()

CURRENCIES=["USD", "EUR", "RUB", "KZT", "TRY", "JPY"]
def currency_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cur, callback_data=cur) for cur in CURRENCIES[i:i + 3]]
            for i in range(0, len(CURRENCIES), 3)
        ]
    )
class CurrencyStates(StatesGroup):
    from_currency=State()
    amount=State()
    to_currency=State()
async def convert_currency(from_currency: str, to_currency: str, amount: float) -> float:
    url=f"https://v6.exchangerate-api.com/v6/{CURRENCY_API_KEY}/pair/{from_currency}/{to_currency}/{amount}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data=await response.json()
            return data.get("conversion_result")
        
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("💱 Привет! Выберите валюту, из которой будем конвертировать:", reply_markup=currency_keyboard())
    await state.set_state(CurrencyStates.from_currency)

@dp.callback_query(CurrencyStates.from_currency)
async def choose_from_currency(callback: CallbackQuery, state: FSMContext):
    await state.update_data(from_currency=callback.data)
    await callback.message.edit_text(f"🔢 Введите сумму в {callback.data}:")
    await state.set_state(CurrencyStates.amount)

@dp.message(CurrencyStates.amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount=float(message.text.replace(',', '.'))
        await state.update_data(amount=amount)
        await message.answer("📥 Теперь выберите валюту, в которую перевести:", reply_markup=currency_keyboard())
        await state.set_state(CurrencyStates.to_currency)
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректное число.")

@dp.callback_query(CurrencyStates.to_currency)
async def choose_to_currency(callback: CallbackQuery, state: FSMContext):
    data=await state.get_data()
    from_currency=data["from_currency"]
    amount=data["amount"]
    to_currency=callback.data

    try:
        result=await convert_currency(from_currency, to_currency, amount)
        if result is not None:
            text=f"✅ <b>{amount:.2f} {from_currency} = {result:.2f} {to_currency}</b>"
        else:
            text="❌ Не удалось получить курс валют."
    except Exception as e:
        text=f"⚠️ Ошибка при конвертации: {e}"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.clear()

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))