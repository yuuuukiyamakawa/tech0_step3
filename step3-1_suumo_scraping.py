
import streamlit as st
import pandas as pd
import numpy as np
from streamlit_folium import st_folium
import folium
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os


if __name__ == '__main__':
    # 環境変数の読み込み
    load_dotenv()

    # GoogleSheetsAPI、GoogleDriveAPIの使用
    SCOPES = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    SEVICE_ACCOUNT_FILE = os.getenv('SEVICE_ACCOUNT_FILE')  # 秘密鍵のjsonファイルを指定
    credentials = ServiceAccountCredentials.from_json_keyfile_name(SEVICE_ACCOUNT_FILE, SCOPES)  # 認証情報を作成

    gs = gspread.authorize(credentials)  # スプレッドシートの操作権を取得
    SPREADSHEET_KEY = os.getenv('SPREADSHEET_KEY')
    workbook = gs.open_by_key(SPREADSHEET_KEY)  # 編集するスプレッドシートの指定

    # 編集するワークシートの指定
    def worksheet(sheet):
        worksheet = workbook.worksheet(sheet)
        return worksheet

    # データの読み込み
    df_scrp = pd.DataFrame(worksheet('data').get_all_values())
    df_scrp.columns = list(df_scrp.iloc[0])
    df_scrp = df_scrp.drop(df_scrp.index[0], axis=0)

    # 前処理
    df_scrp['賃料'] = pd.to_numeric(df_scrp['賃料'], errors='coerce')
    df_scrp['築年数'] = pd.to_numeric(df_scrp['築年数'], errors='coerce').fillna(0).astype(int)


# 設定値_家賃
fee_min = int(np.ceil(df_scrp['賃料'].min()))
fee_max = int(np.ceil(df_scrp['賃料'].max()))
fee_median = int(np.ceil(fee_min+fee_max/2))

# 設定値_築年数
age_min =df_scrp['築年数'].min()
age_max = df_scrp['築年数'].max()
age_median = int(np.ceil(age_min+age_max/2))

# 設定値_間取り
df_madori = pd.DataFrame(worksheet('madori').get_all_values())


# 案内表示
st.sidebar.write("希望の条件を設定してください") 

# サイドバーでのパラメータ設定
set_madori = st.sidebar.multiselect('間取り', df_madori, ['2LDK'])  # 間取りの選択
set_fee = st.sidebar.slider('家賃（万円）', min_value=fee_min, max_value=fee_max, value=fee_median, step=5)  # 家賃の選択
set_age = st.sidebar.slider('築年数（年）', min_value=age_min, max_value=age_max, value=age_median, step=1)  # 築年数の選択

for i in range(0, len(set_madori)):
    filt =''
    if i == 0:
        filt += '間取り=="' + set_madori[i] + '"'
    else:
        filt += '|間取り=="' + set_madori[i] + '"'
df_scrp = df_scrp.query(f'{filt}', engine='python')
df_scrp = df_scrp.query('賃料 <= @set_fee')
df_scrp = df_scrp.query('築年数 <= @set_age')

st.sidebar.write('該当物件数：' + str(len(df_scrp)) + '件')  # 該当物件数の表示


# セッション状態の初期化
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = None

# 検索ボタン
if st.sidebar.button('検索', type='primary'):
    # 検索結果の計算（既存の検索ロジック）
    # ...

    # 検索結果をセッション状態に保存
    st.session_state['search_results'] = df_scrp.copy()

# 検索結果の表示
if st.session_state['search_results'] is not None:
    df_result = st.session_state['search_results']
    result_num = len(df_result)
    df_result.index = np.arange(1, result_num + 1)
    st.write('検索結果：' + str(result_num) + '件')

    # マップとデータリストの表示
    loc = [df_result.loc[df_result.index[0], '経度'], df_result.loc[df_result.index[0], '緯度']]
    map = folium.Map(location=loc, zoom_start=16)

    for i, row in df_result.iterrows():
        location = [row['経度'], row['緯度']]
        folium.Marker(location, tooltip=row['物件名']).add_to(map)

    map_display = st_folium(map, width=1200)
    df_result_display = df_result[['物件名', '住所', 'アクセス1', 'アクセス2', 'アクセス3', '築年数', '賃料', '間取り']]
    data_list = st.dataframe(df_result_display, width=1200)






