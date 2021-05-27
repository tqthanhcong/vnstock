import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title=("Tracking the active buy-sell volume"),
                   layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown("<h1 style='text-align: center; color: green;'>Tracking the active buy-sell volume realtime (8h45 -> 14h45)</h1>", unsafe_allow_html=True)

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
col0.header("Input paremeter")
col0.subheader("Input Symbols")
stocks = col0.multiselect(label="",
                          options=symbols,default=["VN30F1M","VCB"])
col0.subheader("Choose charts")
buy_sell_check = col0.checkbox("Volume buy, sell",value=True)
net_vol_check = col0.checkbox("Net volume (buy-sell)",value=True)
price_check = col0.checkbox("Giá",value=True)
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

for i in range(len(cols)):
    try:
        symbol=stocks[i]
        data_load_state = cols[i].text("Có ngay đây. Chờ chút...")
        df,df_side,df_net,df_price=get_data(symbol)
        data_load_state.empty()
        cols[i].markdown("<h3 style='text-align: center; color: black;'>"+symbol+"</h3>", unsafe_allow_html=True)
        #cols[i].subheader("**"+symbol.upper()+"**")
        #my_str="Giá: " + str(df_price.iloc[-1,0])+\
        #    "  ..... +/- ATO: " + str(round(df_price.iloc[-1,0]-df_price.iloc[0,0],0))+\
        #    " ..... Net_vol: "+ str(df_net.iloc[-1,0])
        #cols[i].markdown("<p style='text-align: center; color: gray;'>" + my_str + "</p>", unsafe_allow_html=True)                          
        if buy_sell_check:
            fig = px.line(df_side, template="plotly_white")
            fig.update_layout(legend=dict(yanchor="top",y=0.99,
                                           xanchor="left",x=0.01,
                                           title_text=''),
                              margin=dict(l=0, r=0, t=20, b=20))
            fig.update_xaxes(title_text='',title_font=dict(size=1))
            fig.update_yaxes(title_text='',title_font=dict(size=1))
            cols[i].plotly_chart(fig,use_container_width=True)
        if net_vol_check:
            cols[i].text("Net active buy volume")
            fig = px.area(df_net, template="plotly_white",height=200)
            fig.update_layout(showlegend =False,
                              margin=dict(l=0, r=0, t=20, b=20))
            fig.update_xaxes(title_text='',title_font=dict(size=1))
            fig.update_yaxes(title_text='',title_font=dict(size=1))
            cols[i].plotly_chart(fig,use_container_width=True)
        if price_check:
            cols[i].subheader("Price")
            df_price.plot(figsize=(16,5))
            cols[i].pyplot(plt)   
    except:
        cols[i].write("Mã này không có")
