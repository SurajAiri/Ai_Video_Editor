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
    # print(prompt)

    # call the LLM
    response = completion(
        # api_key=os.getenv("GOOGLE_API_KEY"),
        # model="gemini/gemini-2.0-flash",  
        # model="gemini/gemini-2.5-pro-exp-03-25",  # Gemini Pro via LiteLLM
        model="gpt-4o",  # OpenAI GPT-4 model
        api_key=os.getenv("OPENAI_API_KEY"),  # OpenAI API key
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

trns = """0.48 7.12 You can undo you can undo multiple commands using revert as well, but you might get merge conflict.
7.76 10.40 We will know about merge conflict in a while.
10.72 15.60 As of now, I will give you a bonus if you are using Versus code and you look some changes over here.
16.66 24.27 And you want to undo the change, you can just, click on the file or, like, over here or, like, you have just seen over there.
25.06 26.98 Some this.
35.56 43.02 I will give you if you're using if you're using Versus code, then I have a bonus for you.
43.02 47.57 Like, if I deleted something, then it's so generic, and I can undo this.
47.57 54.70 If I have modified something, like, I it shows some how this blue lines, and I will, like, undo this as well.
54.97 61.05 If I have added nothing, it showed me in green and I can undo this as well.
61.13 62.33 So this is like working."""

res = llm_call_analyse_sent(trns)
print(res)