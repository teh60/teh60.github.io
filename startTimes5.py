import numpy as np
import json
from datetime import datetime as dt
from datetime import timedelta as td
from dateutil import tz
from PIL import Image
# import time
# import pandas as pd

from plotly.offline import plot
import chart_studio.plotly as py
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

quotheID=204035332545576970
dunkID=170658516116307968
dtStr="%Y-%m-%d %H:%M"
plStr="%A %I:%M %p"
# toTZ=tz.gettz("America/Los_Angeles")
toTZ=tz.gettz("US/Central")

def movingAvg(data,size):
    window=np.ones(size)/size
    return np.convolve(data,window,"same")

def isLiveMsg(title):
    if "no stream" in title.lower():
        return False
    if ("cosmetic" in title.lower()) and (("live" or "stream") not in title.lower()):
        return False
    return True

def isGenLive(genMsg):
    return "**He's live!** Today" in genMsg["content"] and genMsg["author"]["id"]==quotheID

# @profile
def formatMsgList(msgList):
    # tF1=time.time()
    for msg in msgList:
        # create datetime objects and shift from UTC to PST
        msg["timestamp"]=dt.fromisoformat(msg["timestamp"]).astimezone(toTZ)
        # convert strings to ints
        msg["author"]["id"]=int(msg["author"]["id"])
    # tF2=time.time()
    # print(f"(format time: {tF2-tF1}")
    return msgList

def timeMargin(alert,gen,window):
    tdWindow=td(hours=window)
    diff=alert["timestamp"]-gen["timestamp"]
    return diff if (tdWindow>diff and diff>td()) else False

def trainMargin(alert,gen):
    if alert["timestamp"].hour>21:
        start=alert["timestamp"].replace(hour=22,minute=0,second=0,microsecond=0)
    elif alert["timestamp"].hour<10:
        start=alert["timestamp"].replace(hour=22,minute=0,second=0,microsecond=0)-td(days=1)
    else:
        return False
    margin=gen["timestamp"]-start
    # print(margin)
    return margin>td() and margin<(alert["timestamp"]-start)

def isTrainMsg(msg):
    return (":dnkLate:" in msg["content"]) or (":dnkSus:" in msg["content"]) or (":dnkSip:" in msg["content"])

def avgs(xData):
    return [movingAvg(xData,31),[sum(xData)/len(xData) for elem in xData]]

# tStart=time.time()

with open("streamAlerts.json",encoding="utf-8") as jsonF:
    streamAlerts=json.load(jsonF)

with open("general.json",encoding="utf-8") as jsonF:
    general=json.load(jsonF)

# tJSON=time.time()

alerts=streamAlerts["messages"]
alerts=formatMsgList(alerts)
alerts=[alert for alert in alerts if isLiveMsg(alert["content"])]

genMsgs=general["messages"]

# t2D=time.time()

genMsgs=formatMsgList(genMsgs)

# t2Dnew=time.time()
# print((t2Dnew-t2D)/len(genMsgs))

dqMsgs=[msg for msg in genMsgs if (isGenLive(msg) or msg["author"]["id"]==dunkID)]
# print(*[(msg["timestamp"],msg["content"],msg["author"]["name"]) for msg in dqMsgs],sep="\n")

dq2=[]
for i in range(len(dqMsgs)):
    if dqMsgs[i]["author"]["id"]==quotheID and dqMsgs[i-1]["author"]["id"]==dunkID and timeMargin(dqMsgs[i],dqMsgs[i-1],2):
        dq2.append([timeMargin(dqMsgs[i],dqMsgs[i-1],2),dqMsgs[i],dqMsgs[i-1]])

# train2=[[0,alert] for alert in alerts]
emoteMsgs=[msg for msg in genMsgs if (isTrainMsg(msg) or isGenLive(msg))]
pQ=0
train2=[]
for i,msg in enumerate(emoteMsgs):
    if isGenLive(msg):
        train2.append([len([emote for emote in emoteMsgs[pQ:i-1] if trainMargin(msg,emote)]),msg])
        pQ=i

