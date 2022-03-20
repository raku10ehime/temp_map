import datetime
import pathlib

import pandas as pd
import simplekml

JST = datetime.timezone(datetime.timedelta(hours=+9))

dt_now = datetime.datetime.now(JST).replace(tzinfo=None)
dt_3dy = dt_now - datetime.timedelta(days=3)

# スプレッドシートのCSVのURL
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSroTLHVCV2xgBucqPyevEtUblVM2cIpJv6SeZTHcbu_GSFQSNUb6KQyc6CDsFWjk5gieDmx126lWRm/pub?gid=0&single=true&output=csv"

df0 = pd.read_csv(url, parse_dates=["日付"])

# eNB-LCIDが重複は一番最後のデータを反映
df0.drop_duplicates(subset=["eNB-LCID"], keep="last", inplace=True)

df1 = df0[(df0["日付"] > dt_3dy) & (df0["処理"] != "削除")].drop(["日付", "処理"], axis=1)

kml = simplekml.Kml(name="temp")

# 開局

temp_img = kml.addfile("temp.png")

# スタイル
temp_normal = simplekml.Style()
temp_normal.iconstyle.scale = 1
temp_normal.iconstyle.icon.href = temp_img

# スタイル
temp_highlight = simplekml.Style()
temp_highlight.iconstyle.scale = 1
temp_highlight.iconstyle.icon.href = temp_img

temp_stylemap = simplekml.StyleMap()
temp_stylemap.normalstyle = temp_normal
temp_stylemap.highlightstyle = temp_highlight


# スタイルマップに登録

kml.document.stylemaps.append(temp_stylemap)

fol = kml.newfolder()

if len(df1) > 0:

    df1["場所"] = df1["市町村"].str.cat(df1["住所"])

    csv_path = pathlib.Path("map", "temp.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    df1.to_csv(csv_path, encoding="utf_8_sig", index=False)

    for i, r in df1.iterrows():

        pnt = fol.newpoint(name=r["場所"])
        pnt.coords = [(r["経度"], r["緯度"])]

        pnt.stylemap = kml.document.stylemaps[0]
        pnt.description = f'eNB-LCID: {r["eNB-LCID"]}'

        ex_data = simplekml.ExtendedData()

        for n, v in r.items():

            ex_data.newdata(name=str(n), value=str(v))

        pnt.extendeddata = ex_data

kmz_path = pathlib.Path("map", "temp.kmz")

kml.savekmz(kmz_path)
