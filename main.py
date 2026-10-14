import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import random

TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = 8514764458

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

users_db = {}
orders_db = {}

bot_settings = {
    "support_username": "YourUsername",
    "log_channel": "@YourChannelOrChatID",
    "force_channel": "@RXPremiumZone",
    "banner_image": "https://i.ibb.co.com/example/banner.jpg",
    "services": {
        "tiktok": [
            {"id": 1, "name": "1K Views", "price": 2},
            {"id": 2, "name": "1K Likes", "price": 6}
        ],
        "telegram": [
            {"id": 1, "name": "1K Views", "price": 1},
            {"id": 2, "name": "1K Members", "price": 20}
        ],
        "youtube": [
            {"id": 1, "name": "1K Views", "price": 10},
            {"id": 2, "name": "1K Likes", "price": 15}
        ],
        "facebook": [
            {"id": 1, "name": "1K Followers", "price": 55},
            {"id": 2, "name": "1K Video Views", "price": 5}
        ],
        "instagram": [
            {"id": 1, "name": "1K Likes", "price": 15},
            {"id": 2, "name": "1K Followers", "price": 20}
        ]
    }
}


class DepositState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_proof = State()


class OrderProcessState(StatesGroup):
    waiting_for_link = State()
    waiting_for_quantity = State()


class AdminActionState(StatesGroup):
    waiting_for_ban_id = State()
    waiting_for_channel = State()
    waiting_for_force_channel = State()
    waiting_for_support = State()
    waiting_for_image_url = State()


def get_main_menu(user_id):
    keyboard = [
        [
            InlineKeyboardButton(
                text="🛍️ 𝐍𝐄𝐖 𝐎𝐑𝐃𝐄𝐑",
                callback_data="new_order"
            ),
            InlineKeyboardButton(
                text="💰 𝐏𝐑𝐈𝐂𝐄 & 𝐈𝐍𝐅𝐎",
                callback_data="price_info"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 𝐃𝐄𝐏𝐎𝐒𝐈𝐓",
                callback_data="deposit"
            ),
            InlineKeyboardButton(
                text="👤 𝐌𝐘 𝐀𝐂𝐂𝐎𝐔𝐍𝐓",
                callback_data="my_account"
            )
        ],
        [
            InlineKeyboardButton(
                text="🫂 𝐑𝐄𝐅𝐄𝐑 & 𝐄𝐀𝐑𝐍",
                callback_data="refer_earn"
            ),
            InlineKeyboardButton(
                text="🎧 𝐒𝐔𝐏𝐏𝐎𝐑𝐓",
                callback_data="support"
            )
        ]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton(
                text="⚙️ 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋",
                callback_data="admin_panel"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_button(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔙 Return / Back",
                callback_data="main_menu"
            )
        ]
    ])