# get x and y data for dunk late from 8pm PST times
(late8,days)=zip(*[(alert["timestamp"],alert["timestamp"].strftime(dtStr)) for alert in alerts])
late8=[(date.hour+24+date.minute/60)-22 if date.hour<=6 else (date.hour+date.minute/60)-22 for date in late8]
# calculate dunk to 8pm PST times
(late8avg,late8line)=avgs(late8)
# late8avg=movingAvg(late8,31)
# late8line=[sum(late8)/len(late8) for elem in late8]
days1=(alerts[-1]["timestamp"]+td(days=1)).strftime(dtStr)

# get x and y data for quothe to Chase Times
(lateQ,daysQ)=zip(*[(dq[0].seconds/60,dq[1]["timestamp"].strftime(dtStr)) for dq in dq2])
# calculate quothe to Chase Times
(lateQavg,lateQline)=avgs(lateQ)
# lateQavg=movingAvg(lateQ,31)
# lateQline=[sum(lateQ)/len(lateQ) for elem in lateQ]

# convert date axis from PST to CST (chase time)
dayDunk=[alert["timestamp"].strftime(dtStr) for alert in alerts]
dayList=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
# pre allocate bar chart and cumsum scatter chart axes
dayCount=[0 for day in dayList]
dayCountH=[[0 for alert in alerts] for day in dayList]
# calculate # of streams per day of the week and which day each stream took place on
offAlerts=[]
for i,alert in enumerate(alerts):
    cDay=alert["timestamp"].isoweekday()
    dayCount[cDay-1]+=1
    dayCountH[cDay-1][i]+=1
    if cDay in (1,7):
        offAlerts.append((cDay-1,i,alert))
dayColor=px.colors.qualitative.G10[:7]
# cumulatively sum each day of the week's occurences to make nice plot
for i,week in enumerate(dayCountH):
    dayCountH[i]=np.cumsum(week)

(deltaX,deltaY)=zip(*[(tup[2]["timestamp"].strftime(dtStr),dayCountH[tup[0]][tup[1]]) for tup in offAlerts])

# hover text for first subplot
(time8,title8)=zip(*[(alert["timestamp"].strftime(plStr),alert["content"]) for alert in alerts])
# python mod different than C/java mod so fun yay
(late8h,late8m)=zip(*[(int(date),int((date-int(date))*60)) for date in late8])
# hover text for second subplot
(timeQ,titleQ)=zip(*[(dq[1]["timestamp"].strftime(plStr),dq[1]["content"]) for dq in dq2])
(dqMsg,dqMin)=zip(*[(dq[2]["content"],int(dq[0].seconds/60)) for dq in dq2])
# hover text for fourth subplot
(timeD,titleD)=zip(*[(tup[2]["timestamp"].strftime(plStr),tup[2]["content"]) for tup in offAlerts])

late8D=[tup[2]["timestamp"] for tup in offAlerts]
late8D=[(date.hour+24+date.minute/60)-22 if date.hour<=6 else (date.hour+date.minute/60)-22 for date in late8D]

(late8hD,late8mD)=zip(*[(int(date),int((date-int(date))*60)) for date in late8D])
cntD=[[dayCountH[i][tup[1]] for tup in offAlerts] for i in range(7)]

(trainX,trainY)=zip(*[(tup[1]["timestamp"].strftime(dtStr),tup[0]) for tup in train2])
(timeT,titleT)=zip(*[(tup[1]["timestamp"].strftime(plStr),tup[1]["content"]) for tup in train2])

(trainAvg,trainLine)=avgs(trainY)

print(len(alerts))
# tXY=time.time()
# subplot tiles
titleLate8="How Late Chase is from Start Time of 10 PM CST (UTC-6) aka Chase's Timezone"
titleLateQ="How Late Chase is After Sending the First Message in #general"
titleWeek="How Many Streams for each day of the Week"
titleWeekH="How Many Streams for each day of the Week vs. Time"
titleTrain="How Long Does the dnkLate/dnkSus/dnkSip Train get"
fig=make_subplots(
    rows=5,
    cols=1,
    subplot_titles=(
        f"<span style='color:#ffffff;'>{titleLate8}</span>",
        f"<span style='color:#ffffff;'>{titleLateQ}</span>",
        f"<span style='color:#ffffff;'>{titleWeek}</span>",
        f"<span style='color:#ffffff;'>{titleWeekH}</span>",
        f"<span style='color:#ffffff;'>{titleTrain}</span>",
        ),
    vertical_spacing=0.06,
    )
