# ライブラリのインポート
import requests
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd

import gspread
from oauth2client.service_account import ServiceAccountCredentials

data_list = []

# suumoサイトで東京都港区の賃貸物件を検索
url = 'https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13103&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1&page={}'

# スクレイピングページ数の指定
max_page = 2

# 1-指定ページまでをスクレイピング
for i in range(1,max_page+1):

    target_url = url.format(i)
    res = requests.get(target_url)

    # スクレイピング先のサーバー負荷軽減の為、1ページ情報を取得後に1秒のディレイ
    sleep(1)

    soup = BeautifulSoup(res.text, 'html.parser')  

    # 物件情報の取得
    contents = soup.find_all('div',class_= 'cassetteitem')

    # 1物件ずつ情報の取得
    for content in contents:
        
        # 物件名、住所、アクセス、築年数、階建 情報ブロック
        detail = content.find('div',class_='cassetteitem-detail')
        # 階数、賃料、管理費、敷金、礼金、間取り、面積 情報ブロック
        table = content.find('table', class_='cassetteitem_other')

        # 物件名、住所、アクセス、築年数、階建の取得
        title = content.find('div', class_= 'cassetteitem_content-title').text
        address = content.find('li', class_= 'cassetteitem_detail-col1').text
        access = content.find('li', class_= 'cassetteitem_detail-col2').text
        age = content.find('li', class_= 'cassetteitem_detail-col3').find_all('div')[0].text
        story = content.find('li', class_= 'cassetteitem_detail-col3').find_all('div')[1].text

        # テーブルの行情報の取得
        tr_tags = table.find_all('tr',class_='js-cassette_link')

        # リスト1列毎に階数、賃料、管理費、敷金、礼金、間取り、面積の取得
        for tr_tag in tr_tags:
            floor, price, first_fee, capacity = tr_tag.find_all('td')[2:6]

            fee, management_fee = price.find_all('li')
            deposit, gratuity = first_fee.find_all('li')
            madori, menseki = capacity.find_all('li')

            # 取得した情報を辞書に格納
            data = {
                'title':title,
                'address':address,
                'access':access,
                'age':age,
                'story':story,
                'floor':floor.text,
                'fee':fee.text,
                'management_fee':management_fee.text,
                'deposit':deposit.text,
                'gratuity':gratuity.text,
                'madori':madori.text,
                'menseki':menseki.text
            }

            data_list.append(data)

    # データフレームを作成する
    df = pd.DataFrame(data_list)


# 使用するGoogleSheetsAPI、GoogleDriveAPI情報の指定
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://spreadsheets.google.com/feeds'
]

# 秘密鍵のjsonファイルを指定
SEVICE_ACCOUNT_FILE = ''

# 認証情報を作成
credentials = ServiceAccountCredentials.from_json_keyfile_name(SEVICE_ACCOUNT_FILE, SCOPES)

# スプレッドシートの操作件を取得
gs = gspread.authorize(credentials)

# 編集するスプレッドシートとワークシートの指定
SPREADSHEET_KEY = ''
workbook = gs.open_by_key(SPREADSHEET_KEY)
worksheet = workbook.worksheet("シート1")

# dfから値を習得
values = [df.columns.values.tolist()] + df.values.tolist()

# スプレッドシートにデータを追加
worksheet.update("A1", values)