import asyncio
import random
import aiosqlite
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ChatPermissions
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus

# === ВСТАВЬ СВОЙ ТОКЕН ОТ BOTFATHER ===
API_TOKEN = "8278496682:AAEpQdJdFfO1oW-IjO7SOynDegr-pVlVhK4"

# === РАНГИ И ОПЫТ ===
RANKS = [
    ("Пепел", 0), ("Новичок", 100), ("Искатель", 235), ("Посвящённый", 505),
    ("Хранитель порога", 810), ("Страж теней", 1250), ("Пламя пробуждения", 1725),
    ("Писарь Архива", 2335), ("Смотритель пыли", 2980), ("Голос забвения", 3760),
    ("Ткач судеб", 4575), ("Око Архива", 5525), ("Тень предзнаменования", 6510),
    ("Носитель знаний", 7630), ("Повелитель ключей", 8785), ("Хранитель врат", 10075),
    ("Вестник истины", 11400), ("Призрак кода", 12860), ("Судья памяти", 14355),
    ("Повелитель теней", 15985), ("Владыка записей", 17650), ("Пророк байтов", 19450),
    ("Повелитель уровней", 21285), ("Архивариус", 23255), ("Тень вечности", 25260),
    ("Хранитель кодекса", 27400), ("Повелитель пыли", 29575), ("Господин забвения", 31885),
    ("Владыка Архива", 34230), ("Бессмертный", 36710), ("Тень бытия", 39225),
    ("Повелитель реальности", 41875), ("Хранитель бытия", 44560), ("Господин кода", 47380),
    ("Архитектор теней", 50235), ("Повелитель времени", 53225), ("Бог Архива", 59410),
    ("Вне времени", 68605), ("Вне кода", 77665), ("Вне Архива", 86660)
]

# === ПРОРОЧЕСТВА ===
PROPHECIES = [
    "🕯️ Когда луна коснётся окна сервера, ты услышишь стон удаляемых файлов.",
    "🌑 Под маской анонима скрывается тот, кто знает твою смертную дату.",
    "📜 В полночь ты найдёшь сообщение, написанное твоим почерком. Но ты его не писал.",
    "🔥 Кто-то ставит тебе «+» из пустоты. Его аккаунт — призрак.",
    "👁️ Ты увидишь своё имя в логах, датированных 31.12.2099. Не читай дальше.",
    "⚡ Один клик — и ты пересечёшь грань. Обратно не будет.",
    "💀 Тень в чате — не ошибка. Она наблюдает. Она ждёт.",
    "🕯️ Архив шепчет: твой следующий уровень — жертвоприношение.",
    "🌑 Не доверяй тому, у кого нет истории. Он — пустота, пришедшая поглотить.",
]

# === ДОСТИЖЕНИЯ ===
ACHIEVEMENTS = {
    1: ("Шёпот Архива", "Ты написал 100 сообщений в Архиве.", False),
    2: ("Огни пустоты", "Ты оставил 1000 следов в пустоте.", False),
    3: ("След из пепла", "5000 слов твоих застыли в пепле.", False),
    4: ("Дыхание теней", "10000 сообщений слиялись с тьмой.", False),
    5: ("Чтец кодекса", "Ты достиг 1000 опыта и услышал голос Архива.", False),
    6: ("Голос из тьмы", "Ты впервые услышал одобрение — «+».", False),
    7: ("Клеймо позора", "Первый «-» коснулся твоего имени.", False),
    8: ("Хранитель искры", "Ты обрёл репутацию +25.", False),
    9: ("Тень у ворот", "Ты пал до репутации -25.", False),
    10: ("Идущий в Архив", "Ты достиг ранга «Пламя пробуждения».", False),
    11: ("Связанный временем", "Ты пробыл неделю в Архиве.", False),
    12: ("Голос пророчества", "Ты трижды вызвал пророчество.", False),
    13: ("Наперсник Архива", "Твоя репутация вознеслась до +100.", False),
    14: ("Заклейменный", "Твоё имя поглотила метка -100.", False),
    15: ("Око Архива", "Ты вошёл в топ-3 лидеров.", False),
    16: ("Сломанный круг", "Ты вынес приговор сам себе — «-».", True),
    17: ("Призрак в сети", "Ты воззвал к модераторам через /report.", True),
    18: ("Глас извне", "Ты позвал Архив ровно в 03:33.", True),
    19: ("Забытый ключ", "Ты достиг странной отметки: 6666xp.", True),
    20: ("Порог Архива", "Ты стал Бессмертным…", True),
}