# row 1
# lateness
fig.add_trace(
    go.Scatter(
        x=days,
        y=late8,
        mode="markers+lines",
        line=dict(width=1.5,color="rgb(50,130,210)"),
        marker=dict(size=5),
        name="Lateness",
        legendgroup='1',
        customdata=np.stack((time8,title8,late8h,late8m),axis=-1),
        hovertemplate='<extra></extra><b>Date</b>: %{customdata[0]}<br><br>'+
                      '<b>Live Message</b>: %{customdata[1]}<br><br>'+
                      '<b>Lateness</b>: %{customdata[2]} hour(s) and %{customdata[3]} minute(s)<br>'
        ),
    row=1,
    col=1,
    )
# late moving avg
fig.add_trace(
    go.Scatter(
        x=days,
        y=late8avg,
        name="Lateness MA w = 31",
        legendgroup='1',
        line=dict(width=2,color="red"),
        hoverinfo='skip',
        ),
    row=1,
    col=1,
    )
# late avg line
fig.add_trace(
    go.Scatter(
        x=days,
        y=late8line,
        name=f"Lateness AVG = {int(late8line[0]*60)} min",
        legendgroup='1',
        line=dict(width=2,color="orange"),
        hoverinfo='skip',
        ),
    row=1,
    col=1,
    )

# row 2
# quothe late
fig.add_trace(
    go.Scatter(
        x=daysQ,
        y=lateQ,
        mode="markers+lines",
        line=dict(width=1.5,color="rgb(50,130,210)"),
        marker=dict(size=5),
        name="Quothe-Dunk",
        legendgroup='2',
        customdata=np.stack((timeQ,titleQ,dqMsg,dqMin),axis=-1),
        hovertemplate='<extra></extra><b>Date</b>: %{customdata[0]}<br><br>'+
                      '<b>Live Message</b>: %{customdata[1]}<br><br>'+
                      '<b>Dunk\'s Message</b>: %{customdata[2]}<br><br>'+
                      '<b>Delay</b>: %{customdata[3]} minute(s)<br>'
        ),
    row=2,
    col=1,
    )
# quothe late moving avg
fig.add_trace(
    go.Scatter(
        x=daysQ,
        y=lateQavg,
        line=dict(width=2,color="red"),
        name="Quothe-Dunk MA w = 31",
        legendgroup='2',
        hoverinfo='skip',
        ),
    row=2,
    col=1,
    )
# quothe late avg line
fig.add_trace(
    go.Scatter(
        x=daysQ,
        y=lateQline,
        line=dict(width=2,color="orange"),
        name=f"Quothe-Dunk AVG = {int(lateQline[0])} min",
        legendgroup='2',
        hoverinfo='skip',
        ),
    row=2,
    col=1,
    )

# row 3
# day of the week
fig.add_trace(
    go.Bar(
        # dataframe=dayDunk,
        x=dayList,
        y=dayCount,
        text=dayCount,
        textposition='auto',
        textfont=dict(color="white"),
        marker_color=dayColor,
        opacity=0.5,
        # name="count",
        legendgroup='3',
        # showlegend=False,
        hoverinfo="skip"
        ),
    row=3,
    col=1,
    )
# row 4
# day of the week vs time

print('wtf guys')

