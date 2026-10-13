import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
import random

TOKEN = "8776364249:AAFoalVITYxaAvQjs6ojem2Lf-7iBd0n8C4"
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
        "tiktok": [{"id": 1, "name": "1K Views", "price": 2}, {"id": 2, "name": "1K Likes", "price": 6}],
        "telegram": [{"id": 1, "name": "1K Views", "price": 1}, {"id": 2, "name": "1K Members", "price": 20}],
        "youtube": [{"id": 1, "name": "1K Views", "price": 10}, {"id": 2, "name": "1K Likes", "price": 15}],
        "facebook": [{"id": 1, "name": "1K Followers", "price": 55}, {"id": 2, "name": "1K Video Views", "price": 5}],
        "instagram": [{"id": 1, "name": "1K Likes", "price": 15}, {"id": 2, "name": "1K Followers", "price": 20}]
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
        [InlineKeyboardButton(text="🛍️ 𝐍𝐄𝐖 𝐎𝐑𝐃𝐄𝐑", callback_data="new_order"),
         InlineKeyboardButton(text="💰 𝐏𝐑𝐈𝐂𝐄 & 𝐈𝐍𝐅𝐎", callback_data="price_info")],
        [InlineKeyboardButton(text="💳 𝐃𝐄𝐏𝐎𝐒𝐈𝐓", callback_data="deposit"),
         InlineKeyboardButton(text="👤 𝐌𝐘 𝐀𝐂𝐂𝐎𝐔𝐍𝐓", callback_data="my_account")],
        [InlineKeyboardButton(text="🫂 𝐑𝐄𝐅𝐄𝐑 & 𝐄𝐀𝐑𝐍", callback_data="refer_earn"),
         InlineKeyboardButton(text="🎧 𝐒𝐔𝐏𝐏𝐎𝐑𝐓", callback_data="support")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton(text="⚙️ 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_button(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Return / Back", callback_data="main_menu")]
    ])

async def check_subscription(user_id: int) -> bool:
    channel = bot_settings.get("force_channel")
    if not channel:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        pass
    return False

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id in users_db and users_db[user_id].get("is_banned", False):
        await message.answer("❌ দুঃখিত, আপনি এই বট থেকে ব্যানড হয়েছেন!")
        return

    is_joined = await check_subscription(user_id)
    if not is_joined:
        channel = bot_settings.get("force_channel")
        force_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 চ্যানেলে জয়েন করুন", url=f"https://t.me/{channel.lstrip('@')}")],
            [InlineKeyboardButton(text="✅ Joined", callback_data="check_join")]
        ])
        await message.answer(
            f"⛔ বট ব্যবহারের আগে আমাদের চ্যানেলে জয়েন করুন\n\n📢 আমাদের চ্যানেল:\n➡️ <b>{channel}</b>\n\n✅ সব চ্যানেলে জয়েন করার পর নিচের <b>Joined</b> বাটনে ক্লিক করুন।",
            reply_markup=force_markup, parse_mode="HTML"
        )
        return

    if user_id not in users_db:
        users_db[user_id] = {
            "name": message.from_user.full_name,
            "balance": 0.0,
            "orders": 0, "completed": 0, "pending": 0, "canceled": 0,
            "referrals": 0, "is_banned": False
        }
    welcome_text = f"স্বাগতম <b>{message.from_user.full_name}</b>!\n\nআমাদের 𝗥𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 বটে আপনাকে স্বাগতম। নিচে থেকে আপনার পছন্দের অপশনটি বেছে নিন:"
    await message.answer(welcome_text, reply_markup=get_main_menu(user_id), parse_mode="HTML")

@dp.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_joined = await check_subscription(user_id)
    if not is_joined:
        await callback.answer("❌ আপনি এখনো চ্যানেলে জয়েন করেননি! দয়া করে আগে জয়েন করুন।", show_alert=True)
        return
    
    if user_id not in users_db:
        users_db[user_id] = {
            "name": callback.from_user.full_name,
            "balance": 0.0,
            "orders": 0, "completed": 0, "pending": 0, "canceled": 0,
            "referrals": 0, "is_banned": False
        }
    await callback.message.delete()
    welcome_text = f"স্বাগতম <b>{callback.from_user.full_name}</b>!\n\nআমাদের 𝗥𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 বটে আপনাকে স্বাগতম। নিচে থেকে আপনার পছন্দের অপশনটি বেছে নিন:"
    await callback.message.answer(welcome_text, reply_markup=get_main_menu(user_id), parse_mode="HTML")

