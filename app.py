import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
import time

# Read .env file
load_dotenv()

# Create OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit title
st.title("Sentiment Analysis Tool")

st.write(
    """
    This application works in two ways:
    - You can analyze by entering a single sentence.
    - You can analyze entire rows by uploading an Excel file.
    """
)

# Create tabs
tab1, tab2 = st.tabs(['Single Sentence Analysis', 'Excel File Sentiment Analysis'])

# -------------------------------
# Tab 1: Single Sentence Analysis
# -------------------------------

with tab1:
    dil_secimi = st.selectbox(
        "Select a language",
        ["English", "Türkçe"]
    )

    if dil_secimi == "Türkçe":
        user_input = st.text_area("Please enter the text you want to analyze:")

    elif dil_secimi == "English":
        user_input = st.text_area("Please enter the text you want to analyze:")


    if st.button("Analyze", key="single_analysis_button"):
        if not user_input.strip():
            st.warning("Please enter a text.")

        else:
            # Prompt
            if dil_secimi == "Türkçe":
                prompt_instruction  = (
                    "Determine the sentiment of the following text and give your confidence score.\n"
                    "Answer only in the following format:\n"
                    "Sentiment: (Positive/Negative/Neutral)\n"
                    "Score: (Integer from 0-100)\n\n"
                    f"Text: {user_input}\n\n"
                    "Answer:"
                )

                cevap_basligi = "Answer:"
                sentiment_prefix = "Sentiment:"
                score_prefix = "Score:"

            elif dil_secimi == "English":
                prompt_instruction  = (
                    "Determine the sentiment of the following text and give your confidence score.\n"
                    "Answer only in the following format:\n"
                    "Sentiment: (Positive/Negative/Neutral)\n"
                    "Score: (Integer from 0-100)\n\n"
                    f"Text: {user_input}\n\n\n"
                    "Answer:"
                )

                cevap_basligi = "Answer:"
                sentiment_prefix = "Sentiment:"
                score_prefix = "Score:"


            # Combine prompt
            prompt_text = (
                f"{prompt_instruction}\n\n"
                f"Text: {user_input}\n\n"
                f"{cevap_basligi}"
            )

            try:
                # OpenAI Chat Completion request
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional sentiment analysis expert."},
                        {"role": "user", "content": prompt_text}
                    ],
                    temperature=0
                )

                # Get model response
                response_text = completion.choices[0].message.content.strip()
            

                # Parse output
                lines = response_text.split("\n")
                sentiment_line = next(line for line in lines if line.startswith("Sentiment:"))
                score_line = next(line for line in lines if line.startswith("Score:"))

                sentiment = sentiment_line.replace("Sentiment:", "").strip()
                score = score_line.replace("Score:", "").strip()

                # Display result
                st.success(f"Sentiment: {sentiment}")
                st.info(f"Confidence Score: {score}/100")


            except Exception as e:
                st.error(f"Failed to parse response. Response: {response_text}") 


# -------------------------------
# Tab 2: Excel Batch Analysis
# -------------------------------
with tab2:
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        st.write("Uploaded File:")
        st.dataframe(df.head())

        column_name = st.selectbox(
            "Select the column you want to analyze",
            df.columns
        )

        if st.button("Analyze all rows"):
            texts = df[column_name].fillna("").astype(str).tolist()
            sentiments = []
            scores = []

            progress_bar = st.progress(0)
            status_text = st.empty()


            for idx, text in enumerate(texts):
                prompt_text = (
                    "Determine the sentiment of the following text and give your confidence score.\n"
                    "Answer only in the following format:\n"
                    "Sentiment: (Positive/Negative/Neutral)\n"
                    "Score: (Integer from 0-100)\n\n"
                    f"Text: {user_input}\n\n\n"
                    "Answer:"                   
                )


                try:
                    # OpenAI Chat Completion request
                    completion = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a professional sentiment analysis expert."},
                            {"role": "user", "content": prompt_text}
                        ],
                        temperature=0
                    )

                    # Get model response
                    response_text = completion.choices[0].message.content.strip()
                

                    # Parse output
                    lines = response_text.split("\n")
                    sentiment_line = next(line for line in lines if line.startswith("Sentiment:"))
                    score_line = next(line for line in lines if line.startswith("Score:"))

                    sentiment = sentiment_line.replace("Sentiment:", "").strip()
                    score = score_line.replace("Score:", "").strip()


                except Exception as e:
                    sentiment = "Error"
                    score = "Error"
                    st.error(f"Error occurred on line {idx+1}: {e}")


                sentiments.append(sentiment)
                scores.append(score)


                progress_bar.progress((idx + 1) / len(texts))
                status_text.text(f"{idx + 1} / {len(texts)} analyzed.")

                time.sleep(0.2)

            df['Sentiment'] = sentiments
            df['Score'] = scores

            st.success("Analysis completed.")
            st.dataframe(df)


            # Create byte stream for download_button
            from io import BytesIO
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                label="Download results as Excel",
                data=buffer,
                file_name="sentiment_analysis_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
