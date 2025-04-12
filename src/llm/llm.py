import os
from litellm import completion
from prompt import generate_sent_analysis_prompt
from dotenv import load_dotenv

load_dotenv()

def llm_call_analyse_sent(transcript:str):
    """
    Call the LLM to analyze the transcript
    """

    # generate the prompt
    prompt = generate_sent_analysis_prompt(transcript)
    
    # call the LLM
    response = completion(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini/gemini-1.5-flash",  # Gemini Pro via LiteLLM
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # print(response["choices"][0]["message"]["content"])
    return response["choices"][0]["message"]["content"]


# Example usage

trns = """0.96 2.16 Hello, everyone.
2.80 3.68 Hello, everyone.
3.68 5.44 Welcome back to our channel.
6.40 7.44 I'm Suraj.
7.44 10.72 Today, I'm here to try some new project.
11.20 17.93 Today, I'm here to try some new project That is an AI based video editor application.
18.86 22.06 This will edit the application sorry.
22.78 29.10 This will this will edit the video based on the transcript of the video."""

res = llm_call_analyse_sent(trns)
print(res)