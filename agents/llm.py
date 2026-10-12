# One way to call any model. The agent loop only speaks the common format
# below; each provider gets a small adapter that translates at the edge and
# measures tokens, latency and cost the same way for every model.
#
# Common format
#   tools:    {"name", "description", "params": <JSON schema>}
#   messages: {"role": "user", "text": ...}
#             {"role": "assistant", "text", "tool_calls": [{"id", "name", "args"}],
#              "provider", "raw": <provider's own content, replayed unchanged>}
#             {"role": "tool", "results": [{"id", "content"}]}
#   reply:    {"text", "reasoning", "tool_calls", "raw", "stop_reason",
#              "tokens_in", "cache_read", "cache_write", "tokens_out",
#              "latency_ms", "cost_usd"}

import json
import time

import anthropic
import openai
from dotenv import load_dotenv

load_dotenv()  # API keys come from .env, never from code

# USD per 1M tokens (input, output). Prices change: re-check and update the
# date. Haiku 5.5: Anthropic list price for prompts up to 100K, checked 2026-10-11.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    # GPT-6 Luna: OpenAI list price, standard tier, checked 2026-10-12.
    "gpt-6-luna": (0.10, 0.50),
}


# Prompt caching: re-sent history that matches the last request is billed
# at ~0.1x as a cache read; the new part is written to cache at ~1.25x
# (5-minute cache). Multipliers from Anthropic's caching docs, 2026-10-11.
# OpenAI (GPT-5.6 and later) uses the same 0.1x / 1.25x, and caches on its
# own with no cache_control needed. OpenAI caching docs, 2026-10-12.
CACHE_READ = 0.1
CACHE_WRITE = 1.25


def cost_usd(model, tokens_in, tokens_out, cache_read=0, cache_write=0):
    # Unknown model: None, not 0, so a missing price is never mistaken for free.
    # tokens_in here is only the uncached input.
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    billed_in = tokens_in + cache_read * CACHE_READ + cache_write * CACHE_WRITE
    return (billed_in * price_in + tokens_out * price_out) / 1_000_000


def to_anthropic_messages(messages):
    out = []
    for m in messages:
        if m["role"] == "user":
            out.append({"role": "user", "content": m["text"]})
        elif m["role"] == "assistant":
            # Replay Claude's own blocks unchanged: its thinking blocks are only
            # valid exactly as it wrote them.
            out.append({"role": "assistant", "content": m["raw"]})
        elif m["role"] == "tool":
            # All results of one turn go back in a single user message.
            results = [
                {"type": "tool_result", "tool_use_id": r["id"], "content": r["content"]}
                for r in m["results"]
            ]
            out.append({"role": "user", "content": results})
    return out


def to_openai_input(messages):
    # Responses API format. The system prompt goes in `instructions`, not here.
    out = []
    for m in messages:
        if m["role"] == "user":
            out.append({"role": "user", "content": m["text"]})
        elif m["role"] == "assistant":
            # Replay GPT's own output items (reasoning, tool calls, text)
            # unchanged, like Claude's thinking blocks.
            out.extend(m["raw"])
        elif m["role"] == "tool":
            # One item per result; Claude wants them all in one message.
            for r in m["results"]:
                out.append({"type": "function_call_output", "call_id": r["id"], "output": r["content"]})
    return out


def call_anthropic(model, system, messages, tools):
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    start = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        # "summarized" so the log shows how the agent reasoned; the default
        # on current models returns empty thinking text.
        thinking={"type": "adaptive", "display": "summarized"},
        # Each call re-sends the whole history; caching bills the repeated
        # part at ~0.1x. Auto mode marks the last block, so every call
        # reuses everything the previous call already sent.
        cache_control={"type": "ephemeral"},
        tools=[{"name": t["name"], "description": t["description"], "input_schema": t["params"]} for t in tools],
        messages=to_anthropic_messages(messages),
    )
    latency_ms = (time.perf_counter() - start) * 1000

    text, reasoning, tool_calls = [], [], []
    for block in response.content:
        if block.type == "text":
            text.append(block.text)
        elif block.type == "thinking":
            reasoning.append(block.thinking)
        elif block.type == "tool_use":
            tool_calls.append({"id": block.id, "name": block.name, "args": block.input})

    usage = response.usage
    uncached = usage.input_tokens  # only the part not served from cache
    cache_read = usage.cache_read_input_tokens or 0
    cache_write = usage.cache_creation_input_tokens or 0
    tokens_out = usage.output_tokens  # includes thinking tokens
    return {
        "text": "\n".join(text),
        "reasoning": "\n".join(reasoning),
        "tool_calls": tool_calls,
        "raw": response.to_dict()["content"],
        "stop_reason": response.stop_reason,
        # tokens_in is everything the model read, so runs with and without
        # caching compare; the cache fields show how much was cheap.
        "tokens_in": uncached + cache_read + cache_write,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "tokens_out": tokens_out,
        "latency_ms": round(latency_ms),
        "cost_usd": cost_usd(model, uncached, tokens_out, cache_read, cache_write),
    }


def call_openai(model, system, messages, tools):
    client = openai.OpenAI()  # reads OPENAI_API_KEY
    start = time.perf_counter()
    response = client.responses.create(
        model=model,
        instructions=system,
        input=to_openai_input(messages),
        # strict=False: strict mode demands schema changes Claude doesn't
        # need; both models should get exactly the same tools.
        tools=[{"type": "function", "name": t["name"], "description": t["description"],
                "parameters": t["params"], "strict": False} for t in tools],
        # "auto" summary so the log shows how it reasoned, like Claude's
        # "summarized". medium is the model's default effort.
        reasoning={"effort": "medium", "summary": "auto"},
        # store=False: OpenAI keeps no copy, we resend the whole history as
        # with Claude. Reasoning then comes back encrypted so it can be replayed.
        store=False,
        include=["reasoning.encrypted_content"],
        max_output_tokens=16000,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    text, reasoning, tool_calls = [], [], []
    for item in response.output:
        if item.type == "message":
            text.extend(part.text for part in item.content if part.type == "output_text")
        elif item.type == "reasoning":
            reasoning.extend(part.text for part in item.summary)
        elif item.type == "function_call":
            # call_id, not id: the result must quote call_id to match.
            tool_calls.append({"id": item.call_id, "name": item.name, "args": json.loads(item.arguments)})

    usage = response.usage
    cache_read = usage.input_tokens_details.cached_tokens or 0
    cache_write = usage.input_tokens_details.cache_write_tokens or 0
    # input_tokens counts everything read, cached parts included.
    uncached = usage.input_tokens - cache_read - cache_write
    tokens_out = usage.output_tokens  # includes reasoning tokens
    stop = response.incomplete_details.reason if response.incomplete_details else response.status
    return {
        "text": "\n".join(text),
        "reasoning": "\n".join(reasoning),
        "tool_calls": tool_calls,
        "raw": response.to_dict()["output"],
        "stop_reason": stop,
        "tokens_in": usage.input_tokens,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "tokens_out": tokens_out,
        "latency_ms": round(latency_ms),
        "cost_usd": cost_usd(model, uncached, tokens_out, cache_read, cache_write),
    }


ADAPTERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
}


def call_model(config, system, messages, tools):
    # config: {"provider": "anthropic", "model": "claude-haiku-5-5"}
    adapter = ADAPTERS[config["provider"]]
    return adapter(config["model"], system, messages, tools)