async def check_subscription(user_id: int) -> bool:
    channel = bot_settings.get("force_channel")

    if not channel:
        return True

    try:
        member = await bot.get_chat_member(
            chat_id=channel,
            user_id=user_id
        )

        if member.status in ["member", "administrator", "creator"]:
            return True

    except Exception:
        logging.exception("চ্যানেল সদস্যপদ যাচাই করা যায়নি")

    return False


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id

    if user_id in users_db and users_db[user_id].get("is_banned", False):
        await message.answer(
            "❌ দুঃখিত, আপনি এই বট থেকে ব্যানড হয়েছেন!"
        )
        return

    is_joined = await check_subscription(user_id)

    if not is_joined:
        channel = bot_settings.get("force_channel")

        force_markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 চ্যানেলে জয়েন করুন",
                    url=f"https://t.me/{channel.lstrip('@')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Joined",
                    callback_data="check_join"
                )
            ]
        ])

        await message.answer(
            f"⛔ বট ব্যবহারের আগে আমাদের চ্যানেলে জয়েন করুন\n\n"
            f"📢 আমাদের চ্যানেল:\n➡️ <b>{channel}</b>\n\n"
            f"✅ সব চ্যানেলে জয়েন করার পর নিচের Joined বাটনে ক্লিক করুন।",
            reply_markup=force_markup,
            parse_mode="HTML"
        )
        return

    if user_id not in users_db:
        users_db[user_id] = {
            "name": message.from_user.full_name,
            "balance": 0.0,
            "orders": 0,
            "completed": 0,
            "pending": 0,
            "canceled": 0,
            "referrals": 0,
            "is_banned": False
        }

    welcome_text = (
        f"স্বাগতম <b>{message.from_user.full_name}</b>!\n\n"
        "আমাদের 𝗥𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 বটে আপনাকে স্বাগতম। "
        "নিচে থেকে আপনার পছন্দের অপশনটি বেছে নিন:"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(user_id),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_joined = await check_subscription(user_id)

    if not is_joined:
        await callback.answer(
            "❌ আপনি এখনো চ্যানেলে জয়েন করেননি!",
            show_alert=True
        )
        return

    if user_id not in users_db:
        users_db[user_id] = {
            "name": callback.from_user.full_name,
            "balance": 0.0,
            "orders": 0,
            "completed": 0,
            "pending": 0,
            "canceled": 0,
            "referrals": 0,
            "is_banned": False
        }

    await callback.message.delete()

    welcome_text = (
        f"স্বাগতম <b>{callback.from_user.full_name}</b>!\n\n"
        "আমাদের 𝗥𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 বটে আপনাকে স্বাগতম। "
        "নিচে থেকে আপনার পছন্দের অপশনটি বেছে নিন:"
    )

    await callback.message.answer(
        welcome_text,
        reply_markup=get_main_menu(user_id),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery):
    user_id = callback.from_user.id

    is_joined = await check_subscription(user_id)

    if not is_joined:
        await callback.answer(
            "⚠️ প্রথমে চ্যানেলে জয়েন করুন!",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "মূল মেনুতে ফিরে এসেছেন:",
        reply_markup=get_main_menu(user_id)
    )
    await callback.answer()


@dp.callback_query(F.data == "new_order")
async def new_order_menu(callback: CallbackQuery):
    order_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎵 TikTok Services",
                callback_data="cat_tiktok"
            ),
            InlineKeyboardButton(
                text="📢 Telegram Services",
                callback_data="cat_telegram"
            )
        ],
        [
            InlineKeyboardButton(
                text="▶️ YouTube Services",
                callback_data="cat_youtube"
            ),
            InlineKeyboardButton(
                text="👥 Facebook Services",
                callback_data="cat_facebook"
            )
        ],
        [
            InlineKeyboardButton(
                text="📸 Instagram Services",
                callback_data="cat_instagram"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Return",
                callback_data="main_menu"
            )
        ]
    ])

    await callback.message.edit_text(
        "🛍️ <b>NEW ORDER MENU</b>\n\n"
        "দয়া করে আপনার পছন্দের ক্যাটাগরি সিলেক্ট করুন:",
        reply_markup=order_markup,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cat_"))
async def show_category_services(callback: CallbackQuery):
    cat_key = callback.data.split("_")[1]
    services = bot_settings["services"].get(cat_key, [])

    if not services:
        await callback.answer(
            "এই ক্যাটাগরিতে বর্তমানে কোনো সার্ভিস নেই।",
            show_alert=True
        )
        return

    buttons = []

    for service in services:
        buttons.append([
            InlineKeyboardButton(
                text=f"🔹 {service['name']} — ৳{service['price']} (প্রতি ১ হাজার)",
                callback_data=f"select_srv_{cat_key}_{service['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 Return",
            callback_data="new_order"
        )
    ])

    await callback.message.edit_text(
        f"📦 <b>{cat_key.upper()} SERVICES</b>\n\n"
        "নিচের সার্ভিসগুলো থেকে সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )
    await callback.answer()async def approve_order(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ শুধু অ্যাডমিন এই কাজ করতে পারবেন।", show_alert=True)
        return

    order_id = int(callback.data.split("_")[2])

    if order_id in orders_db:
        o = orders_db[order_id]
        user_id = o["user_id"]

        users_db[user_id]["pending"] = max(
            0, users_db[user_id]["pending"] - 1
        )
        users_db[user_id]["completed"] += 1

        await bot.send_message(
            user_id,
            f"🎉 অভিনন্দন! আপনার অর্ডার আইডি "
            f"<code>{order_id}</code> সম্পন্ন হয়েছে। ✅",
            parse_mode="HTML"
        )

        await callback.message.edit_text(
            f"✅ অর্ডার #{order_id} সফলভাবে অ্যাপ্রুভ করা হয়েছে।"
        )

    await callback.answer()


@dp.callback_query(F.data.startswith("ord_rej_"))
async def cancel_order(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ শুধু অ্যাডমিন এই কাজ করতে পারবেন।", show_alert=True)
        return

    order_id = int(callback.data.split("_")[2])

    if order_id in orders_db:
        o = orders_db[order_id]
        user_id = o["user_id"]
        refund_amount = o["cost"]

        users_db[user_id]["balance"] += refund_amount
        users_db[user_id]["pending"] = max(
            0, users_db[user_id]["pending"] - 1
        )
        users_db[user_id]["canceled"] += 1

        await bot.send_message(
            user_id,
            f"❌ আপনার অর্ডার আইডি <code>{order_id}</code> "
            f"বাতিল করা হয়েছে। ৳{refund_amount:.2f} রিফান্ড করা হয়েছে।",
            parse_mode="HTML"
        )

        await callback.message.edit_text(
            f"❌ অর্ডার #{order_id} বাতিল করা হয়েছে এবং টাকা ফেরত দেওয়া হয়েছে।"
        )

    await callback.answer()


@dp.callback_query(F.data == "my_account")
async def my_account(callback: CallbackQuery):
    user_id = callback.from_user.id

    u = users_db.get(user_id, {
        "name": callback.from_user.full_name,
        "balance": 0.0,
        "orders": 0,
        "completed": 0,
        "pending": 0,
        "canceled": 0
    })

    text = (
        f"👤 𝐌𝐘 𝐀𝐂𝐂𝐎𝐔𝐍𝐓\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 𝐔𝐬𝐞𝐫 𝐈𝐃 : <code>{user_id}</code>\n"
        f"👤 𝐍𝐚𝐦𝐞 : {u['name']}\n"
        f"💰 𝐁𝐚𝐥𝐚𝐧𝐜𝐞 : ৳{u['balance']:.2f}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 𝐓𝐨𝐭𝐚𝐥 𝐎𝐫𝐝𝐞𝐫𝐬 : {u['orders']}\n"
        f"✅ 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝 : {u['completed']}\n"
        f"⏳ 𝐏𝐞𝐧𝐝𝐢𝐧𝐠 : {u['pending']}\n"
        f"❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐞𝐝 : {u['canceled']}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_back_button(user_id),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "price_info")
async def price_info(callback: CallbackQuery):
    user_id = callback.from_user.id

    text = (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📲 𝗥𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 – 𝗦𝗘𝗥𝗩𝗜𝗖𝗘 𝗟𝗜𝗦𝗧\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for category, services in bot_settings["services"].items():
        text += f"🔵 <b>{category.upper()}</b>\n"

        for service in services:
            text += f"▪️ {service['name']} — ৳{service['price']}\n"

        text += "━━━━━━━━━━━━━━━━━━━━━━\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_back_button(user_id),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "deposit")
async def deposit_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💳 𝗗𝗘𝗣𝗢𝗦𝗜𝗧 𝗠𝗘𝗡𝗨\n\n"
        "আপনি কত টাকা ডিপোজিট করতে চান, পরিমাণ লিখুন।\n"
        "⚠️ সর্বনিম্ন ডিপোজিট: ১০ টাকা।",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Cancel",
                        callback_data="main_menu"
                    )
                ]
            ]
        )
    )

    await state.set_state(DepositState.waiting_for_amount)
    await callback.answer()


@dp.message(DepositState.waiting_for_amount)
async def deposit_amount_received(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("❌ সঠিক টাকার পরিমাণ সংখ্যায় লিখুন।")
        return

    amount = int(message.text)

    if amount < 10:
        await message.answer("❌ সর্বনিম্ন ১০ টাকা ডিপোজিট করতে পারবেন।")
        return

    await state.update_data(amount=amount)
    await message.answer(
        "📥 টাকা পাঠানোর পর ট্রানজেকশন আইডি অথবা পেমেন্টের স্ক্রিনশট পাঠান।"
    )

    await state.set_state(DepositState.waiting_for_proof)


@dp.message(DepositState.waiting_for_proof)
async def deposit_proof_received(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    user = message.from_user

    if not amount:
        await message.answer("❌ ডিপোজিটের তথ্য পাওয়া যায়নি। আবার চেষ্টা করুন।")
        await state.clear()
        return

    admin_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Approve",
                    callback_data=f"dep_acc_{user.id}_{amount}"
                ),
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=f"dep_rej_{user.id}"
                )
            ]
        ]
    )

    proof_text = (
        f"🔔 <b>ডিপোজিট রিকোয়েস্ট</b>\n\n"
        f"👤 ইউজার: {user.full_name}\n"
        f"🆔 আইডি: <code>{user.id}</code>\n"
        f"💰 পরিমাণ: ৳{amount}\n"
        f"📄 প্রমাণ: নিচের মেসেজে দেওয়া হয়েছে।"
    )

    await bot.send_message(
        ADMIN_ID,
        proof_text,
        reply_markup=admin_markup,
        parse_mode="HTML"
    )

    if message.photo:
        await bot.send_photo(
            ADMIN_ID,
            photo=message.photo[-1].file_id,
            caption=f"ডিপোজিট প্রমাণ — ইউজার আইডি: {user.id}"
        )
    elif message.text:
        await bot.send_message(
            ADMIN_ID,
            f"ট্রানজেকশন তথ্য:\n{message.text}"
        )
    else:
        await bot.send_message(
            ADMIN_ID,
            "ইউজার ডিপোজিট প্রমাণ হিসেবে একটি ফাইল পাঠিয়েছেন।"
        )

    await message.answer(
        "✅ আপনার ডিপোজিট রিকোয়েস্ট জমা হয়েছে। অ্যাডমিন যাচাই করবেন।",
        reply_markup=get_main_menu(user.id)
    )

    await state.clear()


