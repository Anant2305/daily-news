import os
import asyncio
from typing import Any

import streamlit as st
from openai import OpenAI
from composio import Composio
from composio_openai import OpenAIResponsesProvider
from agents import Agent, Runner, WebSearchTool

if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "COMPOSIO_API_KEY" not in os.environ:
    os.environ["COMPOSIO_API_KEY"] = st.secrets["COMPOSIO_API_KEY"]


async def News_Tool():
    agent = Agent[Any](
        name="Assistant",
        tools=[WebSearchTool()],
        instructions=(
            "You are a helpful assistant who collects news from the internet "
            "from reliable sources and summarizes them."
        ),
    )
    result = await Runner.run(
        agent,
        (
            "What are the latest news about AI? Give a brief summary in 100 words "
            "for each news item. Only give me news from the last 72 hours. Always "
            "quote the source and date of each news item."
        ),
    )
    return result.final_output


def Email_tool(news, email):
    user_id = "me"

    try:
        composio = Composio(
            api_key=os.environ["COMPOSIO_API_KEY"],
            provider=OpenAIResponsesProvider(),
        )

        openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        tools = composio.tools.get(
            user_id=user_id,
            tools=["GMAIL_SEND_EMAIL"],
        )

        subject = "Daily AI News by Anant's Agent"
        task = (
            f"Send an email to {email} with the subject '{subject}' and the body "
            f"containing the following news: {news}"
        )

        response = openai_client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that sends emails using the available "
                        "tools. Always call the Gmail tool to send the email instead "
                        "of just drafting it."
                    ),
                },
                {"role": "user", "content": task},
            ],
            tools=tools,
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
    if st.button("Send this email via Gmail", type="primary"):
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
            st.warning("Please enter an email address")