fig.add_trace(
    go.Scatter(
        x=deltaX,
        y=deltaY,
        mode="markers",
        marker=dict(color="white",size=10),
        name="Hover",
        opacity=0.75,
        # legendgroup='3',
        showlegend=False,
        customdata=np.stack((timeD,titleD,cntD[0],cntD[1],cntD[2],cntD[3],cntD[4],cntD[5],cntD[6],late8hD,late8mD),axis=-1),
        hovertemplate='<extra></extra><b>Date</b>: %{customdata[0]}<br>'+
                      '<b>Live Message</b>: %{customdata[1]}<br>'+
                      '<b>Lateness</b>: %{customdata[9]} hour(s) and %{customdata[10]} minute(s)<br><br>'
                      'Monday: %{customdata[2]}<br>'+
                      'Tuesday: %{customdata[3]}<br>'+
                      'Wednesday: %{customdata[4]}<br>'+
                      'Thursday: %{customdata[5]}<br>'+
                      'Friday: %{customdata[6]}<br>'+
                      'Saturday: %{customdata[7]}<br>'+
                      'Sunday: %{customdata[8]}<br>',
    ),
    row=4,
    col=1,
)
for i,day in enumerate(dayList):
    fig.add_trace(
        go.Scatter(
            x=dayDunk,
            y=dayCountH[i],
            line=dict(width=2,color=dayColor[i]),
            name=day,
            legendgroup='4',
            hoverinfo='skip',
        ),
        row=4,
        col=1,
        )
# row 5
# train info
fig.add_trace(
    go.Scatter(
        x=trainX,
        y=trainY,
        mode="markers+lines",
        line=dict(width=1.5,color="rgb(50,130,210)"),
        marker=dict(size=5),
        name="Train Length",
        legendgroup='5',
        showlegend=False,
        # showlegend=False,
        customdata=np.stack((timeT,titleT),axis=-1),
        hovertemplate='<extra></extra><b>Train Length: </b>%{y}<br><br>'+
                      '<b>Date</b>: %{customdata[0]}<br><br>'+
                      '<b>Live Message</b>: %{customdata[1]}<br><br>'
        ),
    row=5,
    col=1,
    )
# train moving avg
fig.add_trace(
    go.Scatter(
        x=trainX,
        y=trainAvg,
        name="Train MA w = 31",
        legendgroup='5',
        showlegend=False,
        line=dict(width=2,color="red"),
        hoverinfo='skip',
        ),
    row=5,
    col=1,
    )
# train avg line
fig.add_trace(
    go.Scatter(
        x=trainX,
        y=trainLine,
        name=f"Train AVG = {trainLine[0]:.2f}",
        legendgroup='5',
        showlegend=False,
        line=dict(width=2,color="orange"),
        hoverinfo='skip',
        ),
    row=5,
    col=1,
    )
fig.add_layout_image(
    dict(
        source="https://cdn.discordapp.com/emojis/909929040406798528.webp?size=96&quality=lossless",
        xref='paper',
        yref='paper',
        x=-0.01,
        y=1.04,
        sizex=0.1,
        sizey=0.1,
        xanchor="left",
        yanchor="bottom",
        )
    )
fig.add_layout_image(
    dict(
        source="https://cdn.discordapp.com/emojis/909929040331300904.webp?size=96&quality=lossless",
        xref='paper',
        yref='paper',
        x=0.948,
        y=1.04,
        sizex=0.1,
        sizey=0.1,
        xanchor="left",
        yanchor="bottom",
        )
    )
JEB=Image.open("jebated.png")
ABBC=Image.open("ABBC.webp")
GIGA=Image.open("GIGACHAD.webp")

imgJEB=dict(source=JEB,
        xref='x5 domain',
        yref='y5 domain',
        x=-0.08,
        y=0,
        sizex=1,
        sizey=1,
        xanchor="left",
        yanchor="bottom",)
imgABBC=dict(source=ABBC,
        xref='x5 domain',
        yref='y5 domain',
        x=0.27,
        y=0,
        sizex=1,
        sizey=1,
        xanchor="left",
        yanchor="bottom",)
imgGIGA=dict(source=GIGA,
        xref='x5 domain',
        yref='y5 domain',
        x=0.98,
        y=0,
        sizex=1,
        sizey=1,
        xanchor="left",
        yanchor="bottom",)
