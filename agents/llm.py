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
import os
import time

import anthropic
import openai
from dotenv import load_dotenv

load_dotenv()  # API keys come from .env, never from code

# USD per 1M tokens (input, cached input, output). Prices change: re-check
# and update the date.
# Cached input: re-sent history that matches the last request is billed
# cheaper; each provider sets its own cached price.
PRICES = {
    # Anthropic list price for prompts up to 100K, checked 2026-10-11.
    "claude-haiku-5-5": (0.10, 0.01, 0.50),
    # OpenAI list price, standard tier, checked 2026-10-12.
    "gpt-6-luna": (0.10, 0.01, 0.50),
    # xAI list price for prompts under 200K, docs.x.ai/docs/models, checked 2026-10-12.
    "grok-4.20-0309-reasoning": (1.25, 0.20, 2.50),
}

# The new part of a prompt is written to cache at 1.25x the input price
# (5-minute cache): Anthropic caching docs 2026-10-11, OpenAI 2026-10-12.
CACHE_WRITE = 1.25


def cost_usd(model, tokens_in, tokens_out, cache_read=0, cache_write=0):
    # Unknown model: None, not 0, so a missing price is never mistaken for free.
    # tokens_in here is only the uncached input.
    if model not in PRICES:
        return None
    price_in, price_cached, price_out = PRICES[model]
    return (tokens_in * price_in + cache_read * price_cached
            + cache_write * price_in * CACHE_WRITE + tokens_out * price_out) / 1_000_000


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


def to_chat_messages(system, messages):
    # Chat Completions format: the system prompt is the first message.
    out = [{"role": "system", "content": system}]
    for m in messages:
        if m["role"] == "user":
            out.append({"role": "user", "content": m["text"]})
        elif m["role"] == "assistant":
            out.append(m["raw"])
        elif m["role"] == "tool":
            # One message per result, matched to its call by tool_call_id.
            for r in m["results"]:
                out.append({"role": "tool", "tool_call_id": r["id"], "content": r["content"]})
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
    # "auto" summary so the log shows how it reasoned, like Claude's
    # "summarized". medium is the model's default effort.
    return call_responses(client, model, system, messages, tools,
                          reasoning={"effort": "medium", "summary": "auto"})


def call_xai(model, system, messages, tools):
    # xAI speaks OpenAI's Responses API, so only the address and key differ.
    client = openai.OpenAI(base_url="https://api.x.ai/v1", api_key=os.environ["XAI_API_KEY"])
    # No reasoning settings: xAI's docs list no effort or summary options
    # for grok-4.20, and an unknown option could be rejected.
    return call_responses(client, model, system, messages, tools, reasoning=None)


def call_responses(client, model, system, messages, tools, reasoning):
    extra = {"reasoning": reasoning} if reasoning else {}
    start = time.perf_counter()
    response = client.responses.create(
        model=model,
        instructions=system,
        input=to_openai_input(messages),
        # strict=False: strict mode demands schema changes Claude doesn't
        # need; every model should get exactly the same tools.
        tools=[{"type": "function", "name": t["name"], "description": t["description"],
                "parameters": t["params"], "strict": False} for t in tools],
        # store=False: the provider keeps no copy, we resend the whole history
        # as with Claude. Reasoning then comes back encrypted so it can be replayed.
        store=False,
        include=["reasoning.encrypted_content"],
        max_output_tokens=16000,
        **extra,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    text, reasoning, tool_calls = [], [], []
    for item in response.output:
        if item.type == "message":
            text.extend(part.text for part in item.content if part.type == "output_text")
        elif item.type == "reasoning":
            reasoning.extend(part.text for part in item.summary or [])
        elif item.type == "function_call":
            # call_id, not id: the result must quote call_id to match.
            tool_calls.append({"id": item.call_id, "name": item.name, "args": json.loads(item.arguments)})

    usage = response.usage
    cache_read = usage.input_tokens_details.cached_tokens or 0
    # OpenAI reports cache writes; other providers may leave the field out.
    cache_write = getattr(usage.input_tokens_details, "cache_write_tokens", 0) or 0
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


def call_chat(model, system, messages, tools):
    # Our own vLLM server; it speaks OpenAI's Chat Completions format.
    client = openai.OpenAI(base_url=os.environ["VLLM_BASE_URL"], api_key=os.environ["VLLM_API_KEY"])
    start = time.perf_counter()
    # No temperature etc.: vLLM uses the model's own recommended defaults,
    # as Haiku and Luna use theirs.
    response = client.chat.completions.create(
        model=model,
        messages=to_chat_messages(system, messages),
        tools=[{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                 "parameters": t["params"]}} for t in tools],
        max_tokens=16000,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    choice = response.choices[0]
    message = choice.message
    tool_calls = []
    for call in message.tool_calls or []:
        try:
            args = json.loads(call.function.arguments)
        except json.JSONDecodeError:
            # Small models sometimes write broken JSON. Empty args make the
            # game answer "invalid arguments" instead of crashing the run.
            args = {}
        tool_calls.append({"id": call.id, "name": call.function.name, "args": args})

    # Replay only the answer and tool calls, not the thinking: Qwen's model
    # card says past thinking should not be in the history.
    raw = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        raw["tool_calls"] = [call.to_dict() for call in message.tool_calls]

    # vLLM's reasoning parser puts the thinking in an extra field; its name
    # changed between vLLM versions, so try both.
    reasoning = getattr(message, "reasoning", None) or getattr(message, "reasoning_content", None) or ""
    usage = response.usage
    return {
        "text": message.content or "",
        "reasoning": reasoning,
        "tool_calls": tool_calls,
        "raw": raw,
        "stop_reason": choice.finish_reason,
        "tokens_in": usage.prompt_tokens,
        "cache_read": 0,  # vLLM reuses cached prefixes but doesn't report it by default
        "cache_write": 0,
        "tokens_out": usage.completion_tokens,  # includes thinking tokens
        "latency_ms": round(latency_ms),
        # None: we pay per GPU hour, not per token (see cost_usd).
        "cost_usd": cost_usd(model, usage.prompt_tokens, usage.completion_tokens),
    }


ADAPTERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
    "xai": call_xai,
    "vllm": call_chat,
}


def call_model(config, system, messages, tools):
    # config: {"provider": "anthropic", "model": "claude-haiku-5-5"}
    adapter = ADAPTERS[config["provider"]]
    return adapter(config["model"], system, messages, tools)
