"""Independent local ASR of the selected excerpt; never uses the source transcript as a prompt."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.codex-tools/jijing-asr'))
from faster_whisper import WhisperModel
source=ROOT/'downloads/jijing-20260920/ieltsa/assets/494b5ff8b614-2026-sep-hf-1.mp3'
out=ROOT/'content-pipeline/batches/jijing-20260920/content-review/audio-independent-asr.json'
sys.stdout.reconfigure(encoding='utf-8')
print('Loading public tiny.en model for local, unprompted transcription',flush=True)
model=WhisperModel('tiny.en',device='cpu',compute_type='int8',cpu_threads=4,download_root=str(ROOT/'.codex-tools/jijing-asr-models'))
segments,info=model.transcribe(str(source),language='en',beam_size=3,vad_filter=False,condition_on_previous_text=False,clip_timestamps='0,400')
rows=[]
for segment in segments:
    row=dict(start=segment.start,end=segment.end,text=segment.text)
    rows.append(row)
    print(json.dumps(row,ensure_ascii=False),flush=True)
out.write_text(json.dumps(dict(method='faster-whisper tiny.en CPU int8; no supplied transcript or initial prompt; first 400 seconds',source=str(source),duration=info.duration,segments=rows),ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved',out,flush=True)
