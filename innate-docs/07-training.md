# Training & Policy Development

> End-to-end pipeline for training manipulation policies: data collection, dataset format, ACT training, evaluation, and deployment.

> Source: https://docs.innate.bot · mirrored 2026-04-11 · MARS OS 0.4.5

## Contents

- [Training Overview](#training-overview)
- [Data Collection](#data-collection)
- [Dataset Format](#dataset-format)
- [Train ACT Policy](#train-act-policy)
- [Training Manager](#training-manager)
- [Evaluate](#evaluate)
- [Deploy Trained Skill](#deploy-trained-skill)

---

## Training Overview

_Source: https://docs.innate.bot/training/overview.md_

# Training overview

> Teach your robot new manipulation skills by demonstrating them.

Innate lets you train end-to-end manipulation policies directly from the app. You demonstrate a task with the leader arm, upload the data, train a model on Innate's cloud GPUs, and deploy the result as a skill your robot can execute autonomously.

The underlying architecture is [ACT (Action Chunking with Transformers)](https://arxiv.org/abs/2304.13705) — a neural network that observes camera images and joint positions, then outputs coordinated arm and base actions.

## The pipeline at a glance

```text  theme={null}
Record episodes  →  Upload dataset  →  Train on cloud  →  Download model  →  Run as a skill
     (app)            (~10s/min)        (1-3 hours)         (automatic)        (app or code)
```

Everything happens through four tabs inside a physical skill page in the app:

| Tab           | What you do                                         |
| ------------- | --------------------------------------------------- |
| **Record**    | Collect demonstration episodes with the leader arm  |
| **Train**     | Configure hyperparameters and launch a training run |
| **Runs**      | Monitor active training jobs                        |
| **Completed** | Download finished models and activate them          |

Once a trained model is activated, the skill appears in **Manual Control** and is available to agents and code.

## What goes in, what comes out

**Input:** A dataset of teleoperated demonstrations — each episode captures synchronized camera images (main + wrist), joint positions, joint velocities, and optionally wheel odometry at 30 Hz.

**Output:** A PyTorch checkpoint that runs inference at 25 Hz, outputting 6 arm joint commands and 2 base velocity commands every 40 ms.

## When to use trained skills

Trained policies shine when:

* The task involves **visuomotor coordination** (reach for, grasp, place)
* Object positions **vary between runs** and the robot needs to adapt visually
* Writing explicit motion code would be brittle or impractical

For fixed, repeatable motions (a wave, a gesture), a **replay skill** is simpler — record once, play back. See [Policy-Defined Skills](/software/skills/policy-defined-skills) for the comparison.

## Next steps

<CardGroup cols={2}>
  <Card title="Record a dataset" icon="video" href="/training/data-collection">
    Collect high-quality demonstrations.
  </Card>

  <Card title="Train a policy" icon="brain" href="/training/train-act-policy">
    Configure and launch training on Innate's cloud.
  </Card>

  <Card title="Deploy your skill" icon="rocket" href="/training/deploy-trained-skill">
    Download, activate, and run your trained model.
  </Card>

  <Card title="Dataset format" icon="database" href="/training/dataset-format">
    Understand what's inside each episode file.
  </Card>

  <Card title="Training Manager" icon="wrench" href="/training/training-manager">
    Browser-based power-user UI for dataset management.
  </Card>
</CardGroup>


---

## Data Collection

_Source: https://docs.innate.bot/training/data-collection.md_

# Record a dataset

> Collect high-quality demonstration episodes for training a manipulation policy.

Training a manipulation policy starts with data. You teleoperate the robot through the task you want it to learn, and the app records synchronized camera images, joint positions, and velocities at 30 Hz. The more consistent and varied your demonstrations, the better the resulting policy.

## Create a physical skill

Before you can record, you need a skill entry to hold your dataset.

<Steps>
  <Step title="Open the Skills screen">
    In the app, tap **Skills** and switch to the **Physical** tab.
  </Step>

  <Step title="Create the skill">
    Tap the **+** button, enter a name in **Enter Action name here**, and tap **Create Physical Skill**. The app opens the episode recorder directly.
  </Step>
</Steps>

If the skill already exists, open **Skills**, go to the **Datasets** tab, and select it.

## Record episodes

Inside the skill page's **Record** tab you'll see an episode counter, the current episode list, and a **Record Episode** button.

<Steps>
  <Step title="Open the recorder">
    Tap **Record Episode** at the bottom of the Record tab.
  </Step>

  <Step title="Enable arm streaming">
    On the recorder screen, toggle **Arm** on. The **Record** button is enabled only when arm updates are flowing (you'll see an MPS value appear).
  </Step>

  <Step title="Capture the demonstration">
    Press **Record**, teleoperate the robot through the task, then press **Stop** when done.
  </Step>

  <Step title="Save or discard">
    After stopping, choose **Save** to keep the episode or **Discard** to drop it.
  </Step>
</Steps>

Repeat until you have enough episodes. See the tips below for guidance on how many you need.

## Tips for high-quality data

<AccordionGroup>
  <Accordion title="How many episodes do I need?">
    **50–80 episodes** is a good starting point for a simple task (pick up one object from a fixed area). For tasks that require generalization across object positions, lighting, or object types, aim for **150+ episodes**. More diverse data almost always improves robustness.
  </Accordion>

  <Accordion title="Be consistent with start poses">
    Begin each episode with the arm in roughly the same position. Large variation in start poses confuses the policy — it spends capacity learning where to begin instead of how to complete the task.
  </Accordion>

  <Accordion title="Demonstrate smoothly and deliberately">
    Avoid jerky movements, hesitations, or mid-episode corrections. The policy learns to imitate exactly what you do, including mistakes. If you fumble, discard the episode and re-record.
  </Accordion>

  <Accordion title="Vary object placement slightly">
    Move the target object by 2–5 cm between episodes. This teaches the policy to use vision instead of memorizing a single position.
  </Accordion>

  <Accordion title="Control lighting and background">
    Keep lighting and background consistent across your recording session. Dramatic changes between episodes (e.g., a bright window that appears only in some episodes) add noise the policy can't resolve.
  </Accordion>

  <Accordion title="Recording with base movement">
    If your task involves driving the robot while manipulating, enable base movement in the recorder. The episode will additionally capture `cmd_vel` and odometry data. See [Dataset format](/training/dataset-format#additional-fields-for-mobile-tasks) for details on the extra fields.
  </Accordion>
</AccordionGroup>

## Review your dataset

After saving, return to the skill's **Record** tab to inspect your episodes. Each episode card shows an index and timestamp.

Tap any episode to open **Episode Replay**, where you can play back the recorded actions and camera feeds to verify quality. Delete any episodes that look wrong — inconsistent demonstrations hurt more than a smaller dataset helps.

## Upload to the cloud

Once you're satisfied with your dataset, upload it so it's available for training.

<Steps>
  <Step title="Open the Record tab">
    Navigate to the skill's **Record** tab. You'll see an **Upload** button and a sync status indicator.
  </Step>

  <Step title="Start the upload">
    Tap **Upload**. The app compresses your episodes and uploads them to Innate's training servers. A progress indicator shows the current stage.
  </Step>

  <Step title="Confirm sync status">
    When the upload finishes, the sync badge turns green. You can verify this on the **Train** tab — the dataset card should show the correct episode count and a green sync status.
  </Step>
</Steps>

<Tip>
  If you add more episodes later, upload again. Only new episodes are transferred — you don't need to re-upload the entire dataset.
</Tip>

## Next steps

<CardGroup cols={2}>
  <Card title="Train a policy" icon="brain" href="/training/train-act-policy">
    Configure hyperparameters and launch training on Innate's cloud.
  </Card>

  <Card title="Dataset format" icon="database" href="/training/dataset-format">
    Understand what's inside each episode file.
  </Card>

  <Card title="Training Manager" icon="wrench" href="/training/training-manager">
    Power-user web UI for merging datasets, deleting episodes, and more.
  </Card>
</CardGroup>


---

## Dataset Format

_Source: https://docs.innate.bot/training/dataset-format.md_

# Dataset format

> What's inside each recorded episode and how the data is structured.

Understanding the dataset format is useful if you want to inspect your recordings, debug training issues, or build custom tooling around the training pipeline.

## File structure

Each physical skill lives in a directory under `~/skills/` on the robot:

```text  theme={null}
~/skills/pick_up_cup/
├── metadata.json           # Skill config (name, type, execution params)
├── data/
│   ├── episode_0.h5        # First recorded episode
│   ├── episode_1.h5        # Second recorded episode
│   └── ...
└── <run_id>/               # Created after training completes
    ├── act_policy_step_135000.pth   # Trained model checkpoint
    └── dataset_stats.pt             # Normalization statistics
```

## Episode format (HDF5)

Each episode is stored as an HDF5 file with the following structure:

| Dataset              | Shape              | Description                                   |
| -------------------- | ------------------ | --------------------------------------------- |
| `action`             | `(T, action_dim)`  | Leader arm commands recorded at each timestep |
| `qpos`               | `(T, num_joints)`  | Follower arm joint positions                  |
| `qvel`               | `(T, num_joints)`  | Follower arm joint velocities                 |
| `images/main_camera` | `(T, 480, 640, 3)` | Main camera RGB frames                        |
| `images/arm_camera`  | `(T, 480, 640, 3)` | Wrist camera RGB frames                       |

Where `T` is the number of timesteps in the episode and `action_dim` is typically 6 (joint positions) or 10 (6 joints + 2 base velocity + 2 reserved).

### Additional fields for mobile tasks

When recording with base movement enabled, the episode also includes:

| Dataset   | Shape      | Description                                  |
| --------- | ---------- | -------------------------------------------- |
| `cmd_vel` | `(T, 2)`   | Base velocity commands (linear x, angular z) |
| `odom`    | `(T, ...)` | Odometry readings from `/odom`               |

## Recording parameters

The recorder captures data at **30 Hz** by default with these settings (from `recorder.yaml`):

| Parameter                 | Value                                                     |
| ------------------------- | --------------------------------------------------------- |
| Data frequency            | 30 Hz                                                     |
| Image resolution          | 640 × 480                                                 |
| Max timesteps per episode | 1800 (60 seconds at 30 Hz)                                |
| Camera topics             | `/mars/main_camera/left/image_raw`, `/mars/arm/image_raw` |
| Arm state topic           | `/mars/arm/state`                                         |
| Leader command topic      | `/mars/arm/commands`                                      |

## Metadata file

Each skill directory contains a `metadata.json` that evolves as you progress through the pipeline:

**After creating the skill:**

```json  theme={null}
{
  "name": "pick_up_cup",
  "type": "learned"
}
```

**After training and activation:**

```json  theme={null}
{
  "name": "pick_up_cup",
  "type": "learned",
  "guidelines": "Use when you need to pick up a cup from the table",
  "execution": {
    "model_type": "act_policy",
    "checkpoint": "run_abc123/act_policy_step_135000.pth",
    "stats_file": "run_abc123/dataset_stats.pt",
    "action_dim": 10,
    "duration": 45.0,
    "start_pose": [-0.015, -0.399, 1.456, -1.135, -0.023, 0.833],
    "end_pose": []
  }
}
```

The `execution` block tells the BehaviorServer everything it needs to load and run the policy: which checkpoint to use, the action dimensionality, the maximum execution duration, and the arm pose to move to before starting inference.

## Normalization statistics

The training pipeline computes per-feature normalization statistics (mean and standard deviation) from your dataset and saves them in `dataset_stats.pt`. During inference, the policy uses these stats to normalize observations and unnormalize action outputs, ensuring consistency between what the model saw during training and what it sees at runtime.


---

## Train ACT Policy

_Source: https://docs.innate.bot/training/train-act-policy.md_

# Train an ACT policy

> Configure hyperparameters and launch training on Innate's cloud GPUs.

Once your dataset is [uploaded](/training/data-collection), you can train an ACT policy from the **Train** tab inside the skill page.

ACT ([Action Chunking with Transformers](https://arxiv.org/abs/2304.13705)) is a visuomotor policy architecture that takes camera images and joint positions as input and predicts a chunk of future actions at once. The "chunking" makes the output temporally smooth and reduces compounding errors compared to single-step prediction.

## Configure hyperparameters

The **Train** tab shows your dataset summary and a set of tunable hyperparameters. The defaults work well for most tasks — adjust them only if you have a reason to.

| Parameter         | Default | What it controls                                                                                                |
| ----------------- | ------- | --------------------------------------------------------------------------------------------------------------- |
| **Chunk size**    | 30      | Number of future actions predicted per inference step. Larger values produce smoother but less reactive motion. |
| **Batch size**    | 96      | Training examples per gradient step. Larger batches are more stable but use more GPU memory.                    |
| **Max steps**     | 120,000 | Total training iterations. More steps can improve quality but eventually overfit on small datasets.             |
| **Learning rate** | 5e-5    | Step size for updating the transformer weights.                                                                 |
| **LR backbone**   | 5e-5    | Step size for the vision backbone (ResNet18). Lower values fine-tune vision features more gently.               |

<Tip>
  Tap the **?** icon next to the hyperparameters for an in-app explanation of each one.
</Tip>

### When to change the defaults

* **Small dataset (50–80 episodes):** Lower max steps to \~80,000 to avoid overfitting.
* **Long episodes or complex task:** Increase max steps to 150,000–200,000.
* **Robot seems to hesitate during execution:** Try a larger chunk size (50–80) for smoother output.
* **Robot overshoots or ignores corrections:** Try a smaller chunk size (15–20) for more reactive behavior.

## Start a training run

<Steps>
  <Step title="Verify sync status">
    The **Train** tab shows a dataset card. Confirm the sync badge is green and the episode count looks correct. If it says "Not synced," go back to the **Record** tab and upload first.
  </Step>

  <Step title="Adjust parameters (optional)">
    Edit any hyperparameters you want to change, or leave the defaults.
  </Step>

  <Step title="Launch training">
    Tap **Start Training Run**. Confirm in the dialog. The app creates a run on Innate's cloud and switches to the **Runs** tab.
  </Step>
</Steps>

Training runs on Innate's GPU servers. A typical run with default settings takes **1–3 hours** depending on dataset size.

<Info>
  Each robot can have one active training run at a time by default. If you need concurrent runs, reach out on [Discord](https://discord.gg/innate) for approval.
</Info>

## Monitor a run

The **Runs** tab shows all active (non-completed) training jobs for this skill. Each run card displays:

* **Run ID** — a unique identifier
* **Status** — the current stage in the pipeline
* A progress indicator

### Training run lifecycle

| Status               | Meaning                                       |
| -------------------- | --------------------------------------------- |
| Waiting for approval | Run is queued and pending GPU allocation      |
| Approved             | Resources allocated, about to start           |
| Booting              | Training instance is spinning up              |
| Running              | Training is in progress                       |
| Done                 | Training finished, model is ready to download |

You can safely close the app or turn off your robot's screen while training runs. The job continues on the cloud. Status updates resume when you reopen the skill page.

## What happens during training

Behind the scenes, the training server:

1. Loads your episodes (images, joint positions, velocities) into a normalized dataset
2. Trains an ACT model with a ResNet18 vision backbone and a transformer encoder-decoder
3. Uses a variational autoencoder (VAE) to learn a latent action distribution
4. Saves checkpoints periodically throughout training
5. Produces a final checkpoint (`.pth`) and dataset statistics file (`.pt`)

The model learns to map what the robot sees and feels to the actions you demonstrated — effectively learning to imitate your behavior.

## Next steps

When the run status reaches **Done**, head to the [deploy page](/training/deploy-trained-skill) to download and activate your trained skill.


---

## Training Manager

_Source: https://docs.innate.bot/training/training-manager.md_

# Training Manager (web UI)

> A browser-based interface for managing datasets, editing skills, and launching training runs.

<Info>
  The Training Manager is an **experimental** tool — built in an evening by the
  team to scratch an itch. It works, it's useful, and it ships with the OS. But
  it's rough around the edges. Contributions welcome.
</Info>

The Training Manager is a local web server that runs on your robot and gives you a browser-based dashboard for the entire training pipeline. It's the power-user complement to the app's training UI — useful when you need to merge datasets, remove bad episodes, or point a training run at a custom ACT fork.

## Launch it

The Training Manager is bundled with the `training-client` CLI. Run it from inside the robot (via SSH) or inside the Docker container:

```bash  theme={null}
python -m training_client.cli ui
```

This starts a local web server and prints two URLs:

```text  theme={null}
  Training Manager
    Local:   http://localhost:8080
    Network: http://192.168.50.22:8080
```

Open the **Network** URL from any device on the same WiFi — your laptop, phone, or tablet.

### CLI options

| Flag             | Default                      | Description           |
| ---------------- | ---------------------------- | --------------------- |
| `--port`         | `8080`                       | HTTP port             |
| `--skills-dir`   | `~/skills`                   | Root skills directory |
| `-s`, `--server` | env `TRAINING_SERVER_URL`    | Orchestrator URL      |
| `-t`, `--token`  | env `INNATE_SERVICE_KEY`     | Service key           |
| `--issuer`       | env `INNATE_AUTH_ISSUER_URL` | Auth issuer URL       |

## The three tabs

The UI is organized into three tabs: **Skills**, **Datasets**, and **Training**.

### Skills tab

Browse every skill directory on the robot. Each card shows the skill name, type, episode count, and whether a trained checkpoint exists.

Click a skill to open its detail view, where you can:

* **Edit metadata** — change the skill name, guidelines (the text BASIC reads to decide when to use this skill), and execution parameters
* **View the full `metadata.json`** — useful for debugging or verifying that a checkpoint was activated correctly

### Datasets tab

This is where the Training Manager really earns its keep. For each skill, you can:

* **Browse episodes** — see every episode in the dataset with timestamps and metadata
* **Play back video** — watch the recorded camera feeds for any episode directly in the browser (both main and wrist cameras)
* **Delete episodes** — select bad episodes and create a cleaned copy of the dataset without them. The original is preserved; a new skill directory is created with the episodes re-indexed.
* **Merge datasets** — combine episodes from multiple skills into a single new dataset. Select which episodes to include from each source. This is useful when you've recorded demonstrations across multiple sessions or want to mix data from different setups.
* **Upload to cloud** — submit a skill and upload its data to Innate's training servers, with a progress bar showing compression and upload stages

<Tip>
  **Merge workflow example:** You recorded 30 episodes of "pick up cup" last
  week and 25 more today with a slightly different cup. Instead of retraining
  separately, merge both into a 55-episode "pick up cup v2" dataset and train
  once on the combined data.
</Tip>

### Training tab

View all training runs across all skills, create new runs, and monitor progress.

When creating a new run, you get full control over:

**Hyperparameters** — all the same parameters from the app, plus more:

| Parameter                | Default | Description                              |
| ------------------------ | ------- | ---------------------------------------- |
| `LEARNING_RATE`          | 5e-5    | Transformer learning rate                |
| `LEARNING_RATE_BACKBONE` | 5e-5    | Vision backbone (ResNet18) learning rate |
| `BATCH_SIZE`             | 96      | Training batch size                      |
| `MAX_STEPS`              | 120,000 | Total training iterations                |
| `CHUNK_SIZE`             | 30      | Action chunk length                      |
| `NUM_WORKERS`            | 4       | Data loader workers                      |
| `WORLD_SIZE`             | 4       | Number of GPUs                           |

**Repository and branch** — point the training server at a custom ACT repository and branch. This is the key feature for researchers: fork the ACT training code, modify the architecture or loss function, and run training against your fork without any server-side changes.

| Field          | Description                                           |
| -------------- | ----------------------------------------------------- |
| **Repository** | GitHub `owner/repo` path (e.g. `your-org/act-custom`) |
| **Ref**        | Branch name, tag, or commit SHA to check out          |

**Infrastructure** — configure GPU type, GPU count, time budget, and cost budget.

**Architecture parameters** are shown as read-only for reference (vision backbone, model dimensions, encoder/decoder layers, VAE settings).

Each run card shows its current status with live updates via server-sent events (SSE), so you can watch a run progress through the lifecycle without refreshing.

## Log terminal

A collapsible terminal panel at the bottom of every page streams real-time backend logs. This shows every API call, upload progress message, and error — handy for debugging when something doesn't work as expected.

## Architecture

The Training Manager is a FastAPI backend serving a React + Tailwind SPA. The backend delegates all cloud operations to the same `training_client` library that the ROS training node uses, so there's no duplicate logic.

```text  theme={null}
Browser ──→ FastAPI server (port 8080)
               ├── /api/skills     → reads/writes ~/skills/*/metadata.json
               ├── /api/datasets   → episode browsing, video streaming, merge, delete
               ├── /api/training   → list runs, create runs, watch status (via SSE)
               ├── /api/logs       → real-time log stream (SSE)
               └── /*              → serves the React SPA
                        │
                        ▼
               training_client.SkillManager
                        │
                        ▼
               Innate Training Orchestrator (training-v1.innate.bot)
```


---

## Evaluate

_Source: https://docs.innate.bot/training/evaluate.md_

# Evaluate and iterate

> Test your trained policy, diagnose problems, and improve it.

Training a policy is rarely one-and-done. This page covers how to evaluate your skill, identify common failure modes, and iterate toward reliable performance.

## First test

After [deploying your trained skill](/training/deploy-trained-skill), run it from **Manual Control** with the same setup you used for recording.

<Steps>
  <Step title="Reproduce the training scene">
    Place the robot, objects, and lighting as close as possible to the conditions you recorded in. The first test should be easy for the policy — if it fails on its own training distribution, something is wrong.
  </Step>

  <Step title="Run the skill">
    Select the skill in Manual Control and tap play. Watch the full execution without intervening.
  </Step>

  <Step title="Note the result">
    Did the robot complete the task? Where did it hesitate, overshoot, or fail? Mental notes are fine — you'll iterate fast.
  </Step>
</Steps>

## Common failure modes

| Symptom                                 | Likely cause                                             | Fix                                                                  |
| --------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------- |
| Robot doesn't move or barely moves      | Too few episodes, or episodes have inconsistent starts   | Record more episodes with consistent start poses                     |
| Arm overshoots the target               | Jerky demonstrations or high variance in approach angles | Re-record smoother demonstrations; try a larger chunk size           |
| Robot starts well but drifts            | Not enough variation in demonstrations                   | Add more episodes with slight object position changes                |
| Works on first run, fails on repeat     | Object or robot position shifted                         | Record with more position variation; aim for 2–5 cm spread           |
| Gripper doesn't close at the right time | Inconsistent grasp timing across episodes                | Focus on consistent timing when closing the gripper                  |
| Robot ignores the object entirely       | Lighting or background changed significantly             | Record in the current conditions, or control lighting more carefully |

## How to improve a policy

### Add more data

The most reliable way to improve a policy. Add 20–30 episodes that specifically cover the failure case, sync, and retrain. You don't need to start from scratch — the new episodes are added to the existing dataset.

### Tune hyperparameters

If the behavior is qualitatively close but not quite right:

* **Chunk size** controls the smoothness/reactivity tradeoff. Increase it if the robot hesitates; decrease it if the robot overshoots.
* **Max steps** may need increasing for larger datasets. A good heuristic: the model should see each episode hundreds of times during training.
* **Learning rate** — lower it (1e-5) if training seems unstable; raise it (1e-4) if the model isn't learning fast enough.

See the [hyperparameter reference](/training/train-act-policy#configure-hyperparameters) for details.

### Improve demonstration quality

Review your recorded episodes. Look for:

* Episodes where you hesitated or corrected course excessively
* Episodes that are much longer or shorter than average
* Episodes where the start pose is significantly different

Replace low-quality episodes with clean ones, re-sync, and retrain.

## Scaling up

Once your policy works in the original setup, gradually introduce variation:

1. **Move the object** a few centimeters between runs
2. **Change the object** slightly (same cup in a different color)
3. **Adjust lighting** modestly

If the policy breaks, record 10–20 more episodes under the new conditions and retrain. Each round of data makes the policy more robust.

<Tip>
  Policies trained on 150+ diverse episodes can generalize surprisingly well. Invest in data variety and you'll spend less time debugging.
</Tip>


---

## Deploy Trained Skill

_Source: https://docs.innate.bot/training/deploy-trained-skill.md_

# Deploy a trained skill

> Download your trained model, activate it, and run it on the robot.

Once a training run is marked **Done**, the model is ready to download to your robot and use as a skill.

## Download the model

When a run completes, it appears in the **Completed** tab (or shows a download button in the **Runs** tab).

<Steps>
  <Step title="Open the completed run">
    Navigate to the skill page and open the **Completed** tab. Find the run you want to deploy.
  </Step>

  <Step title="Tap Download">
    Tap the download button on the run card. The app downloads the trained checkpoint and dataset statistics file to the robot.
  </Step>

  <Step title="Wait for activation">
    A progress bar shows the download and verification stages. When it completes, the model is automatically activated — the skill's `metadata.json` is updated with the checkpoint path.
  </Step>
</Steps>

The robot's brain reloads automatically after activation. Your skill is now live.

<Info>
  Auto-download is also enabled. If the robot is on and connected when a training run finishes, the model downloads and activates without any manual action.
</Info>

## Run the skill from the app

The simplest way to test your trained skill is from **Manual Control**.

<Steps>
  <Step title="Open Manual Control">
    Go to the **Manual Control** screen from the app's main navigation.
  </Step>

  <Step title="Select the skill">
    Open the skill dropdown and select your newly trained skill. Only activated (non-training) skills appear in this list.
  </Step>

  <Step title="Execute">
    Tap the play button. The robot moves to the start pose and begins running the policy at 25 Hz — reading cameras, processing images, and outputting arm and base commands in real time.
  </Step>

  <Step title="Stop if needed">
    Tap the stop button at any time to interrupt execution. The robot halts immediately.
  </Step>
</Steps>

## Run the skill from code

Trained skills are available to agents and code-defined skills just like any other skill. Reference the skill by its ID in your agent's skill list:

```python  theme={null}
from brain_client.agent_types import Agent
from typing import List

class TidyUpAgent(Agent):
    @property
    def id(self) -> str:
        return "tidy_up"

    @property
    def display_name(self) -> str:
        return "Tidy Up"

    def get_skills(self) -> List[str]:
        return ["pick_up_cup", "navigate_to_position"]

    def get_prompt(self) -> str:
        return """You are a tidying robot. Use pick_up_cup to grab cups
        you see, then navigate to the kitchen to put them away."""
```

BASIC calls your trained skill the same way it calls any other skill — the execution pipeline handles loading the checkpoint, running inference, and sending commands to the hardware.

## What happens during execution

When the skill runs, the BehaviorServer:

1. Loads the ACT checkpoint into GPU memory
2. Moves the arm to the learned start pose
3. Enters a **25 Hz inference loop** where each cycle:
   * Captures frames from the main camera and wrist camera
   * Reads the current 6-DOF joint state
   * Resizes images to 224×224 and normalizes them
   * Runs a forward pass through the policy
   * Sends the first 6 outputs as joint commands to `/mars/arm/commands`
   * Sends outputs 7–8 as base velocity to `/cmd_vel`
4. Optionally moves the arm to an end pose when the task completes

## Multiple training runs

You can train multiple runs with different hyperparameters for the same skill. Each run produces an independent checkpoint stored in its own subdirectory. When you download and activate a run, it becomes the active checkpoint for that skill.

To switch between runs, download a different completed run — activation overwrites the checkpoint path in `metadata.json`.

## Iterating on a skill

If the skill doesn't perform as expected:

* **Add more episodes** to your dataset, sync again, and retrain. More data almost always helps.
* **Adjust hyperparameters** — see the [training guide](/training/train-act-policy#when-to-change-the-defaults) for tuning advice.
* **Review your demonstrations** — replay episodes to spot inconsistencies, then re-record the weak ones.

Training is fast and cheap to iterate on. Don't hesitate to run multiple rounds.


---
