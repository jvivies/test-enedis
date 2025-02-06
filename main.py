import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

def getPicker():
    today = datetime.datetime.now()
    next_year = today.year 
    ttoday= datetime.date(next_year, 1, 1)
    jan_1 = datetime.date(next_year-2, 1, 1)
    dec_31 = datetime.date(next_year, 12, 31)

    d = st.date_input(
        "Filter by Date Range",
        (ttoday, datetime.date(next_year, 1, 7)),
        jan_1,
        dec_31,
        format="MM.DD.YYYY",
    )
    return d
custom_html = """<div class="banner">
    <img src="https://static.wixstatic.com/media/87260b_3ae09b2243664894b60911bf6f830397~mv2.png/v1/fill/w_418,h_150,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/Logo_enedis_header.png" alt="Banner Image">
    </div>
    <style>
        .banner {
            width: 140%;
            height: 200px;
            overflow: hidden;
        }
        .banner img {
            width: 400px;
            object-fit: cover;
        }
    </style>
"""

st.components.v1.html(custom_html)

gir = pd.read_excel("./data/GIR_01_25.xlsx")  
use = pd.read_excel("./data/USE_01_25.xlsx") 
use=use.rename(columns={'Immatriculation': 'IMMATRICULATION'})

immatriculation_options = use['IMMATRICULATION'].unique()

st.title('Booking, Distance and Battery Level Over Time')

col1,col2,col3=st.columns([1,1,2])
filters = col1.toggle("Filter by Car", value=False)
filterDate = col2.toggle("Filter by Date Range", value=False)
group = col3.toggle("Group Booking", value=False)

if filterDate:
    res=getPicker()
    if len(res) != 2:
        st.stop()

use['Date'] = pd.to_datetime(use['Date'],format="%d/%m/%Y")

# FILTER BY DATE RANGE
if filterDate:
    startt,endd=res
    startt=pd.to_datetime(startt)
    endd=pd.to_datetime(endd)
    use=use[use["Date"].isin(pd.date_range(startt, endd))]
    # for whatever reason the IsIn doesn;t work, sounds like a format issue (reset index?)..
    s=pd.to_datetime(gir['Date départ'])
    gir=gir[(s>pd.to_datetime(startt))&(s<pd.to_datetime(endd))]

if filters:
    multisel=st.multiselect('Select Immatriculations:',immatriculation_options,default=immatriculation_options[0])    


# APPLY IMMAT FILTERS
if filters:
    use=use[use["IMMATRICULATION"].isin(multisel)]
    gir = gir[gir["IMMATRICULATION"].isin(multisel)]

# KEEP INTACT FOR RAW DISPLAY -- DEBUG
disp1=use.copy()
disp2=gir.copy()

# CLEAN AND ADD MISSING DAYS FOR USAGE
use['Niveau batterie départ'] = use['Niveau batterie départ']*100
use["Début"] = pd.to_datetime(use["Date"].astype(str) + " " + use["Début"], format="%Y-%m-%d %H:%M")
use["Fin"] = pd.to_datetime(use["Date"].astype(str) + " " + use["Fin"], format="%Y-%m-%d %H:%M")

if filters and len(multisel)==0:
    st.info('Select at least One Car')
    st.stop()

use=use.drop(columns=['IMMATRICULATION'])
use=use.resample('D',on='Date').mean()
use=use.reset_index()

# BUILD BOOKING DF
gir['Task']=gir['IMMATRICULATION']
gir['Start']=gir['Date départ']
gir['Start Day'] = gir['Date départ'].dt.dayofweek
gir['Start Day'] = gir['Start Day'].map({
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
})
gir['End Day'] = gir['Date retour'].dt.dayofweek
gir['End Day'] = gir['End Day'].map({
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
})
gir['Booked']='ALL'
gir['Finish']=gir['Date retour']

ygroup="IMMATRICULATION"
if group:
    ygroup="Booked"

# CHARTS
colors = ['#88b947', '#88b947', '#88b947']
fig = px.timeline(gir, x_start="Start", x_end="Finish", y=ygroup,color_discrete_sequence=colors,height=650)
fig.update_layout(showlegend=False)
fig.update_layout(yaxis={'dtick':1})
fig.update_yaxes(
    title="",
    tickson="boundaries",
    fixedrange=True,
)

trace1=go.Scatter(x=use['Début'], 
    y=use['Distance'],
    line_color = 'blue',
    mode = 'lines+markers',
    showlegend = False,
)
trace2=go.Scatter(x=use['Début'], 
    y = use['Niveau batterie départ'], 
    line_color = '#88b947',
    mode = 'lines+markers',
    showlegend = False)
figcombo = make_subplots(rows=3, cols=1, figure=fig, shared_xaxes=True,row_heights = [0.5, 0.3, 0.3])
fig.add_trace(trace1, row=2, col=1)
fig.add_trace(trace2, row=3, col=1)
fig.update_layout(xaxis1_showticklabels=False, xaxis2_showticklabels=False, xaxis3_showticklabels=True,yaxis3_range=[0,110],yaxis2_title_text='Distance(KM)',yaxis3_title_text='Battery(%)')
          
st.plotly_chart(figcombo, use_container_width=True)
with st.expander("Raw Data"):
    st.write("Usage:")
    st.dataframe(disp1,use_container_width=True,hide_index=True)
    st.write("Booking:")
    st.dataframe(disp2,use_container_width=True,hide_index=True)

# UI TWEAKS
def setUI():
    hvar='''
        <script>
            var my_style= window.parent.document.createElement('style');
            my_style.innerHTML=`
                footer{
                    display:none;
                }
                .stApp {
                    margin-top: -80px
                }
                .stApp header{
                    background-color: transparent;
                }
                
                .streamlit-expanderHeader p{
                    font-size: x-large;
                }
                .main .block-container{
                    max-width: unset;
                    padding-left:1em;
                    padding-right: 1em;
                    padding-top: 0em;
                    padding-bottom: 1em;
                `;
                window.parent.document.head.appendChild(my_style);       
        </script>
        '''
    components.html(hvar, height=0, width=0)

setUI()