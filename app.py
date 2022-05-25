import os
import json
import logging
import time
import requests
import boto3
import csv

from chalice import Chalice
from chalice import BadRequestError, ForbiddenError

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage, TextSendMessage, PostbackEvent, StickerMessage, StickerSendMessage

app = Chalice(app_name='kisopro-zoho-gi')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = WebhookHandler('xxx')
line_bot = LineBotApi('')
os.chdir('/tmp')#ここじゃないとLambdaで読み書き出来ない

def id_quiz(w_id,hintn,text):#idのある場合
    S = requests.Session()#w_idの記事を取得、不正解ならヒントを表示
    URL = "https://ja.wikipedia.org/w/api.php"
    ARTICLE_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,
        "exsectionformat": "plain",
        "pageids": w_id
    }
    ARTICLE_R = S.get(url=URL, params=ARTICLE_PARAMS)
    ARTICLE_DATA = ARTICLE_R.json()
    ans = ARTICLE_DATA["query"]["pages"][str(w_id)]['title']
    if('(' in ans):
        ans = ans.split('(')[0]#()で別の読みを紹介している場所は答えに含まれない
    ans = ans.replace(' ','')
    if(str(text)==str(ans)):#正解なら正解を表示し終了
        return ["0","0"]
    content = ARTICLE_DATA["query"]["pages"][str(w_id)]["extract"]
    content = content.split("\n\n\n")#不正解ならヒントを表示、hintnからhintを錬成
    if(int(hintn) >= len(content) or int(hintn)>=6):#用意できるヒントの数もうない場合
        return ["1",ans]#nomore hints
    if(type(content)!=list):
        return ["1",ans]#nomore hints
    hint = content[int(hintn)]#まだヒントがある場合
    titlemaru = ""#たまに答えが入ってしまっているので○で置換
    ansnum = len(ans)
    for i in range(ansnum):
        titlemaru +="○"
    hint = hint.replace(ans,titlemaru)
    if(len(hint)>120):
        hint = hint[:120] #120文字程度のヒントを錬成
    return ["2",hint+"..."]


#クイズ新作、つまりuser_idがなかった場合
def new_quiz():
    S = requests.Session()
    URL = "https://ja.wikipedia.org/w/api.php"
    #wikipediaのランダム記事リスト（idとタイトル）を取得するためのパラメータの設定
    RANDOM_PARAMS = {
        "action": "query",
        "format": "json",
        "list": "random",
        "rnlimit": "1",
        "rnnamespace": "0"
    }
    ARTICLE_PARAMS = {#記事本体を取得する
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,
        "exsectionformat": "plain",
    }
    RANDOM_R = S.get(url=URL, params=RANDOM_PARAMS)
    RANDOM_DATA = RANDOM_R.json()
    w_id=(RANDOM_DATA["query"]["random"])[0]['id']
    ARTICLE_PARAMS["pageids"] = str(w_id)
    ARTICLE_R = S.get(url=URL, params=ARTICLE_PARAMS)
    ARTICLE_DATA = ARTICLE_R.json()
    #print(ARTICLE_DATA)
    ans = ARTICLE_DATA["query"]["pages"][str(w_id)]['title']
    if('(' in ans):
        ans = ans.split('(')[0]#()で別の読みを紹介している場所は答えに含まれない
    ans = ans.replace(' ','')
    ansnum = len(ans)
    #print(ARTICLE_DATA["query"]["pages"][str(w_id)]['extract'])
    content = ARTICLE_DATA["query"]["pages"][str(w_id)]["extract"]
    content = content.replace('）は', '。')#最初の説明文、「は、」を「。」に置換
    content = content.split('。')#「○○は、～～～。」まで抽出するための処理。
    titlemaru=""#答えを○○にする
    for i in range(ansnum):
        titlemaru +="○"
    quiz = "【問題】\n"+titlemaru + "は" + content[1]+"。"#最初の文が完成
    return [quiz,w_id]

def delquiz(now_id):#ボタンの右の場合。強制終了、リセット
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('wikilist')
    bucket.download_file('test.csv', 'test_myd.csv')
    filename = 'test_myd.csv'
    dict={}
    with open(filename, encoding='utf8', newline='') as f:
        csvreader = csv.reader(f)
        dict = {rows[0]:rows[1] for rows in csvreader}
    w_id = dict[now_id][1:]
    reply ="リセット。　答え\n http://ja.wikipedia.org/w/index.php?curid="+str(w_id)
    del dict[now_id]
    with open(filename, 'w') as f:  
        writer = csv.writer(f)
        for k, v in dict.items():
            writer.writerow([k, v])
    bucket.upload_file('test_myd.csv', 'test.csv')
    return reply

def runquiz(now_id,text):#会話入力時、クイズの処理全般
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('wikilist')
    bucket.download_file('test.csv', 'test_myd.csv')
    filename = 'test_myd.csv'
    dict={}
    with open(filename, encoding='utf8', newline='') as f:
        csvreader = csv.reader(f)
        dict = {rows[0]:rows[1] for rows in csvreader}

    if(now_id in dict):#クイズがある場合
        w_id = dict[now_id][1:]
        hintn = dict[now_id][:1]
        res = id_quiz(w_id,hintn,text)
        if(res[0] == "0"):#正解の場合
            reply = "正解！\n http://ja.wikipedia.org/w/index.php?curid="+str(w_id)
            del dict[now_id]
        elif(res[0] == "1"):
            reply = "不正解。\n 答え\n http://ja.wikipedia.org/w/index.php?curid="+str(w_id)
            del dict[now_id]
        else:
            reply = "不正解。\n hint"+str(hintn)+"\n"+res[1]
            hintn=int(hintn)+1#ヒント＋１
            dict[now_id] = str(hintn)+w_id
    else:#useridがないとき新しくクイズを錬成
        new_q = new_quiz()
        dict[now_id] = "1"+str(new_q[1])
        reply = new_q[0]
    with open(filename, 'w') as f:  
        writer = csv.writer(f)
        for k, v in dict.items():
            writer.writerow([k, v])
    bucket.upload_file('test_myd.csv', 'test.csv')
    return reply

    #既にクイズがある場合


@app.route('/')
def index():
    return {'hello': 'world'}


# webhook
@app.route('/callback', methods=['POST'])
def callback():
    try:
        request = app.current_request
        #logger.info(json.dumps(request.json_body))

        signature = request.headers['X-Line-Signature']
        #logger.info(signature)

        body = request.raw_body.decode('utf8')

        handler.handle(body, signature)

    except InvalidSignatureError as err:
        logger.exception(err)
        raise ForbiddenError('Invalid signature.')

    except Exception as err:
        logger.exception(err)
        raise BadRequestError('Invalid Request.')

    return {}


# Message Event
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    # Return the original message
    reply_token = event.reply_token
    user_id = event.source.user_id
    reply = runquiz(user_id, event.message.text)
    line_bot.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


@handler.add(PostbackEvent)
def on_postback(event):
    reply_token = event.reply_token
    user_id = event.source.user_id
    postback_msg = event.postback.data
    #logger.info(postback_msg)
    if(postback_msg == "left"):
        reply = runquiz(user_id,"")
    if(postback_msg == "right"):
        reply = delquiz(user_id)

    line_bot.push_message(
        to=user_id,
        messages=TextSendMessage(text=reply)
    )