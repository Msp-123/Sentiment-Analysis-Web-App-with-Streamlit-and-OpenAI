import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
import time

# .env dosyasını oku
load_dotenv()

# OpenAI istemcisi oluştur
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Streamlit başlığı
st.title("Sentiment Analysis Tool")

st.write(
    """
    This application works in two ways:
    - You can analyze by entering a single sentence.
    - You can analyze entire rows by uploading an Excel file.
    """
)

# Sekmeler oluştur
tab1, tab2 = st.tabs(['Single Sentence Analysis', 'Excel File Sentiment Analysis'])

# -------------------------------
# Tab 1: Tek Cümle Analizi
# -------------------------------

with tab1:
    dil_secimi = st.selectbox(
        "Select a language",
        ["English" ,"Türkçe" ]
    )

    if dil_secimi == "Türkçe":
        user_input = st.text_area("Lütfen analiz etmek istediğiniz metni girin:")

    elif dil_secimi == "English":
        user_input = st.text_area("Please enter the text you want to analyze:")


    if st.button("Analysis", key="single_analysis_button"):
        if not user_input.strip():
            st.warning("Please enter a text.")

        else:
            #Prompt
            if dil_secimi == "Türkçe":
                prompt_instruction  = (
                    "Aşağıdaki metnin duygusunu belirle ve güven skorunu ver.\n"
                    "Yalnızca şu formatta cevap ver:\n"
                    "Duygu: (Olumlu/Olumsuz/Nötr)\n"
                    "Skor: (0-100 arası tam sayı)\n\n"
                    f"Metin: {user_input}\n\n"
                    "Cevap:"
                )

                cevap_basligi = "Cevap:"
                sentiment_prefix = "Duygu:"
                score_prefix = "Skor:"

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


            # Prompt birleştirme
            prompt_text = (
                f"{prompt_instruction}\n\n"
                f"Text: {user_input}\n\n"
                f"{cevap_basligi}"
            )

            try:
            # OpenAI Chat Completion isteği

                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional sentiment analysis expert."}, # Modelin kimliği, rolü ve davranış biçimini tanımlı
                        {"role": "user", "content": prompt_text} # Kullanıcının mesajıdır.
                    ],
                    temperature=0 # Bu parametre cevabın rastgeleliğini / yaratıcılığını kontrol eder. 
                )

                # Model cevabını al
                response_text = completion.choices[0].message.content.strip()
            

                # Çıktıyı parçala
                lines = response_text.split("\n")
                sentiment_line = next(line for line in lines if line.startswith("Duygu:"))
                score_line = next(line for line in lines if line.startswith("Skor:"))

                sentiment = sentiment_line.replace("Duygu:", "").strip()
                score = score_line.replace("Skor:", "").strip()

                # Sonucu göster
                if dil_secimi == "Türkçe":
                    st.success(f"Duygu: {sentiment}")
                    st.info(f"Güven Skoru: {score}/100")
                else:
                    st.success(f"Sentiment: {sentiment}")
                    st.info(f"Confidence Score: {score}/100")


            except Exception as e:
                st.error(f"Failed to parse response. Response: {response_text}") 


# -------------------------------
# Tab 2: Excel Toplu Analiz
# -------------------------------
with tab2:
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)

        st.write("Uploaded File:")
        st.dataframe(df.head())

        column_name = st.selectbox(
            "Select the column you want to do sentiment analysis",
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
                # OpenAI Chat Completion isteği
                    completion = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content":"Sen profesyonel bir duygu analiz uzmanısın."}, # Modelin kimliği, rolü ve davranış biçimini tanımlı
                            {"role": "user", "content": prompt_text} # Kullanıcının mesajıdır.
                        ],
                        temperature=0 # Bu parametre cevabın rastgeleliğini / yaratıcılığını kontrol eder. 
                    )

                    # Model cevabını al
                    response_text = completion.choices[0].message.content.strip()
                

                    # Çıktıyı parçala
                    lines = response_text.split("\n")
                    sentiment_line = next(line for line in lines if line.startswith("Sentiment:"))
                    score_line = next(line for line in lines if line.startswith("Score:"))

                    sentiment = sentiment_line.replace("Sentiment:", "").strip()
                    score = score_line.replace("Score:", "").strip()

                    # Sonucu göster
                    #st.success(f"Emotion: {sentiment}")
                    #st.info(f"Confidence Score: {score}/100")


                except Exception as e:
                    sentiment = "Error"
                    score = "Error"
                    st.error(f"Error occurred on line {idx+1}: {e}")


                sentiments.append(sentiment)
                scores.append(score)


                progress_bar.progress((idx + 1) / len(texts))
                status_text.text(f"{idx + 1} / {len(texts)} was analyzed.")

                time.sleep(0.2)

            df['Sentiment'] = sentiments
            df['Score'] = scores

            st.success("Analysis completed.")
            st.dataframe(df)


            # Data download_button için byte stream gerekiyor
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
            
