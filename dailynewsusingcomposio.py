import streamlit as st
from openai import OpenAI
import os
import asyncio

from composio import Composio
from composio_openai import OpenAIResponsesProvider
from agents import Agent, Runner, WebSearqchTool

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

async def News_Tool():
  agent = Agent[Any](
      name="Assistant",
      tools=[WebSearchTool()],
      instructions=(
          "You are a helpful assistant who collects news from the internet "
          "from reliable sources and summerizes them."
      ),
  )
  result1 = await Runner.run(
      agent,
      (
          "What it the latest news about AI? Give a brief summary in 100 words "
          "for each news. Only give me news in the last 72 hours. Always quote "
          "the source and date of the news"
      ),
  )
  return result1.final_output

def Email_tool(news, email):

  # Initialise Composio SDK with OpenAI provider
  composio = Composio[Any](
      api_key=st.secrets["COMPOSIO_API_KEY"],
      provider=OpenAIResponsesProvider(),
  )

  st.write("no problems with composio api key or provider")

  try:
    openai_client = OpenAI()

    tolls = composio.tools.get(
        user_id='me',
        tools=["GMAIL_SEND_EMAIL"],
    )

    subject = "Daily AI News by Anant's Agent"
    body = news
    task = (
        f"Send an email {email} with the bubject '{subject} and the body "
        f"containing the following news: {body}"
    )
    st.write("no problem with the request params")

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant that sends emails using the "
                    "available tools. Always call the Gmail tool to send "
                    "the email instead of jus drafting it."
                ),
            }
            {"role": "user", "content": task},
        ],
    )

    result = composio.provider.handle_tool_calls(
        user_id=user_id,
        response=response,
    )

    return result
  except Exception as e:
    st.error(f"Failed to send email: {e}")
    return None

st.header(":blue[Daily AI News]")

if "news" not in st.session_state:
  st.session_state["news"] = ""

if st.button("What's the recent news about AI?", type="primary"):
  with st.spinner("Fetching news..."):
    news = asyncio.run(News_Tool())
    st.session_state["news"] = news
    st.success("News fetched")
    st.text_area("Latest AI News", st.session_state["news"], height=300)

if st.session_state["news"]:
  st.write(
      "Give your email address to send this news to your inbox. "
      "This will be a one-time email and not a recurring one. "
      "We do not store your email address!"
  )
  email = st.text_input("Enter your email")
  if st.button("Send this email vial GMail", type="primary"):
      if email:
        with st.spinner("Sending email..."):
          try:
            result = Email_tool(st.session_state["news"], email)
            if result:
              st.success("Email sent")
            else:
              st.error("Failed to send email")
          except Exception as e:
            st.error(f"Failed to send email: {e}")
    else:
      st.warning("Please fetch the news first")
