# Innate MARS Documentation

> Local mirror of https://docs.innate.bot — fetched 2026-04-11 for the RoboHacks hackathon.
> MARS OS 0.4.5 · Cloud Agent 0.2.1 · Controller App 1.1.0

## How to use this folder

Split by topic so you can `@`-reference just the parts you need without burning context on the whole docs site.
For broad full-text search across everything, use `grep` in this folder or reference the monolithic `../INNATE_DOCS.md`.

## Files

| File | Topic | What's inside |
|------|-------|----------------|
| [`01-hackathon.md`](01-hackathon.md) | **Start here** | Hackathon setup, quick start, use cases. **Read first.** _(19 KB)_ |
| [`02-hardware.md`](02-hardware.md) | **Hardware** | MARS sensors, arm, compute, calibration, battery, connectivity, troubleshooting. _(32 KB)_ |
| [`03-software-setup.md`](03-software-setup.md) | **Dev setup** | Software architecture, dev loop, Innate CLI, Foxglove, BASIC agent. _(30 KB)_ |
| [`04-agents.md`](04-agents.md) | **Agents** | Agent definitions, starting agents, examples, Chess beta. _(25 KB)_ |
| [`05-skills.md`](05-skills.md) | **Skills** | Code-defined + policy-defined skills, robot interfaces, example skills. **Core for building behaviors.** _(51 KB)_ |
| [`06-ros2.md`](06-ros2.md) | **ROS2** | Topics, services, actions, nav/manip stacks, debugging. _(19 KB)_ |
| [`07-training.md`](07-training.md) | **Training** | Data collection → HDF5 → ACT policy training → evaluate → deploy. **For VLA work.** _(32 KB)_ |
| [`08-support.md`](08-support.md) | **Support** | Discord + API reference. _(0 KB)_ |

## Recommended reading order for a VLA project

1. [`01-hackathon.md`](01-hackathon.md) — get the robot on, understand the stack
2. [`05-skills.md`](05-skills.md) — skills are what your agent invokes; focus on policy-defined + physical skill examples
3. [`07-training.md`](07-training.md) — full train-deploy loop for ACT policies (or your own VLA)
4. [`04-agents.md`](04-agents.md) — if you want an LLM brain orchestrating the skill
5. [`06-ros2.md`](06-ros2.md) — only dive in when you need low-level topics/services
6. Hardware/setup/support as needed

## External resources

- **Innate OS repo:** https://github.com/innate-inc/innate-os
- **RoboHacks utils (HDF5→LeRobot converter, STEP files, APK):** https://github.com/innate-inc/robohacks-utils
- **GraspGen reference project:** https://github.com/innate-inc/GraspGen
- **Discord:** https://discord.com/invite/KtkyT97kc7
- **W&B training dashboard:** https://wandb.ai/vignesh-anand/act-simple/table
- **OpenAPI spec:** https://docs.innate.bot/api-reference/openapi.json
- **Mintlify docs index (llms.txt):** https://docs.innate.bot/llms.txt

## Regenerating

Raw page cache is at `/tmp/innate_docs/`. Re-fetch with the Python urllib script or curl each URL in `/tmp/innate_docs/urls.txt`.