@dp.callback_query(F.data == "main_menu")
async def back_to_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_joined = await check_subscription(user_id)
    if not is_joined:
        await callback.answer("⚠️ প্রথমে চ্যানেলে জয়েন করুন!", show_alert=True)
        return
    await callback.message.edit_text("মূল মেনুতে ফিরে এসেছেন:", reply_markup=get_main_menu(user_id))
    await callback.answer()

@dp.callback_query(F.data == "new_order")
async def new_order_menu(callback: CallbackQuery):
    order_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎵 TikTok Services", callback_data="cat_tiktok"),
         InlineKeyboardButton(text="📢 TeleGram Services", callback_data="cat_telegram")],
        [InlineKeyboardButton(text="▶️ YouTube Services", callback_data="cat_youtube"),
         InlineKeyboardButton(text="👥 FaceBook Services", callback_data="cat_facebook")],
        [InlineKeyboardButton(text="📸 Instagram Services", callback_data="cat_instagram")],
        [InlineKeyboardButton(text="🔙 Return", callback_data="main_menu")]
    ])
    await callback.message.edit_text("🛍️ <b>NEW ORDER MENU</b>\n\nদয়া করে আপনার পছন্দের ক্যাটাগরি সিলেক্ট করুন:", reply_markup=order_markup, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_category_services(callback: CallbackQuery):
    cat_key = callback.data.split("_")[1]
    services = bot_settings["services"].get(cat_key, [])
    if not services:
        await callback.answer("এই ক্যাটাগরিতে বর্তমানে কোনো সার্ভিস নেই।", show_alert=True)
        return
    buttons = []
    for s in services:
        buttons.append([InlineKeyboardButton(text=f"🔹 {s['name']} — ৳{s['price']} (Per 1k)", callback_data=f"select_srv_{cat_key}_{s['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Return", callback_data="new_order")])
    await callback.message.edit_text(f"📦 <b>{cat_key.upper()} SERVICES</b>\n\nনিচের সার্ভিসগুলো থেকে সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("select_srv_"))
async def select_service_item(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    cat_key = parts[2]
    srv_id = int(parts[3])
    services = bot_settings["services"].get(cat_key, [])
    selected_service = next((s for s in services if s["id"] == srv_id), None)
    if not selected_service:
        await callback.answer("সার্ভিসটি পাওয়া যায়নি!", show_alert=True)
        return
    await state.update_data(cat=cat_key, service_name=selected_service["name"], price_per_k=selected_service["price"])
    await callback.message.edit_text(f"🔗 আপনি সিলেক্ট করেছেন: <b>{selected_service['name']}</b>\nদাম প্রতি ১০০০: ৳{selected_service['price']}\n\nদয়া করে আপনার টার্গেটেড লিংকটি (Link) এখানে পাঠান:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="main_menu")]]), parse_mode="HTML")
    await state.set_state(OrderProcessState.waiting_for_link)
    await callback.answer()

@dp.message(OrderProcessState.waiting_for_link)
async def order_link_received(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    await message.answer("🔢 আপনি কত পরিমাণ (Quantity) নিতে চান তা সংখ্যায় লিখুন (যেমন: 500 বা 1000):")
    await state.set_state(OrderProcessState.waiting_for_quantity)

@dp.message(OrderProcessState.waiting_for_quantity)
async def order_quantity_received(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ দয়া করে সঠিক সংখ্যা লিখুন:")
        return
    qty = int(message.text)
    data = await state.get_data()
    price_per_k = data.get("price_per_k")
    total_cost = (price_per_k / 1000) * qty
    user_id = message.from_user.id
    current_balance = users_db[user_id]["balance"]
    if current_balance < total_cost:
        await message.answer(f"❌ আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স নেই!\nপ্রয়োজন: ৳{total_cost:.2f} | আপনার আছে: ৳{current_balance:.2f}\n\nদয়া করে আগে ডিপোজিট করুন।", reply_markup=get_main_menu(user_id))
        await state.clear()
        return
    users_db[user_id]["balance"] -= total_cost
    users_db[user_id]["orders"] += 1
    users_db[user_id]["pending"] += 1
    order_id = random.randint(10000000, 99999999)
    orders_db[order_id] = {
        "user_id": user_id, "name": message.from_user.full_name,
        "service": data.get("service_name"), "quantity": qty,
        "cost": total_cost, "link": data.get("link")
    }
    log_channel = bot_settings.get("log_channel")
    banner_img = bot_settings.get("banner_image")
    channel_text = (
        f"🔔 <b>নতুন অর্ডার প্লেস হয়েছে!</b>\n\n👤 কাস্টমার: {message.from_user.full_name}\n"
        f"🆔 ইউজার আইডি: <code>{user_id}</code>\n📦 অর্ডার আইডি: <code>{order_id}</code>\n"
        f"🛠️ সার্ভিস নাম: {data.get('service_name')}\n📦 পরিমাণ: {qty}\n"
        f"🔗 অর্ডার লিংক: {data.get('link')}\n💰 মোট খরচ: ৳{total_cost:.2f}"
    )
    admin_action_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Approve", callback_data=f"ord_acc_{order_id}"),
         InlineKeyboardButton(text="❌ Cancel & Refund", callback_data=f"ord_rej_{order_id}")]
    ])
    try:
        await bot.send_photo(log_channel, photo=banner_img, caption=channel_text, parse_mode="HTML")
    except Exception:
        try:
            await bot.send_message(log_channel, channel_text, parse_mode="HTML")
        except Exception:
            pass
    await bot.send_message(ADMIN_ID, f"📥 <b>অর্ডারের রিকোয়েস্ট:</b>\n\n{channel_text}", reply_markup=admin_action_markup, parse_mode="HTML")
    await message.answer(f"✅ আপনার অর্ডারটি সফলভাবে গ্রহণ করা হয়েছে!\nঅর্ডার আইডি: <code>{order_id}</code>\nখরচ হয়েছে: ৳{total_cost:.2f}", reply_markup=get_main_menu(user_id), parse_mode="HTML")
    await state.clear()
    @dp.callback_query(F.data.startswith("ord_acc_"))
async def approve_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    if order_id in orders_db:
        o = orders_db[order_id]
        users_db[o["user_id"]]["pending"] -= 1
        users_db[o["user_id"]]["completed"] += 1
        await bot.send_message(o["user_id"], f"🎉 অভিনন্দন! আপনার অর্ডার আইডি <code>{order_id}</code> সম্পন্ন (Completed) হয়েছে। ✅", parse_mode="HTML")
        await callback.message.edit_text(f"✅ অর্ডার #{order_id} সফলভাবে অ্যাপ্রুভ করা হয়েছে।")
    await callback.answer()

@dp.callback_query(F.data.startswith("ord_rej_"))
async def cancel_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    if order_id in orders_db:
        o = orders_db[order_id]
        u_id = o["user_id"]
        refund_amount = o["cost"]
        users_db[u_id]["balance"] += refund_amount
        users_db[u_id]["pending"] -= 1
        users_db[u_id]["canceled"] += 1
        await bot.send_message(u_id, f"❌ আপনার অর্ডার আইডি <code>{order_id}</code> বাতিল করা হয়েছে এবং আপনার ৳{refund_amount:.2f} টাকা একাউন্টে রিফান্ড করা হয়েছে।", parse_mode="HTML")
        await callback.message.edit_text(f"❌ অর্ডার #{order_id} ক্যানসেল করা হয়েছে ও টাকা রিফান্ড করা হয়েছে।")
    await callback.answer()

@dp.callback_query(F.data == "my_account")
async def my_account(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = users_db.get(user_id, {"name": callback.from_user.full_name, "balance": 0.0, "orders": 0, "completed": 0, "pending": 0, "canceled": 0})
    text = (
        f"👤 𝐌𝐘 𝐀𝐂𝐂𝐎𝐔𝐍𝐓\n━━━━━━━━━━━━━━━━━━\n🆔 𝐔𝐬𝐞𝐫 𝐈𝐃 : <code>{user_id}</code>\n"
        f"👤 𝐍𝐚𝐦𝐞 : {u['name']}\n💰 𝐁𝐚𝐥𝐚𝐧𝐜𝐞 : ৳ {u['balance']:.2f}\n━━━━━━━━━━━━━━━━━━\n"
        f"📦 𝐓𝐨𝐭𝐚𝐥 𝐎𝐫𝐝𝐞𝐫𝐬 : {u['orders']}\n✅ 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝 𝐎𝐫𝐝𝐞𝐫𝐬 : {u['completed']}\n"
        f"⏳ 𝐏𝐞𝐧𝐝𝐢𝐧𝐠 𝐎𝐫𝐝𝐞𝐫𝐬 : {u['pending']}\n❌ 𝐂𝐚𝐧𝐜𝐞𝐥𝐞𝐝 𝐎𝐫𝐝𝐞𝐫𝐬 : {u['canceled']}"
    )
    await callback.message.edit_text(text, reply_markup=get_back_button(user_id), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "price_info")
async def price_info(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = "━━━━━━━━━━━━━━━━━━━━━━\n📲 𝗥𝗫 𝗦𝗠𝗠 𝗭𝗢𝗡𝗘 – 𝗦𝗘𝗥𝗩𝗜𝗖𝗘 𝗟𝗜𝗦𝗧\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for cat, svcs in bot_settings["services"].items():
        text += f"🔵 <b>{cat.upper()}</b>\n"
        for s in svcs:
            text += f"▪️ {s['name']} — ৳{s['price']}\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    await callback.message.edit_text(text, reply_markup=get_back_button(user_id), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "deposit")
async def deposit_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💳 𝖉𝖊𝖕𝖔𝖘𝖎𝖙 𝖒𝖊𝖓𝖚\n\nআপনি কত টাকা ডিপোজিট করতে চান তার পরিমাণ লিখুন।\n⚠️ সর্বনিম্ন 10 টাকা ডিপোজিট করা যাবে।",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Cancel", callback_data="main_menu")]])
    )
    await state.set_state(DepositState.waiting_for_amount)
    await callback.answer()