print('is it this')
fig.update_layout(
    title="<b>            dnkLate or: How I Learned to Stop Worrying and Love 11 PM CST Stream Start</b>",
    title_font_color="white",
    title_font_size=30,
    margin_t=300,
    plot_bgcolor="rgb(40,40,40)",
    paper_bgcolor="rgb(40,40,40)",
    showlegend=True,
    legend_font_color="white",
    hovermode="x unified",
    hoverlabel=dict(font_size=16),
    legend_tracegroupgap=710,
    width=1890,
    height=4000,
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=1,
            y=1.012,
            active=-1,
            font=dict(color="red"),
            buttons=list([
                dict(
                    label="2 hours early - 4 hours late",
                    method="relayout",
                    args=[{"yaxis.range":[-2,4]}],
                    ),
                dict(
                    label="Late Only",
                    method="relayout",
                    args=[{"yaxis.range":[0,max(late8)]}],
                    ),
                dict(
                    label="Early Only",
                    method="relayout",
                    args=[{"yaxis.range":[min(late8),0]}],
                    ),
                dict(
                    label="All",
                    method="relayout",
                    args=[{"yaxis.range":[min(late8),max(late8)]}],
                    ),
                ])
            ),
        dict(
            type="buttons",
            direction="right",
            x=0.24,
            y=0.17,
            active=-1,
            font=dict(color="red"),
            buttons=list([
                dict(
                    label="Preview of TI Bet Post",
                    method="relayout",
                    args=(["images", [imgJEB,imgABBC,imgGIGA]]),
                    args2=(["images",[]]),
                    ),
                ])
            ),
    ]
    )
# row 1
fig.update_xaxes(
    row=1,
    col=1,
    range=[days[0],days1],
    tickangle=30,
    nticks=30,
    title="Date",
    color="white",
    gridcolor="rgb(60,60,60)",
    )
fig.update_yaxes(
    row=1,
    col=1,
    range=[-2,4],
    tickmode="linear",
    tick0=0,
    dtick=1,
    title="Hours",
    color="white",
    gridcolor="rgb(60,60,60)",
    )
# row 2
fig.update_xaxes(
    row=2,
    col=1,
    range=[daysQ[0],daysQ[-1]],
    tickangle=30,
    nticks=30,
    # tick0="2000-01-01",
    # dtick="M1",
    title="Date",
    color="white",
    gridcolor="rgb(60,60,60)",)
fig.update_yaxes(
    row=2,
    col=1,
    range=[0,100],
    tickmode="linear",
    tick0=0,
    dtick=10,
    title="Minutes",
    color="white",
    gridcolor="rgb(60,60,60)",
    )
# row 3
fig.update_xaxes(
    row=3,
    col=1,
    title="Day of the Week",
    title_standoff=0,
    automargin="width",
    color="white",
    gridcolor="rgb(60,60,60)",
    )
fig.update_yaxes(
    row=3,
    col=1,
    title="Count",
    color="white",
    gridcolor="rgb(60,60,60)",
    )
# row 4
fig.update_xaxes(
    row=4,
    col=1,
    range=[dayDunk[0],dayDunk[-1]],
    tickangle=30,
    nticks=30,
    title="Date",
    color="white",
    gridcolor="rgb(60,60,60)",
    )
fig.update_yaxes(
    row=4,
    col=1,
    title="Count",
    color="white",
    gridcolor="rgb(60,60,60)",
    )
# row 5
fig.update_xaxes(
    row=5,
    col=1,
    range=[trainX[0],trainX[-1]],
    # fixedrange=True,
    tickangle=30,
    nticks=30,
    title="Date",
    color="white",
    gridcolor="rgb(60,60,60)",
    )
fig.update_yaxes(
    row=5,
    col=1,
    # fixedrange=True,
    # title="Count",
    color="white",
    gridcolor="rgb(60,60,60)",
    )

print('how bout this')

# add descriptive text between plots
titlePara=("After seeing @nolava create the two amazing TI bet blogposts I was inspired to make my own but while working on that, I got sidetracked and ended up making this page of data, statistics,<br>"
"and graphs all focused/themed around Chase's stream start times and dates instead. (TI/Bet analysis post maybe coming Soon&#8482;, idk as I coded this I realized I am pretty rusty at coding so we shall see)<br><br>"
"<i>First Note:</i> (there are more)  All the graphs are zoom and pan friendly, in the very top right there is a static toolbar (sorry, didn't get around to finding how to fix that in plotly, sidenote this was coded in python3)<br>"
"Also, you can double click a graph to reset it to my default bounds.  Finally, all except the third and somewhat fourth figure have tooltips on data points/lines")
fig.add_annotation(
    x=0,
    y=1.26,
    xref='x domain',
    yref='y domain',
    # yshift=-20,
    text=titlePara,
    align="left",
    font_color="white",
    font_size=16,
    showarrow=False,)