# === БАЗА ===
async def init_db():
    async with aiosqlite.connect("gothic_users.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            exp INTEGER DEFAULT 0,
            reputation INTEGER DEFAULT 0,
            last_message TIMESTAMP,
            achievements TEXT DEFAULT "",
            joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prorock_count INTEGER DEFAULT 0,
            messages_count INTEGER DEFAULT 0
        )
        """)
        await db.commit()

# === ЛОГИКА ===
def get_rank(exp: int):
    rank_name = RANKS[0][0]
    for r, xp in RANKS:
        if exp >= xp: rank_name = r
    return rank_name

async def give_achievement(user_id: int, ach_id: int, message: types.Message):
    async with aiosqlite.connect("gothic_users.db") as db:
        cur = await db.execute("SELECT achievements FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if not row: return
        already = row[0].split(",") if row[0] else []
        if str(ach_id) in already: return
        already.append(str(ach_id))
        await db.execute("UPDATE users SET achievements=? WHERE user_id=?", (",".join(already), user_id))
        await db.commit()
    name, desc, secret = ACHIEVEMENTS[ach_id]
    await message.reply(f"🏅 Достижение!\n<b>{name}</b>\n{desc}")

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# === Обработка обычных сообщений (опыт/репутация) ===
@dp.message(F.text & ~F.text.startswith("/"))
async def message_handler(message: types.Message):
    if message.chat.type not in ("group", "supergroup"): return
    uid = message.from_user.id
    uname = message.from_user.username or message.from_user.full_name
    async with aiosqlite.connect("gothic_users.db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (uid, uname))
        await db.commit()
        cur = await db.execute("SELECT exp, reputation, last_message, messages_count FROM users WHERE user_id=?", (uid,))
        exp, rep, last_msg, msgs = await cur.fetchone()
        msgs += 1
        now = datetime.now()
        if not last_msg or (now - datetime.fromisoformat(last_msg)).seconds > 180:
            exp += 5
        if message.text.strip() == "+":
            rep = min(rep + 1, 255); 
            if rep >= 1: await give_achievement(uid, 6, message)
            if rep >= 25: await give_achievement(uid, 8, message)
            if rep >= 100: await give_achievement(uid, 13, message)
        elif message.text.strip() == "-":
            rep = max(rep - 1, -255);
            if rep <= -1: await give_achievement(uid, 7, message)
            if rep <= -25: await give_achievement(uid, 9, message)
            if rep <= -100: await give_achievement(uid, 14, message)
        await db.execute("UPDATE users SET exp=?, reputation=?, last_message=?, username=?, messages_count=? WHERE user_id=?",
                         (exp, rep, now.isoformat(), uname, msgs, uid))
        await db.commit()
    if msgs == 100: await give_achievement(uid, 1, message)
    if msgs == 1000: await give_achievement(uid, 2, message)
    if msgs == 5000: await give_achievement(uid, 3, message)
    if msgs == 10000: await give_achievement(uid, 4, message)
    if exp >= 1000: await give_achievement(uid, 5, message)
    if exp == 6666: await give_achievement(uid, 19, message)
    if get_rank(exp) == "Пламя пробуждения": await give_achievement(uid, 10, message)
    if get_rank(exp) == "Бессмертный": await give_achievement(uid, 20, message)

# === Команды ===
@dp.message(Command("xp"))
async def cmd_xp(message: types.Message):
    uid = message.from_user.id
    async with aiosqlite.connect("gothic_users.db") as db:
        cur = await db.execute("SELECT exp, reputation, achievements FROM users WHERE user_id=?", (uid,))
        row = await cur.fetchone()
        if not row: await message.reply("Ты ещё не в Архиве."); return
        exp, rep, ach = row
        await message.reply(f"✨ Опыт: {exp}\n🏆 Ранг: {get_rank(exp)}\n📊 Репутация: {rep}\n🎖 Достижений: {len(ach.split(',')) if ach else 0}")

@dp.message(Command("leaders"))
async def cmd_leaders(message: types.Message):
    async with aiosqlite.connect("gothic_users.db") as db:
        cur = await db.execute("SELECT username, exp, reputation FROM users ORDER BY exp DESC, reputation DESC LIMIT 10")
        rows = await cur.fetchall()
    text = "🏆 Доска лидеров:\n\n" + "\n".join([f"{i+1}. {u} — {get_rank(xp)}, {xp}xp, реп {rep}" for i,(u,xp,rep) in enumerate(rows)])
    await message.reply(text)

@dp.message(Command("prorock"))
async def cmd_prorock(message: types.Message):
    uid = message.from_user.id
    async with aiosqlite.connect("gothic_users.db") as db:
        cur = await db.execute("SELECT prorock_count FROM users WHERE user_id=?", (uid,))
        r = await cur.fetchone()
        count = (r[0] if r else 0) + 1
        await db.execute("UPDATE users SET prorock_count=? WHERE user_id=?", (count, uid))
        await db.commit()
    if count == 3: await give_achievement(uid, 12, message)
    await message.reply(random.choice(PROPHECIES))

@dp.message(Command("achievements"))
async def cmd_achievements(message: types.Message):
    uid = message.from_user.id
    async with aiosqlite.connect("gothic_users.db") as db:
        cur = await db.execute("SELECT achievements FROM users WHERE user_id=?", (uid,))
        row = await cur.fetchone()
        if not row: await message.reply("Ты ещё не оставил следа в Архиве."); return
        user_ach = row[0].split(",") if row[0] else []
    text = "🎖️ <b>Достижения:</b>\n\n"
    for aid,(name,desc,secret) in ACHIEVEMENTS.items():
        if str(aid) in user_ach: text += f"✅ <b>{name}</b>\n{desc}\n\n"
        else: text += f"❌ <b>{name if not secret else '???'}</b>\n{desc if not secret else 'Скрыто'}\n\n"
    await message.reply(text)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    if datetime.now().strftime("%H:%M") == "03:33": await give_achievement(message.from_user.id, 18, message)
    await message.reply("""
