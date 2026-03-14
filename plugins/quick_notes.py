def on_transcript(transcript: str):
    t = transcript.casefold().strip()
    if not t.startswith("not al "):
        return None
    note = t.replace("not al ", "", 1).strip()
    if not note:
        return None
    # Bu plugin, notu panoya kopyalamak gibi bir aksiyon yerine ornek olarak screenshot aldirir.
    # Gelistirirken burada dosyaya yazma, API cagrisi veya farkli bir action dondurebilirsiniz.
    return {"action": "ekran_goruntusu", "target": "", "value": 0}