titleR1=("So, for all of you asking \"What time does the stream start?\" and growing the dnkLate train in Discord (including me), the simple answer is 11 PM CST, or on average 52 minutes late so 10:52 PM CST.<br>"
"Remember how sometimes Chase says start time is 9-10 PM CST?  Yeah 9 PM would make him an hour later...<br><br>"
"<i>Note:</i>  MA = moving average, w=31 means window of 31 (days), so averages the blue lateness line @ each point with &#177;15 other days' lateness.<br>"
"<i>Bonus Note:</i>  If you hit All or Early Only to view those extremely negative dates, and mouse over them (you can mouse over them in default but its harder), you'll see the rare morning Chase stream.")
fig.add_annotation(
    x=0,
    y=-0.34,
    xref='x domain',
    yref='y domain',
    # yshift=-20,
    text=titleR1,
    align="left",
    font_color="white",
    font_size=16,
    showarrow=False,)
titleR2=("Thanks to @Ta(l/I)anvor, for the suggestion to graph how long it takes Chase to start stream from his post in #general on !discord.<br><br>"
"<i>Note:</i>  Chase doesn't always give us a message before going live, and I only check for going-live messages/Chase's messages in #general, making this dataset much smaller.")
fig.add_annotation(
    x=0,
    y=-0.27,
    xref='x2 domain',
    yref='y2 domain',
    # yshift=-20,
    text=titleR2,
    align="left",
    font_color="white",
    font_size=16,
    showarrow=False,)
titleR3=("So, I have only been part of the twitch community for a year or so, but even in that period of time people, and Chase himself, have said that Monday is a valid stream day, but I wanted to check.<br>"
"Then I realized, I want to see when these Monday streams stopped occuring, and for that matter sunday streams sometimes happen, and it would be nice to see when those have taken place.<br>"
"Aaaaaaand Monday Streams died on February 21<sup>st</sup>, 2022.  Make no mistake, that other Monday stream was not a regular Monday stream, it was the surprise Noita Beta Branch stream courtesy of Petri<br><br>"
"<i>Note:</i>  I disabled tooltip hovering on the main Tuesday-Saturday data points to make viewing the Monday/Sunday stream info easier.<br>"
"<i>Bonus Note:</i>  Some of the Sunday streams are late-starting Saturday streams as I didn't both filtering for that like I did on earlier graphs")
fig.add_annotation(
    x=0,
    y=-0.32,
    xref='x3 domain',
    yref='y3 domain',
    # yshift=-20,
    text=titleR3,
    align="left",
    font_color="white",
    font_size=16,
    showarrow=False,)
titleR4=("And last but certainly not least, we have the infamous discord emote train that starts at \"On Time\" 10 PM and ends when Quothe (Sorry Xurxo, I didn't code it to look for your message) says the stream is live.<br>"
"Just like the first 2 graphs, I also calculated the moving average and that the train averages 4.73 messages containing dnkLate, dnkSus, or dnkSip.<br><br>"
"<i>Note:</i>  Maybe my filtering was weird, but it appears the emote train wasn't a thing until November 22<sup>nd</sup>, 2021, about a month and a half after Quothe started posting live notifications in #general<br>"
"<i>Final Bonus Note:</i>")
fig.add_annotation(
    x=0,
    y=-0.32,
    xref='x4 domain',
    yref='y4 domain',
    # yshift=-20,
    text=titleR4,
    align="left",
    font_color="white",
    font_size=16,
    showarrow=False,)

print('is it just the chart studio upload')
plotFile=plot(fig,auto_open=False)
# plotURL=py.plot(fig,filename='dnkLate or: How I Learned to Stop Worrying and Love 11 PM CST Stream Start',auto_open=False,validate=False)
# print(plotURL)
