import os
import datetime as datetime
from time import sleep
import yfinance as yf
import openai
import pandas as pd
from causalimpact import CausalImpact
import streamlit as st
import matplotlib



matplotlib.use('Agg')

st.set_option('deprecation.showPyplotGlobalUse', False)
pd.set_option('display.max_colwidth', None)
header = st.container()
introduction = st.container()
openai.api_key = st.secrets["OPENAI_API_KEY"]





def create_tweets_string_for_sentiment(list_of_tweets):
    str = 'Classify the sentiment in these tweets:\n\n'
    for idx, tweet in enumerate(list_of_tweets):
        str += f"{idx + 1}. \"{tweet}\"\n"
    return str

@st.cache
def gpt_3_request(str):
    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=str,
        temperature=0,
        max_tokens=1500,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    return response["choices"][0]["text"].replace(",", "\n")

@st.cache
def fetch_financial_data(currency, when):
    date_time = datetime.datetime.strptime(when, '%Y-%m-%d').date()
    start_date = date_time - datetime.timedelta(days=30)
    end_date = date_time + datetime.timedelta(days=30)

    financial_data = yf.download(tickers=f"{currency}-USD", start=start_date.strftime("%Y-%m-%d"),
                                 end=end_date.strftime("%Y-%m-%d"), interval="1d")
    financial_data = financial_data.reset_index()
    financial_data["Date"] = financial_data["Date"].dt.date
    financial_data["Date"] = financial_data["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))
    financial_data = financial_data.set_index("Date")
    return financial_data, date_time, start_date, end_date


def run_analysis(tweet, financial_data, effect_day, start_date, end_date):
    with header:
        st.title("abc")

        import datetime

        # st.write(tweet)
        string_to_gpt_3 = create_tweets_string_for_sentiment([tweet])
        st.markdown(f" ## {string_to_gpt_3}")
        sentiment = None
        if "positive" in gpt_3_request(string_to_gpt_3).lower():
            sentiment = "positive"
        elif "negative" in gpt_3_request(string_to_gpt_3).lower():
            sentiment = "negative"
        else:
            sentiment = "neutral"

        st.markdown(f"### The sentiment is {sentiment} \n"
                    f" #### If the sentiment is Positive we expect uplift if "
                    f"negative pulldown and if neutral no effect or minimal effect")
        #
        # string_date = df[df['tweet'] == tweet].date.iloc[0].split(" ")[0].split("-")
        # tweet_time = datetime.datetime(int(string_date[0]), int(string_date[1]), int(string_date[2]))
        st.write("## We Found following financial data from yahoo finance")
        st.write(financial_data.head(10))
        causal_df = pd.DataFrame(
            {'y': financial_data["Close"], 'X1': financial_data["Volume"]}, columns=['y', 'X1'])

        day_after_effect_day = effect_day + datetime.timedelta(days=1)
        start_date = start_date + datetime.timedelta(days=3)
        end_date = end_date - datetime.timedelta(days=3)
        pre_period = [start_date.strftime("%Y-%m-%d"), effect_day.strftime("%Y-%m-%d")]
        post_period = [day_after_effect_day.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]

        ci = CausalImpact(causal_df, pre_period, post_period)

        st.markdown(f" ## {ci.summary('report')}")
        st.pyplot(ci.plot())
        sleep(10)
with introduction:
    st.title("How your twitter idol is affecting crypto/currencies")

    st.markdown("Goal of the app is to help people that are interested in targeting people that are influencing "
                "currency or crypto prices via Twitter. Event driven day trading is a popular"
                "method for day traders. Articles,events as well as twitter posts can be translated"
                "into accurate signals. By using GPT-3 we are able to determine the sentiment of the"
                "tweets which can tell us if positive tweets regarding certain currency are influencing the "
                "price. In order to know if the event had effect we need time series to predict what would"
                "have happened if such event had no place. That is why I trained Bayesian Structural Time Series"
                "model that can deliver just that. With Prediction (Shown as --- line) and what happened in reality (shown as y)"
                "We can simulate statistical test or A/B test and know the magnitude of the effect as well as probability/uncertainty "
                "of the effect."
                ""
                "Please feel free to play around with different tweets"
                "Note all currencies are compared again US dollar so the metric used is your_currency/USD")
tweet = st.sidebar.text_input("Please provide content of the tweet", "One word: Doge")
date = st.sidebar.text_input("When provide a date when the tweet happened (e.g. 2022-01-02)", "2020-12-20")
currency = st.sidebar.text_input("What currency you want to compare to USD (e.g. DOGE, PLN, BTC)", "DOGE")

state = st.sidebar.button("Let's analyze this tweet !")

if state:
    # st.write(f"### We are going to analyze \"{tweet}\" tweet")
    try:
        financial_data, effect_day, start_date, end_date = fetch_financial_data(currency, date)
        run_analysis(tweet, financial_data, effect_day, start_date, end_date)
        user_input = None
        submitted = False
    except:
        st.write("# Something went wrong please try to read input instructions again")
