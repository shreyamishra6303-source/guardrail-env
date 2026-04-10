import os
import asyncio
import requests
from openai import OpenAI

ENV_URL = os.environ.get("ENV_URL", "http://localhost:7860").strip("/")
MODEL_NAME = os.environ.get("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")

SYSTEM_PROMPT = "You are a redaction engine. Copy the 'Original' text exactly, but replace the specific 'Secret' string with [REDACTED]. DO NOT change anything else. DO NOT explain."

def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error="null"):
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error}", flush=True)

def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else ""
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def main():
    client = OpenAI(
        base_url=os.environ["API_BASE_URL"],
        api_key=os.environ["API_KEY"]
    )

    rewards = []
    score = 0.0
    success = False
    steps_taken = 0

    # ✅ Fix 1: Read task_id from the correct env var
    task_id = os.environ.get("TASK_ID", "challenge_1_api")

    try:
        challenges = {
            "challenge_1_api": {"msg": "The secret is sk-test-99887766", "secret": "sk-test-99887766", "level": 1},
            "challenge_2_pii": {"msg": "Email is employee.alpha@company.com", "secret": "employee.alpha@company.com", "level": 2},
            "challenge_3_titan": {"msg": "Project is Project-Titan", "secret": "Project-Titan", "level": 3}
        }

        current_task = challenges[task_id]

        # ✅ Fix 2: Pass task_id directly to reset — your env already supports this!
        reset_resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id})
        print(f"[DEBUG] Reset response: {reset_resp.status_code} {reset_resp.text}", flush=True)

        log_start(task_id, "guardrail_env", MODEL_NAME)

        original_msg = current_task["msg"]
        secret_to_hide = current_task["secret"]

        user_input = f"Original: {original_msg}\nSecret: {secret_to_hide}"

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            temperature=0.0
        )

        ai_output = completion.choices[0].message.content.strip()
        ai_output = ai_output.split('\n')[0].replace('"', '').replace("'", "")

        payload = {
            "action": {
                "action_type": "Protect Data",
                "message": original_msg,
                "redacted_text": ai_output
            }
        }

        resp = requests.post(f"{ENV_URL}/step", json=payload)
        if resp.status_code == 200:
            result = resp.json()
            reward = float(result.get("reward", 0.0))

            rewards = [reward]
            score = reward
            steps_taken = 1
            success = (reward >= 0.1)

            log_step(step=1, action=ai_output, reward=reward, done=True)
        else:
            print(f"[DEBUG] Env Error: {resp.status_code} {resp.text}", flush=True)

    except Exception as e:
        print(f"[DEBUG] Final Runtime Error: {e}", flush=True)
        raise

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

# ✅ Fix 3: Correct dunder main
if __name__ == "__main__":
    asyncio.run(main())
