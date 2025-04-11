import os
import json

PATH = "transcript2.json"

# load json
def load_json(path: str):
    """
    Load json file
    """
    with open(path, 'r') as f:
        data = json.load(f)
    return data

# deepgram format
trns = load_json(PATH)
paras = trns['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']

for para in paras:
    for sent in para['sentences']:
        print("{start:.02f} {end:.02f} {text}".format(
            start=sent['start'],
            end=sent['end'],
            text=sent['text']
        ))

# after first analysis
resp = {
  "data": [
    {
      "startTime": "0.48",
      "endTime": "7.12",
      "type": "repetition",
      "isEntire": True
    },
    {
      "startTime": "10.72",
      "endTime": "15.60",
      "type": "repetition",
      "isEntire": True
    },
    {
      "startTime": "16.66",
      "endTime": "24.27",
      "type": "filler_word",
      "isEntire": False
    },
    {
      "startTime": "35.56",
      "endTime": "43.02",
      "type": "repetition",
      "isEntire": True
    },
    {
      "startTime": "43.02",
      "endTime": "47.57",
      "type": "filler_word",
      "isEntire": False
    },
    {
      "startTime": "47.57",
      "endTime": "54.70",
      "type": "filler_word",
      "isEntire": False
    },
    {
      "startTime": "61.13",
      "endTime": "62.33",
      "type": "filler_word",
      "isEntire": False
    }
  ]
}['data']




# words
words = trns['results']['channels'][0]['alternatives'][0]['words']
# for word in words:
#     print("{start:.02f} {end:.02f} {text}".format(
#         start=word['start'],
#         end=word['end'],
#         text=word['word']
#     ))
    

# only printing words within range of invalid and isEntire being False
for word in words:
    for r in resp:
        if r['isEntire'] == False and float(r['startTime']) <= word['start'] <= float(r['endTime']):
            print("{start:.02f} {end:.02f} {text}".format(
                start=word['start'],
                end=word['end'],
                text=word['word']
            ))


total_words = len(words)
print("Total words:", total_words)