@dp.callback_query(F.data.startswith("dep_acc_"))
async def approve_deposit(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ শুধু অ্যাডমিন অনুমোদন দিতে পারবেন।", show_alert=True)
        return

    parts = callback.data.split("_")
    user_id = int(parts[2])
    amount = float(parts[3])

    if user_id not in users_db:
        await callback.answer("❌ ইউজার পাওয়া যায়নি।", show_alert=True)
        return

    users_db[user_id]["balance"] += amount

    await bot.send_message(
        user_id,
        f"🎉 আপনার ৳{amount:.2f} ডিপোজিট অ্যাপ্রুভ হয়েছে!"
    )

    await callback.message.edit_text(
        f"✅ ইউজার {user_id}-এর ৳{amount:.2f} ডিপোজিট অ্যাপ্রুভ করা হয়েছে।"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("dep_rej_"))
async def reject_deposit(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ শুধু অ্যাডমিন এই কাজ করতে পারবেন।", show_alert=True)
        return

    parts = callback.data.split("_")
    user_id = int(parts[2])

    await bot.send_message(
        user_id,
        "❌ আপনার ডিপোজিট রিকোয়েস্টটি বাতিল করা হয়েছে।"
    )

    await callback.message.edit_text(
        f"❌ ইউজার {user_id}-এর ডিপোজিট রিকোয়েস্ট রিজেক্ট করা হয়েছে।"
    )

    await callback.answer()


@dp.callback_query(F.data == "support")
async def support_menu(callback: CallbackQuery):
    current_support = bot_settings.get("support_username", "YourUsername")

    support_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Contact Admin",
                    url=f"https://t.me/{current_support.lstrip('@')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Return",
                    callback_data="main_menu"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🎧 যেকোনো সমস্যায় যোগাযোগ করুন:",
        reply_markup=support_markup
    )

    await callback.answer()


@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ এটি শুধু অ্যাডমিনের জন্য।", show_alert=True)
        return

    text = (
        "⚙️ <b>ADMIN CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 <b>Force Channel:</b> <code>{bot_settings['force_channel']}</code>\n"
        f"📢 <b>Log Channel:</b> <code>{bot_settings['log_channel']}</code>\n"
        f"🎧 <b>Support User:</b> <code>@{bot_settings['support_username']}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "নিচের অপশনগুলো থেকে বটের সেটিংস পরিবর্তন করুন:"
    )

    admin_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Change Force Channel",
                    callback_data="change_force_channel"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Change Log Channel",
                    callback_data="change_channel"
                ),
                InlineKeyboardButton(
                    text="✏️ Change Support",
                    callback_data="change_support"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Ban User",
                    callback_data="ban_user"
                ),
                InlineKeyboardButton(
                    text="✅ Unban User",
                    callback_data="unban_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Main Menu",
                    callback_data="main_menu"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_markup,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "change_force_channel")
