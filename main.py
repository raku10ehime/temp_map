import datetime
import pathlib

import geopandas as gpd
import pandas as pd
import simplekml

JST = datetime.timezone(datetime.timedelta(hours=+9))

dt_now = datetime.datetime.now(JST).replace(tzinfo=None)
dt_3dy = dt_now - datetime.timedelta(days=3)

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTT5Kyh0YLcmiM0dlGmAHcP1NSWVckgGI5OgIbq9weBnrKSPmTfaj471GfIEU4-3dGNIVqccEeZqZF/pub?gid=391974378&single=true&output=csv"

df0 = pd.read_csv(url, parse_dates=["タイムスタンプ"], dtype={"eNB": str, "LCID": str, "備考": str})
df0

# 名前、市町村、町名以降が重複は一番最後のデータを反映
df0.drop_duplicates(subset=["名前", "市町村", "町名以降"], keep="last", inplace=True)

df1 = df0[(df0["タイムスタンプ"] > dt_3dy) & (df0["確認"].isna())].drop(["タイムスタンプ", "確認"], axis=1)

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
    
    df1[["緯度", "経度"]] = df1["緯度・経度"].str.strip("()").str.split(",", expand=True)

    df1["緯度"] = df1["緯度"].str.strip().astype(float)
    df1["経度"] = df1["経度"].str.strip().astype(float)
    
    df1.dropna(subset=["経度", "緯度"], inplace=True)

    df1["場所"] = df1["市町村"].str.cat(df1["町名以降"])

    df1["備考"] = df1["備考"].fillna("")

    df1["eNB-LCID"] = df1["eNB"].str.cat(df1["LCID"], sep="-")

    df1["pid"] = df1["eNB"].astype(int).apply(lambda x: x >> 14)

    df1

    geo_df = gpd.GeoDataFrame(
        df1, geometry=gpd.points_from_xy(df1["経度"], df1["緯度"]), crs=6668
    )

    ehime = gpd.read_file("N03-20210101_38_GML.zip!N03-20210101_38_GML").rename(
        columns={"N03_001": "都道府県名", "N03_004": "市区町村名"}
    )
    ehime

    ehime.crs

    spj = gpd.sjoin(geo_df, ehime, how="left")
    spj

    spj["city"] = spj["市町村"] == spj["市区町村名"]
    spj["pref"] = spj["pid"] == 45

    spj

    df2 = spj.reindex(
        columns=["場所", "緯度", "経度", "eNB-LCID", "pref", "city", "備考"]
    ).copy()

    df2

    csv_path = pathlib.Path("map", "temp.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    df2.to_csv(csv_path, encoding="utf_8_sig")



    for i, r in df2.iterrows():

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
