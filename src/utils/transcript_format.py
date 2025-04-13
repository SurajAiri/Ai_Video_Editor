from src.models.invalid_model import InvalidModel
from typing import List

def format_deepgram_transcript_sent(transcript:dict):
    paras = transcript['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']

    res = ""
    for para in paras:
        for sent in para['sentences']:
            res += "{start:.02f} {end:.02f} {text}\n".format(
                start=sent['start'],
                end=sent['end'],
                text=sent['text']
            )
    return res

def format_deepgram_transcript_word(transcript:dict, invalids: List[InvalidModel]):
    words = transcript['results']['channels'][0]['alternatives'][0]['words']
    
    # new transcript with invalids word only where isEntire is false and  invalids startTime and endTime range


    res = ""
    for inv in invalids:
        # print("--+--"*10)
        for word in words:
            if inv.end_time < word['end']:
                break
            elif inv.start_time <= word['start'] and inv.end_time >= word['end']:
                res += "{start:.02f} {end:.02f} {text}\n".format(
                    start=word['start'],
                    end=word['end'],
                    text=word['word']
                )
        res += "\n"
    return res

# res = """{
#   "data": [
#     {
#       "start_time": "0.48",
#       "end_time": "7.12",
#       "type": "repetition",
#       "is_entire": true
#     },
#     {
#       "start_time": "35.56",
#       "end_time": "43.02",
#       "type": "repetition",
#       "is_entire": true
#     },
#     {
#       "start_time": "10.72",
#       "end_time": "15.60",
#       "type": "repetition",
#       "is_entire": false
#     }
#   ]
# }"""
# import json
# res = json.loads(res)
# print(res['data'])

# trans_path = "/Users/suraj/vscode/aiml/genai/ai_video_editor/notebooks/transcript2.json"
# with open(trans_path, 'r') as file:
#     transcript = json.load(file)

# invalids = [ InvalidModel.from_dict(item) for item in res['data'] ]
# # print(invalids)
# # sort invalids by start_time
# invalids.sort(key=lambda x: x.start_time)

# invalid_words = format_deepgram_transcript_word(transcript, invalids)
# print(invalid_words)