@dp.message(DepositState.waiting_for_amount)
async def deposit_amount_received(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 10:
        await message.answer("❌ সর্বনিম্ন ১০ টাকা বা তার বেশি পরিমাণ লিখুন:")
        return
    await state.update_data(amount=message.text)
    await message.answer("📥 টাকা পাঠিয়ে ট্রানজেকশন আইডি বা স্ক্রিনশট দিন:")
    await state.set_state(DepositState.waiting_for_proof)

@dp.message(DepositState.waiting_for_proof)
async def deposit_proof_received(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount")
    user = message.from_user
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Approve", callback_data=f"dep_acc_{user.id}_{amount}"),
         InlineKeyboardButton(text="❌ Reject", callback_data=f"dep_rej_{user.id}")]
    ])
    await bot.send_message(ADMIN_ID, f"🔔 <b>ডিপোজিট রিকোয়েস্ট:</b>\nইউজার: {user.full_name} (`{user.id}`)\nপরিমাণ: ৳{amount}", reply_markup=admin_markup, parse_mode="HTML")
    await message.answer("✅ ডিপোজিট রিকোয়েস্ট জমা হয়েছে।", reply_markup=get_main_menu(user.id))
    await state.clear()

@dp.callback_query(F.data.startswith("dep_acc_"))
async def approve_deposit(callback: CallbackQuery):
    parts = callback.data.split("_")
    user_id = int(parts[2])
    amount = float(parts[3])
    if user_id in users_db:
        users_db[user_id]["balance"] += amount
    await bot.send_message(user_id, f"🎉 আপনার ৳{amount} টাকা ডিপোজিট অ্যাপ্রুভ হয়েছে!")
    await callback.message.edit_text("✅ ডিপোজিট সফলভাবে অ্যাপ্রুভ করা হয়েছে।")
    await callback.answer()