⚔️ Команды:
/xp — опыт, ранг и репутация
/leaders — топ
/prorock — пророчество
/achievements — твои достижения
/report — жалоба
/help — помощь
""")

@dp.message(Command("report"))
async def cmd_report(message: types.Message):
    await give_achievement(message.from_user.id, 17, message)
    await message.reply("⚔️ Модераторы услышали твой зов.")

# === Модерация ===
async def is_admin(message: types.Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

@dp.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not await is_admin(message): await message.reply("🚫 Нет власти."); return
    if not message.reply_to_message: await message.reply("Используй: /ban в ответ."); return
    u = message.reply_to_message.from_user; 
    await bot.ban_chat_member(message.chat.id, u.id)
    await message.reply(f"⚔️ {u.full_name} изгнан с позором!")

@dp.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not await is_admin(message): await message.reply("🚫 Нет власти."); return
    if not message.reply_to_message: await message.reply("Используй: /unban в ответ."); return
    u = message.reply_to_message.from_user
    await bot.unban_chat_member(message.chat.id, u.id)
    await message.reply(f"🔓 {u.full_name} возвращён в Архив.")

@dp.message(Command("kik"))
async def cmd_kik(message: types.Message):
    if not await is_admin(message): await message.reply("🚫 Нет власти."); return
    if not message.reply_to_message: await message.reply("Используй: /kik в ответ."); return
    u = message.reply_to_message.from_user
    await bot.ban_chat_member(message.chat.id, u.id); await bot.unban_chat_member(message.chat.id, u.id)
    await message.reply(f"💨 {u.full_name} изгнан из Архива.")

@dp.message(Command("mute"))
async def cmd_mute(message: types.Message):
    if not await is_admin(message): await message.reply("🚫 Нет власти."); return
    if not message.reply_to_message: await message.reply("Используй: /mute <минуты> в ответ."); return
    args=message.text.split()
    if len(args)<2: await message.reply("Пример: /mute 60"); return
    try: minutes=int(args[1]); assert 1<=minutes<=60000
    except: await message.reply("Минуты должны быть числом от 1 до 60000."); return
    until=datetime.now()+timedelta(minutes=minutes)
    u=message.reply_to_message.from_user
    await bot.restrict_chat_member(message.chat.id,u.id,permissions=ChatPermissions(can_send_messages=False),until_date=until)
    await message.reply(f"🔇 {u.full_name} лишён голоса на {minutes} минут.")

@dp.message(Command("unmute"))
async def cmd_unmute(message: types.Message):
    if not await is_admin(message): await message.reply("🚫 Нет власти."); return
    if not message.reply_to_message: await message.reply("Используй: /unmute в ответ."); return
    u=message.reply_to_message.from_user
    await bot.restrict_chat_member(message.chat.id,u.id,permissions=ChatPermissions(can_send_messages=True))
    await message.reply(f"🔊 {u.full_name} снова услышан Архивом.")

# === START ===
async def main():
    await init_db()
    print("🔥 Gothic Bot запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
