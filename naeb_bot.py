import random
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

BOT_TOKEN = "8914156159:AAGIC1Moru13sSpyV2o23aC4u6xD01PZ5vs"
ADMIN_IDS = [5646012584, 7433528306]

coupons = {}
issued_coupons = set()

def generate_unique_coupon():
    if len(issued_coupons) >= 90000:
        return None
    while True:
        coupon = str(random.randint(10000, 99999))
        if coupon not in issued_coupons:
            issued_coupons.add(coupon)
            return coupon

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name

    if user_id in coupons:
        coupon_data = coupons[user_id]
        if coupon_data['confirmed']:
            await update.message.reply_text(
                f"⚠️ {username}, ваш купон уже использован!\n\n"
                f"За помощью обратитесь в кассу 4 кабинета."
            )
        else:
            await update.message.reply_text(
                f"⚠️ {username}, ваш купон уже активирован, но ещё не подтверждён!\n\n"
                f"За помощью обратитесь в кассу 4 кабинета."
            )
        return

    coupon_number = generate_unique_coupon()
    if coupon_number is None:
        await update.message.reply_text(
            "❌ Извините, все купоны закончились!\n\n"
            f"За помощью обратитесь в кассу 4 кабинета."
        )
        return

    activation_time = datetime.now()
    coupons[user_id] = {
        'code': coupon_number,
        'time': activation_time,
        'confirmed': False,
        'username': username
    }

    if is_admin(user_id):
        await update.message.reply_text(
            f"👋 Привет, {username}!\n\n"
            f"Вы вошли как администратор.\n"
            f"Используйте /codes для управления купонами и /check для проверки кодов."
        )
    else:
        await update.message.reply_text(
            f"🎉 Поздравляем, {username}!\n\n"
            f"🎫 Ваш купон: <b>{coupon_number}</b>\n"
            f"💰 Купон дает право на получение 5 фишек\n\n"
            f"📍 Пожалуйста, подойдите в <b>4 кабинет</b> и предъявите свой купон.",
            parse_mode="HTML"
        )

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 Новый купон активирован!\n\n"
                         f"👤 Пользователь: {username}\n"
                         f"🕒 Время: {activation_time.strftime('%H:%M:%S')}"
                )
            except:
                pass

async def codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return

    active_coupons = {uid: data for uid, data in coupons.items() if not is_admin(uid)}

    if not active_coupons:
        await update.message.reply_text("📋 Список купонов пуст.")
        return

    keyboard = []
    for user_id, data in active_coupons.items():
        status = "✅" if data['confirmed'] else "❌"
        time_str = data['time'].strftime('%H:%M:%S')
        button_text = f"{status} {data['code']} - {data['username']} ({time_str})"

        if not data['confirmed']:
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"confirm_{user_id}")])
        else:
            keyboard.append([InlineKeyboardButton(button_text, callback_data="none")])

    await update.message.reply_text(
        "📋 Список активированных купонов:\n\n"
        "❌ - не подтверждён\n"
        "✅ - подтверждён\n\n"
        "Нажмите на ❌ чтобы подтвердить купон:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав администратора.")
        return

    if not context.args:
        await update.message.reply_text("Использование: /check <код>")
        return

    code = context.args[0]
    for user_id, data in coupons.items():
        if data['code'] == code:
            status = "✅ Подтверждён" if data['confirmed'] else "❌ Не подтверждён"
            time_str = data['time'].strftime('%Y-%m-%d %H:%M:%S')
            await update.message.reply_text(
                f"🎫 Код: {code}\n"
                f"👤 Пользователь: {data['username']} (ID: {user_id})\n"
                f"🕒 Активирован: {time_str}\n"
                f"📊 Статус: {status}"
            )
            return

    await update.message.reply_text(f"❌ Код {code} не найден.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "none":
        return

    if data.startswith("confirm_"):
        if not is_admin(query.from_user.id):
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return

        user_id = int(data.split("_")[1])
        if user_id in coupons:
            coupons[user_id]['confirmed'] = True

            active_coupons = {uid: d for uid, d in coupons.items() if not is_admin(uid)}

            keyboard = []
            for uid, data_coupon in active_coupons.items():
                status = "✅" if data_coupon['confirmed'] else "❌"
                time_str = data_coupon['time'].strftime('%H:%M:%S')
                button_text = f"{status} {data_coupon['code']} - {data_coupon['username']} ({time_str})"

                if not data_coupon['confirmed']:
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"confirm_{uid}")])
                else:
                    keyboard.append([InlineKeyboardButton(button_text, callback_data="none")])

            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ Ваш купон подтверждён администратором! Можете получить фишки."
                )
            except:
                pass
        else:
            await query.edit_message_text("❌ Пользователь не найден.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("codes", codes))
    application.add_handler(CommandHandler("check", check))
    application.add_handler(CallbackQueryHandler(button_callback))
    print("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()