@dp.callback_query(F.data.startswith("dep_rej_"))
async def reject_deposit(callback: CallbackQuery):
    parts = callback.data.split("_")
    user_id = int(parts[2]) if len(parts) > 2 else 0
    await bot.send_message(user_id, "❌ আপনার ডিপোজিট রিকোয়েস্টটি বাতিল করা হয়েছে।")
    await callback.message.edit_text("❌ ডিপোজিট রিজেক্ট করা হয়েছে।")
    await callback.answer()

@dp.callback_query(F.data == "support")
async def support_menu(callback: CallbackQuery):
    current_support = bot_settings.get("support_username", "YourUsername")
    support_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Contact Admin", url=f"https://t.me/{current_support}")],
        [InlineKeyboardButton(text="🔙 Return", callback_data="main_menu")]
    ])
    await callback.message.edit_text("🎧 যেকোনো সমস্যায় যোগাযোগ করুন:", reply_markup=support_markup)
    await callback.answer()

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    text = (
        f"⚙️ <b>ADMIN CONTROL PANEL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 <b>Force Channel:</b> <code>{bot_settings['force_channel']}</code>\n"
        f"📢 <b>Log Channel:</b> <code>{bot_settings['log_channel']}</code>\n"
        f"🎧 <b>Support User:</b> <code>@{bot_settings['support_username']}</code>\n"
        f"🖼️ <b>Banner Image:</b> <code>{bot_settings['banner_image']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"নিচের অপশনগুলো থেকে আপনার বটের সেটিংস পরিবর্তন করুন:"
    )
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Change Force Channel", callback_data="change_force_channel")],
        [InlineKeyboardButton(text="📢 Change Log Channel", callback_data="change_channel"),
         InlineKeyboardButton(text="✏️ Change Support", callback_data="change_support")],
        [InlineKeyboardButton(text="🖼️ Change Banner Image", callback_data="change_image")],
        [InlineKeyboardButton(text="🚫 Ban User", callback_data="ban_user"),
         InlineKeyboardButton(text="✅ Unban User", callback_data="unban_user")],
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=admin_markup, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "change_force_channel")
async def change_force_channel_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("📢 নতুন ফোর্চ সাবস্ক্রিপশন চ্যানেলের ইউজারনেম দিন (যেমন: `@RXPremiumZone`):", reply_markup=get_back_button(ADMIN_ID))
    await state.set_state(AdminActionState.waiting_for_force_channel)
    await callback.answer()