async def change_force_channel_prompt(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ অনুমতি নেই।", show_alert=True)
        return

    await callback.message.edit_text(
        "📢 নতুন ফোর্স সাবস্ক্রিপশন চ্যানেলের ইউজারনেম লিখুন।\n"
        "উদাহরণ: @RXPremiumZone"
    )

    await state.set_state(AdminActionState.waiting_for_force_channel)
    await callback.answer()


@dp.message(AdminActionState.waiting_for_force_channel)
async def save_new_force_channel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.text:
        await message.answer("❌ চ্যানেলের ইউজারনেম লিখুন।")
        return

    bot_settings["force_channel"] = message.text.strip()

    await message.answer(
        f"✅ ফোর্স চ্যানেল আপডেট হয়েছে: {bot_settings['force_channel']}"
    )

    await state.clear()


@dp.callback_query(F.data == "change_channel")
async def change_channel_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ অনুমতি নেই।", show_alert=True)
        return

    await callback.message.edit_text(
        "📢 নতুন লগ চ্যানেলের ইউজারনেম বা আইডি লিখুন।\n"
        "উদাহরণ: @MyOrderChannel"
    )

    await state.set_state(AdminActionState.waiting_for_channel)
    await callback.answer()


@dp.message(AdminActionState.waiting_for_channel)
async def save_new_channel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.text:
        await message.answer("❌ চ্যানেলের ইউজারনেম বা আইডি লিখুন।")
        return

    bot_settings["log_channel"] = message.text.strip()

    await message.answer(
        f"✅ লগ চ্যানেল আপডেট হয়েছে: {bot_settings['log_channel']}"
    )

    await state.clear()


@dp.callback_query(F.data == "change_support")
async def change_support_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ অনুমতি নেই।", show_alert=True)
        return

    await callback.message.edit_text(
        "🎧 নতুন সাপোর্ট ইউজারনেম লিখুন।\n"
        "উদাহরণ: @YourUsername"
    )

    await state.set_state(AdminActionState.waiting_for_support)
    await callback.answer()


@dp.message(AdminActionState.waiting_for_support)
async def save_new_support(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.text:
        await message.answer("❌ সাপোর্ট ইউজারনেম লিখুন।")
        return

    username = message.text.strip().lstrip("@")
    bot_settings["support_username"] = username

    await message.answer(
        f"✅ সাপোর্ট ইউজারনেম আপডেট হয়েছে: @{username}"
    )

    await state.clear()


@dp.callback_query(F.data == "ban_user")
async def ban_user_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ অনুমতি নেই।", show_alert=True)
        return

    await callback.message.edit_text(
        "🚫 যে ইউজারকে ব্যান করতে চান তার Telegram ID লিখুন।"
    )

    await state.set_state(AdminActionState.waiting_for_ban_id)
    await state.update_data(action="ban")
    await callback.answer()


@dp.callback_query(F.data == "unban_user")
async def unban_user_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ অনুমতি নেই।", show_alert=True)
        return

    await callback.message.edit_text(
        "✅ যে ইউজারকে আনব্যান করতে চান তার Telegram ID লিখুন।"
    )

    await state.set_state(AdminActionState.waiting_for_ban_id)
    await state.update_data(action="unban")
    await callback.answer()


@dp.message(AdminActionState.waiting_for_ban_id)
async def process_ban_unban(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.text:
        await message.answer("❌ Telegram ID সংখ্যায় লিখুন।")
        return

    try:
        target_id = int(message.text.strip())
        data = await state.get_data()
        action = data.get("action")

        if target_id not in users_db:
            await message.answer("❌ এই ইউজার বটের ডাটাবেসে নেই।")

        elif action == "ban":
            users_db[target_id]["is_banned"] = True
            await message.answer(
                f"✅ ইউজার {target_id} ব্যান করা হয়েছে।"
            )

        else:
            users_db[target_id]["is_banned"] = False
            await message.answer(
                f"✅ ইউজার {target_id} আনব্যান করা হয়েছে।"
            )

    except ValueError:
        await message.answer("❌ সঠিক Telegram ID সংখ্যায় লিখুন।")

    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
