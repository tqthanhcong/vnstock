import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests


st.set_page_config(page_title=("Theo dõi khối lượng mua bán chủ động"),
                   layout="wide",
                   initial_sidebar_state="collapsed")
st.title("Theo dõi khối lượng mua bán chủ động")

#get companies list
@st.cache()
def get_symbol_list():
    df=pd.read_csv("listed_company.csv")
    list = df["Symbol"].tolist()
    for x in ["VN30F1M","VN30F2M","VN30F1Q","VN30F2Q"]:
        list.append(x)
    return list


symbols=get_symbol_list()

#divide layout to columns
col0=st.sidebar
col0.header("Nhập thông số")
col0.subheader("Nhập thêm mã cổ phiếu vào đây")
stocks = col0.multiselect(label="",
                          options=symbols,default=["VN30F1M","VCB"])
col0.subheader("Chọn biểu đồ cần vẽ")
buy_sell_check = col0.checkbox("Volume buy, sell",value=True)
net_vol_check = col0.checkbox("Net volume (buy-sell)")
price_check = col0.checkbox("Giá")
col_number=len(stocks)
cols=st.beta_columns(col_number)

#function for get data and clean data
def get_data(symbol):
  #send request to get data
  url="https://svr1.fireant.vn/api/Data/Markets/IntradayQuotes?symbol="+symbol.upper()
  r=requests.get(url)
  df=pd.DataFrame(r.json())
  
  #Choose needed columns
  df=df.iloc[1:,[2,3,4,6]]
  df.columns=["date_time","price","volume","side"]
 
  #Convert datetime
  df=df[df["volume"]>0]
  df["date_time"]=pd.to_datetime(df["date_time"],utc=True)
  df["date_time"] = df["date_time"].dt.tz_convert("Asia/Ho_Chi_Minh")
  df=df[(df["side"]=="B")|(df["side"]=="S")]
  
  df_cum = df.groupby(["side","date_time","price"]).sum().groupby(level=0).cumsum().reset_index()
  df_cum=df_cum.reset_index()
  df_cum=df_cum.sort_values("date_time",ascending=True).set_index("date_time",drop=True)
  
  #df_cum.index = df_cum.index.strftime("%H:%M")
  
  #calculate net volume
  df_cum["buy_vol"]=df_cum["volume"]
  df_cum["sell_vol"]=df_cum["volume"]
  df_cum.loc[df_cum["side"]=="S","buy_vol"]=np.nan
  df_cum.loc[df_cum["side"]=="B","sell_vol"]=np.nan
  df_cum.ffill(inplace=True)
  df_cum.fillna(value=0,inplace=True)
  df_cum["net_vol"]=df_cum["buy_vol"]-df_cum["sell_vol"]
  
  df1=df_cum[["buy_vol","sell_vol"]]
  df2=df_cum[["net_vol"]]
  df3=df_cum[["price"]]
  return df_cum,df1,df2,df3

if st.button("Refresh"):
  for i in range(len(cols)):
    try:
        symbol=stocks[i]
        data_load_state = cols[i].text("Xin chờ một chút...")
        df,df_side,df_net,df_price=get_data(symbol)
        data_load_state.empty()
        
        cols[i].subheader("**"+symbol.upper()+"**")
        cols[i].write("Giá: " + str(df_price.iloc[-1,0]) + \
                      " ***+/- ATO:*** " + "***"+str(round(df_price.iloc[-1,0]-df_price.iloc[0,0],0))+"***")
        cols[i].write("Net_vol: " + str(df_net.iloc[-1,0]))
        
        if buy_sell_check:
            cols[i].line_chart(df_side,height=200)
        if net_vol_check:
            cols[i].text("Khối lượng mua bán ròng")
            cols[i].bar_chart(df_net,height=100)
        if price_check:
            cols[i].subheader("Giá")
            df_price.plot(figsize=(16,5))
            cols[i].pyplot(plt)   
    except:
        cols[i].write("Mã này không có")

for i in range(len(cols)):
    try:
        symbol=stocks[i]
        data_load_state = cols[i].text("Xin chờ một chút...")
        df,df_side,df_net,df_price=get_data(symbol)
        data_load_state.empty()
        
        cols[i].subheader("**"+symbol.upper()+"**")
        cols[i].write("Giá: " + str(df_price.iloc[-1,0]) + \
                      " ***+/- ATO:*** " + "***"+str(round(df_price.iloc[-1,0]-df_price.iloc[0,0],0))+"***")
        cols[i].write("Net_vol: " + str(df_net.iloc[-1,0]))
        
        if buy_sell_check:
            cols[i].line_chart(df_side,height=200)
        if net_vol_check:
            cols[i].text("Khối lượng mua bán ròng")
            cols[i].bar_chart(df_net,height=100)
        if price_check:
            cols[i].subheader("Giá")
            df_price.plot(figsize=(16,5))
            cols[i].pyplot(plt)   
    except:
        cols[i].write("Mã này không có")
