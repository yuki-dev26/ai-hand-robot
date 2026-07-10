"""Silero VAD による自動発話切り出し録音。

発話が min_speech_sec 以上続き、その後 min_silence_sec の無音になったら
WAV を返す。短い発話は破棄して聞き続ける。
"""

from __future__ import annotations

import io
import time
import wave
from collections import deque
from typing import Any

import numpy as np
import sounddevice as sd
import torch
from silero_vad import VADIterator, load_silero_vad

SAMPLE_RATE = 16_000
CHANNELS = 1
CHUNK_SAMPLES = 512  # Silero VAD @ 16kHz は 512 samples 必須
CHUNK_SEC = CHUNK_SAMPLES / SAMPLE_RATE

MIN_SPEECH_SEC = 3.0
MIN_SILENCE_SEC = 1.0
# 発話開始直前のバッファ (切り出し欠け防止)
PRE_ROLL_CHUNKS = int(0.5 / CHUNK_SEC)
# 無音待機が続くと VAD 内部状態が劣化するので定期リセット
IDLE_RESET_SEC = 30.0

_model: Any | None = None


def get_vad_model() -> Any:
    """Silero VAD モデルを遅延ロードして再利用する。"""
    global _model
    if _model is None:
        print("Silero VAD を読み込み中...")
        _model = load_silero_vad()
    return _model


def _to_wav_bytes(pcm_float: np.ndarray) -> bytes:
    pcm = np.clip(pcm_float * 32767, -32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def record_utterance(
    *,
    min_speech_sec: float = MIN_SPEECH_SEC,
    min_silence_sec: float = MIN_SILENCE_SEC,
) -> bytes:
    """Silero VAD で発話を切り出して WAV バイト列を返す。

    - 発話開始を検知して録音開始
    - 有声区間が min_speech_sec 以上あり、無音が min_silence_sec 続いたら確定
    - 短い発話は破棄して再待機
    """
    model = get_vad_model()
    vad = VADIterator(
        model,
        sampling_rate=SAMPLE_RATE,
        min_silence_duration_ms=int(min_silence_sec * 1000),
    )

    pre_roll: deque[np.ndarray] = deque(maxlen=PRE_ROLL_CHUNKS)
    speech_chunks: list[np.ndarray] = []
    in_speech = False
    # start〜end までのサンプル数 (pre-roll は含めない)。end には末尾無音も含まれる。
    segment_samples = 0
    last_activity = time.monotonic()

    print(
        f"聞き取り中... (発話 {min_speech_sec:g}秒以上 → 無音 {min_silence_sec:g}秒で送信 / Ctrl+C で停止)"
    )

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        blocksize=CHUNK_SAMPLES,
    ) as stream:
        while True:
            indata, overflowed = stream.read(CHUNK_SAMPLES)
            if overflowed:
                print("録音警告: バッファオーバーフロー")

            chunk = indata[:, 0].copy()
            tensor = torch.from_numpy(chunk)

            event = vad(tensor, return_seconds=True)

            if event and "start" in event:
                in_speech = True
                speech_chunks = list(pre_roll)
                segment_samples = 0
                last_activity = time.monotonic()
                print("  発話開始")

            if in_speech:
                speech_chunks.append(chunk)
                segment_samples += len(chunk)
                last_activity = time.monotonic()
            else:
                pre_roll.append(chunk)
                # 長時間の無音待機で VAD 状態が劣化するのを防ぐ
                if time.monotonic() - last_activity >= IDLE_RESET_SEC:
                    vad.reset_states()
                    last_activity = time.monotonic()

            if event and "end" in event and in_speech:
                # end イベントは min_silence_sec の無音を含んで発火する
                voiced_sec = max(0.0, segment_samples / SAMPLE_RATE - min_silence_sec)
                in_speech = False
                vad.reset_states()
                pre_roll.clear()
                last_activity = time.monotonic()

                if voiced_sec < min_speech_sec:
                    print(
                        f"  短すぎる発話を破棄 (有声 {voiced_sec:.1f}秒 < {min_speech_sec:g}秒)"
                    )
                    speech_chunks = []
                    segment_samples = 0
                    continue

                print(f"  発話確定 (有声 {voiced_sec:.1f}秒)")
                audio = np.concatenate(speech_chunks)
                return _to_wav_bytes(audio)