@dp.message(AdminActionState.waiting_for_force_channel)
async def save_new_force_channel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    bot_settings["force_channel"] = message.text.strip()
    await message.answer(f"✅ সফলভাবে ফোর্চ সাবস্ক্রিপশন চ্যানেল আপডেট করা হয়েছে: {bot_settings['force_channel']}")
    await state.clear()

@dp.callback_query(F.data == "change_channel")
async def change_channel_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("📢 নতুন লগ চ্যানেলের ইউজারনেম বা আইডি দিন (যেমন: `@MyOrderChannel`):", reply_markup=get_back_button(ADMIN_ID))
    await state.set_state(AdminActionState.waiting_for_channel)
    await callback.answer()

@dp.message(AdminActionState.waiting_for_channel)
async def save_new_channel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    bot_settings["log_channel"] = message.text.strip()
    await message.answer(f"✅ সফলভাবে লগ চ্যানেল আপডেট করা হয়েছে: {bot_settings['log_channel']}")
    await state.clear()

@dp.callback_query(F.data == "change_support")
async def change_support_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("🎧 নতুন সাপোর্ট ইউজারনেম দিন (যেমন: `@YourUsername`):", reply_markup=get_back_button(ADMIN_ID))
    await state.set_state(AdminActionState.waiting_for_support)
    await callback.answer()

@dp.message(AdminActionState.waiting_for_support)
async def save_new_support(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    username = message.text.strip().lstrip('@')
    bot_settings["support_username"] = username
    await message.answer(f"✅ সফলভাবে সাপোর্ট ইউজারনেম আপডেট করা হয়েছে: @{username}")
    await state.clear()

@dp.callback_query(F.data == "change_image")
async def change_image_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("🖼️ নতুন ব্যানার ইমেজের ডিরেক্ট ইমেজ ইউআরএল (Image URL) দিন:", reply_markup=get_back_button(ADMIN_ID))
    await state.set_state(AdminActionState.waiting_for_image_url)
    await callback.answer()

@dp.message(AdminActionState.waiting_for_image_url)
async def save_new_image(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    bot_settings["banner_image"] = message.text.strip()
    await message.answer(f"✅ সফলভাবে ব্যানার ইমেজ লিংক আপডেট করা হয়েছে!")
    await state.clear()

@dp.callback_query(F.data == "ban_user")
async def ban_user_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("🚫 যে ইউজারের আইডি ব্যান করতে চান তা লিখুন:", reply_markup=get_back_button(ADMIN_ID))
    await state.set_state(AdminActionState.waiting_for_ban_id)
    await state.set_data({"action": "ban"})
    await callback.answer()

@dp.callback_query(F.data == "unban_user")
async def unban_user_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("✅ যে ইউজারের আইডি আনব্যান করতে চান তা লিখুন:", reply_markup=get_back_button(ADMIN_ID))
    await state.set_state(AdminActionState.waiting_for_ban_id)
    await state.set_data({"action": "unban"})
    await callback.answer()

@dp.message(AdminActionState.waiting_for_ban_id)
async def process_ban_unban(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.strip())
        data = await state.get_data()
        action = data.get("action")
        if target_id in users_db:
            if action == "ban":
                users_db[target_id]["is_banned"] = True
                await message.answer(f"✅ ইউজার {target_id} সফলভাবে ব্যান করা হয়েছে।")
            else:
                users_db[target_id]["is_banned"] = False
                await message.answer(f"✅ ইউজার {target_id} সফলভাবে আনব্যান করা হয়েছে।")
        else:
            await message.answer("❌ এই আইডির কোনো ইউজার ডাটাবেসে নেই!")
    except ValueError:
        await message.answer("❌ সঠিক ইউজার আইডি সংখ্যায় লিখুন!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    