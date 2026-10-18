# Self-hosting an open model

How the Qwen runs were served, and two lessons that cost money:

```
# on a GPU pod (we used RunPod, 1× H100)
vllm serve Qwen/Qwen3.5-9B --host 127.0.0.1 --port 8000 --api-key $VLLM_API_KEY \
  --max-model-len 65536 --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder --reasoning-parser qwen3

# on your laptop: an SSH tunnel, leave it open
ssh -N -L 8000:localhost:8000 root@<pod-ip> -p <ssh-port>

VLLM_BASE_URL=http://localhost:8000/v1 uv run main.py qwen_solo --seed 1
```

- **Use an SSH tunnel, not the public HTTP proxy.** The proxy cut every call
  longer than 120 s (Cloudflare error 524). Qwen sometimes thinks for 2
  minutes, so runs crashed.
- **Pick a GPU host with CUDA 13.0 or newer.** Current vLLM installs a
  PyTorch built for CUDA 13 and fails on a 12.8 driver.
