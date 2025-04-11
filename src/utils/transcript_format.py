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

