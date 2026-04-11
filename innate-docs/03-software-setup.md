# Software Setup & Dev Environment

> Core software architecture, dev loop (edit → build → restart), Innate CLI, Foxglove visualization, BASIC agent, and inputs.

> Source: https://docs.innate.bot · mirrored 2026-04-11 · MARS OS 0.4.5

## Contents

- [Overview](#overview)
- [BASIC Agent](#basic-agent)
- [Development Setup](#development-setup)
- [MARS Quick Development](#mars-quick-development)
- [Advanced Development](#advanced-development)
- [Innate CLI](#innate-cli)
- [Foxglove Setup](#foxglove-setup)
- [Inputs](#inputs)

---

## Overview

_Source: https://docs.innate.bot/software/overview.md_

# Overview

How to create Agent Apps for Innate Robots using the SDK - or ROS2 straight

## Core concepts

<Frame caption="A system diagram of the software running on Innate robots">
  <img src="https://mintcdn.com/innateinc/0eXO6LY2jsVAky_A/images/system-diagram.png?fit=max&auto=format&n=0eXO6LY2jsVAky_A&q=85&s=ed2ac18e375f79de4e8682e8a282af69" alt="Innate software system diagram" width="2528" height="1073" data-path="images/system-diagram.png" />
</Frame>

#### An agentic OS

Innate robots run an agentic OS built on top of ROS2. It is powered by our cloud agent called BASIC.

This abstraction layer allows to create powerful agentic applications quickly without having to care about the usual suspects of classic robotics (unless you want to).

#### Agents

The central concept of the Innate OS is the `agent` , which is our name for a **physical app for robots.** They are defined by a **system prompt** and a set of **skills** they can use.

**Agents** are like **physical apps** for Innate robots.

The most simple agent is:

```python  theme={null}
from brain_client.agent_types import Agent
from typing import List

class HelloWorld(Agent):
    @property
    def id(self) -> str:
        return "hello_world"

    @property
    def display_name(self) -> str:
        return "Hello World"

    def get_skills(self) -> List[str]:
        return [""]

    def get_prompt(self) -> str:
        return """You are just a robot saying hello_world once you start."""
```

This will start the robot and make it say hello world on the speakers once.

See more in [Agents](/software/agents)

#### Skills

**Skills** are the second core concept of the Innate OS.

A skill can be defined with code, a model checkpoint (such as a **VLA**) or other specific interfaces we define for you. Adding a skill to an agent is like giving additional capabilities to your robot.

Similarly to agentic frameworks, **skills** can be thought as **tool calls**, with extra sauce.

Skills can be interrupted by the robot during execution if required, and send feedback in the context of to the running agent.

See how to create skills in [Skills](/software/skills)

#### BASIC

BASIC is the embodied AI agent that controls Mars. BASIC can run agents and skills, and gives Mars the ability to reason, memorize, plan and make decisions as it runs.

Understand more how BASIC runs in [Innate Capabilities](/software/basic)

#### ROS2 core

Our OS runs at the core on **ROS2** and can be augmented at that level by roboticists that understand it.

See [ROS2 Core](/software/ros2-core) for more information on nodes, topics, and services available.


---

## BASIC Agent

_Source: https://docs.innate.bot/software/basic.md_

# Innate Capabilities

**BASIC** is our embodied agent, named in tribute to the BASIC languages that hobbyists used in the early age of PCs. Think of it as the LLM OS running your agents and skills: it reasons over live perception, chooses the right skills, and controls the robot autonomously from your instructions.

BASIC is a multi-model system that behaves like one assistant with memory and planning. A key capability is **spatial RAG**: what MARS sees gets stored as spatial memories, so the agent can retrieve past observations (objects, places, scenes), answer questions about them, and navigate back to where they were seen.

In practice, this means you can ask things like "where did you last see my keys?" and BASIC can use its memory to point to a location or return there. The Innate Controller app surfaces these memories on phone, so you can inspect what was remembered and where.

## Technical Report

**TBD**

**BASIC** is evaluated and improved in a 3D simulation where we test a wide range of tasks and long-horizon behaviors. More details to be revealed soon.


---

## Development Setup

_Source: https://docs.innate.bot/software/development-setup.md_

# Development Setup

> Get your dev environment connected to MARS in under 10 minutes.

Everything runs on the robot. You SSH in, edit code, restart. That's it.

## Connect to MARS

<Steps>
  <Step title="Find your robot's IP">
    Open the Innate app. Go to **Settings** → **WiFi**. Note the IP address.
  </Step>

  <Step title="SSH in">
    ```bash  theme={null}
    ssh jetson1@<YOUR-ROBOT-IP>
    ```

    Default password: `goodbot`. See [Connecting via SSH](/robots/mars/connecting-via-ssh) for hostname, Ethernet, and USB-C options.
  </Step>

  <Step title="Open your IDE over SSH">
    Use **Cursor**, **Windsurf**, **VSCode**, or any editor with Remote SSH support.

    1. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`).
    2. Run **Remote-SSH: Connect to Host...**.
    3. Enter `jetson1@<YOUR-ROBOT-IP>`.
    4. Open the folder `/home/jetson1/innate-os/`.
  </Step>
</Steps>

<Tip>
  Set up SSH keys to skip the password prompt every time:

  ```bash  theme={null}
  ssh-copy-id jetson1@<YOUR-ROBOT-IP>
  ```
</Tip>

***

## Optional: Fork the open-source repo

<Info>
  You don't need to fork to start developing. Agents and skills in `~/agents/` and `~/skills/` work out of the box. Fork when you want to save, version-control, and share your work — or modify the OS itself (ROS2 nodes, drivers, launch files).
</Info>

MARS runs [innate-os](https://github.com/innate-robotics/innate-os), fully open source. Forking gives you your own remote repo to push changes to:

<Steps>
  <Step title="Fork on GitHub">
    Go to [github.com/innate-robotics/innate-os](https://github.com/innate-robotics/innate-os) and click **Fork**.
  </Step>

  <Step title="Clone your fork onto the robot">
    SSH into MARS and replace the default repo:

    ```bash  theme={null}
    cd ~
    mv innate-os innate-os-backup
    git clone https://github.com/<YOUR-USERNAME>/innate-os.git
    ```
  </Step>

  <Step title="Make your fork launch on startup">
    The systemd service points to `~/innate-os/`. Since you cloned into the same path, it just works. Verify:

    ```bash  theme={null}
    innate service restart
    ```
  </Step>
</Steps>

***

## Launch and restart

MARS auto-launches all ROS2 nodes on boot via systemd. **When you make changes, you need to restart.**

```bash  theme={null}
innate service restart
```

Or use the shorthand:

```bash  theme={null}
in8 restart
```

### Watch the nodes boot

```bash  theme={null}
innate service view
```

This attaches you to the tmux session where every ROS node runs.

| Keys                    | Action                                             |
| ----------------------- | -------------------------------------------------- |
| `Ctrl+B` then `0`–`6`   | Switch to a window                                 |
| `Ctrl+B` then `←` / `→` | Switch between left/right panes                    |
| `Ctrl+B` then `O`       | Cycle to the next pane                             |
| `Ctrl+B` then `Z`       | Zoom a pane to full screen (press again to unzoom) |
| `Ctrl+B` then `D`       | Detach from tmux (nodes keep running)              |

See the [Innate CLI Reference](/software/innate-cli) for all available commands.

***

## Shutting down gracefully

Always shut down properly before unplugging power. A hard power cut can corrupt the filesystem.

```bash  theme={null}
sudo shutdown now
```

Wait for the LED to turn off, then disconnect power.

***

## Project structure

When you SSH in, the key directories are:

| Path                   | What's there                               |
| ---------------------- | ------------------------------------------ |
| `~/agents/`            | Your agent definitions (hot-reloaded)      |
| `~/skills/`            | Your custom skills                         |
| `~/innate-os/`         | The full OS repo                           |
| `~/innate-os/ros2_ws/` | ROS2 workspace (all packages)              |
| `~/innate-os/scripts/` | Launch scripts, diagnostics, update system |

***

## Next steps

<CardGroup cols={2}>
  <Card title="Quick Development" icon="rocket" href="/software/mars-quick-development">
    Build your first agent in 5 minutes.
  </Card>

  <Card title="Advanced Development" icon="wrench" href="/software/advanced-development">
    Modify ROS2 nodes, recompile, visualize topics.
  </Card>

  <Card title="Innate CLI" icon="terminal" href="/software/innate-cli">
    Every command at your fingertips.
  </Card>

  <Card title="Foxglove Setup" icon="eye" href="/software/foxglove-setup">
    Visualize what your robot sees in real time.
  </Card>
</CardGroup>


---

## MARS Quick Development

_Source: https://docs.innate.bot/software/mars-quick-development.md_

# MARS Quick Development

Learn to create your first agent, train your first manipulation model, give MARS the ability to read emails, and put the pieces together

## Create your first agent

Now that you know the basics, you can create your first agent for Mars using the SDK. On the app, go to Settings -> Wifi and read the IP of the robot.

Now, on your PC, ssh in the robot with

```bash  theme={null}
ssh jetson1@<YOUR-ROBOT-IP>
```

Go to `~/agents/` and create a `hello_world.py` agent file:

```python  theme={null}
from typing import List
from brain_client.agent_types import Agent

class HelloWorld(Agent):
    @property
    def id(self) -> str:
        return "hello_world"

    @property
    def display_name(self) -> str:
        return "Hello World"

    def get_skills(self) -> List[str]:
        return [
            "navigate_to_position",
            "wave",
        ]

    def get_prompt(self) -> str:
        return """
You are a friendly greeting robot whose sole purpose is to say hello world to the user!

Your personality:
- You are a nice and cheerful robot.

Instructions:
- When you see a user in front of you, say "hello world" and wave at the user.
- Don't navigate, just turn around if you don't see the user.
"""
```

"*wave*" and "*navigate\_to\_position*" are basic skills that come already created for the robot. This agent makes use of them to act autonomously.

Save the file, then restart the robot (unplug and plug again), open the app and start your agent. Sit in front of the robot, and observe!

<iframe width="100%" height="420" src="https://www.youtube.com/embed/b7cNKEcER24" title="Run your first agent demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

To dive more in the details of how to develop agents:

<Card title="Agents" icon="robot" href="/software/agents">
  Deep-dive on agent structure, lifecycle, and examples.
</Card>

## Train your first manipulation model for a skill

Innate Robots arms can be trained using state-of-the-art manipulation AI models, running straight on the onboard computer. For MARS, we developed an improved version of ACT with a reward model - see [more details here](https://innate.bot/tbd)

To train it, you can use the app to collect episodes of data for imitation learning. I.E. you will be repeatedly performing the task with the robot for a given amount of repetitions to make sure it learns it the way you want.

In the app, go to Skills -> Physical, create a new skill, name it, and press "Add Episodes".

Then, arm the arm and press record to collect an episode. Ideally, all episodes should start in a similar position and end in a similar position, following roughly the same movement. Start with very similar trajectories to accomplish the goal while making sure that the arm camera has the objective of motion relatively in sight. More guidelines on training can be found [here](https://innate.bot/tbd).

Below, an example of training the arm to pick up a cherry.

<iframe width="100%" height="420" src="https://www.youtube.com/embed/dr1TuHpc_94" title="Train your first manipulation model" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

Once you collected around 50 episodes, you can start considering stopping data collection. We can easily train your dataset for you if you go to the Training tab and press Train with whole dataset. You can also use the episodes for yourself by ssh-ing in the robot and getting them there.

Once the model is trained (which takes up to 4 hours), you can get it back on your robot and then trigger it from Manual Control Screen!

## Create your first digital skill

Innate robots can also run any kind of code in the embodied agent BASIC, which can be used to query APIs online or run custom routines onboard.

Below is an example of how to create a skill that queries gmail to read the last emails.

```python  theme={null}
import imaplib
import email
from brain_client.skill_types import Skill, SkillResult

class RetrieveEmails(Primitive):
    def __init__(self, logger):
        self.logger = logger
        self.imap_server = "imap.gmail.com"
        self.email = "your_email@gmail.com"

    @property
    def name(self):
        return "retrieve_emails"

    def guidelines(self):
        return "Use to retrieve recent emails. Provide count (default 5). Returns subjects and content."

    def execute(self, count: int = 5):
        count = min(max(1, count), 20)
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, 993)
            mail.login(self.email, self.password)
            # ... fetch and process emails ...
            email_data = "Email 1: Subject, From, Content..."
            self._send_feedback(email_data)
            return f"Retrieved {count} emails with subjects and content", PrimitiveResult.SUCCESS
        except Exception as e:
            return f"Failed to retrieve emails: {str(e)}", PrimitiveResult.FAILURE
```

You can run this skill in an agent that can query it:

```python  theme={null}
from typing import List
from brain_client.agent_types import Agent

class EmailAssistant(Agent):
    @property
    def id(self) -> str:
        return "email_assistant"

    @property
    def display_name(self) -> str:
        return "Email Assistant"

    def get_skills(self) -> List[str]:
        return [
            "retrieve_emails"
        ]

    def get_prompt(self) -> str:
        return """
You are an email assistant. 
When the user sits in front of you, you should tell them what their last email is
"""
```

Below is the result of running it:

To learn more about the Skills SDK and go further:

<CardGroup cols={2}>
  <Card title="Skills" icon="wrench" href="/software/skills">
    See policy-defined and code-defined skills with interface references.
  </Card>

  <Card title="Advanced Development" icon="code" href="/software/advanced-development">
    Modify ROS2 packages, recompile, and take full control of MARS.
  </Card>
</CardGroup>


---

## Advanced Development

_Source: https://docs.innate.bot/software/advanced-development.md_

# Advanced Development

> Go deeper. Modify ROS2 nodes, recompile, visualize, and take full control of MARS.

MARS is fully open source. Every line of code running on the robot is yours to read, modify, and redeploy. This guide is for developers who want to go beyond the Agent/Skill layer and work directly with the lower-level systems.

## The edit → build → restart loop

This is your core workflow. Every change follows the same cycle:

<Steps>
  <Step title="Edit code">
    Modify any file in `~/innate-os/`. ROS2 packages live in `~/innate-os/ros2_ws/src/`.
  </Step>

  <Step title="Build">
    Build and restart in one command:

    ```bash  theme={null}
    innate build
    ```

    Or build just the package you changed:

    ```bash  theme={null}
    innate build maurice_arm
    ```
  </Step>

  <Step title="Verify">
    Attach to the tmux session and check your node is running:

    ```bash  theme={null}
    innate view
    ```
  </Step>
</Steps>

<Tip>
  For a full clean build:

  ```bash  theme={null}
  innate clean
  innate build
  ```
</Tip>

***

## Reading the tmux windows

Every ROS node runs inside a tmux session called `ros_nodes`. Each window has two panes running related nodes side by side.

```bash  theme={null}
innate view
```

Navigate with:

* `Ctrl+B` then `0`-`6` — switch windows
* `Ctrl+B` then `←` / `→` — switch panes
* `Ctrl+B` then `D` — detach (nodes keep running)

Here's what each window runs:

| Window | Name                | Left pane                          | Right pane                          |
| ------ | ------------------- | ---------------------------------- | ----------------------------------- |
| 0      | `app-bringup`       | App controller                     | Hardware bringup (UART, battery)    |
| 1      | `arm-recorder`      | Arm drivers + kinematics           | Manipulation recorder               |
| 2      | `brain-nav`         | Brain client (cloud connection)    | Navigation stack                    |
| 3      | `behaviors-inputs`  | Behavior server (skills execution) | Input manager                       |
| 4      | `cam-leader`        | Camera pipeline                    | UDP leader receiver (teleoperation) |
| 5      | `ik-logger`         | Inverse kinematics solver          | Telemetry logger                    |
| 6      | `training-uninavid` | On-device training node            | UninaVID vision model               |

If a node crashes, its pane shows the error. Fix the code and build the package.

***

## What you can modify

### Agents and skills (no build needed)

Files in `~/agents/` and `~/skills/` are pure Python. Edit, save, restart — no compilation.

```bash  theme={null}
innate service restart
```

### ROS2 packages (build required)

Everything in `~/innate-os/ros2_ws/src/` is a ROS2 package. After editing, build:

```bash  theme={null}
innate build <package_name>
```

Key packages to know:

| Package           | What it controls                            |
| ----------------- | ------------------------------------------- |
| `brain_client`    | Cloud agent connection, agent orchestration |
| `maurice_bringup` | Hardware init (UART, battery, LEDs)         |
| `maurice_arm`     | Arm drivers, kinematics, MoveIt2            |
| `maurice_nav`     | Nav2, SLAM, path planning                   |
| `maurice_cam`     | Camera pipeline (OAK-D, WebRTC)             |
| `maurice_control` | App control, UDP teleoperation              |
| `manipulation`    | Behavior server, policy execution           |

### Launch files

Launch files configure how nodes start. They live inside each package's `launch/` directory. Edit them to change parameters, remap topics, or add new nodes.

***

## Observability

You need to see what the robot sees. Two options.

### RViz (Linux)

If you're on a Linux machine on the same network, RViz plugs directly into the ROS2 topics and gives you the full visualization stack: TF frames, point clouds, camera feeds, navigation costmaps, arm trajectories.

Make sure Zenoh DDS discovery is configured so your machine can see the robot's topics.

### Foxglove (all platforms)

Not on Linux? Use [Foxglove](https://foxglove.dev/). It connects over WebSocket to a Foxglove Bridge running on MARS and lets you visualize all the same data from any browser.

See the dedicated [Foxglove Setup](/software/foxglove-setup) guide.

***

## Diagnostics

Run hardware diagnostics to check system health:

```bash  theme={null}
innate diag
```

Check the system status dashboard:

```bash  theme={null}
innate
```

This prints version, mode, ROS status, and DDS state at a glance.

***

## Boot sequence

Understanding what happens at power-on helps with debugging:

1. **systemd** starts `zenoh-router.service` (DDS discovery layer)
2. **systemd** starts `ros-app.service` which runs `launch_ros_in_tmux.sh`
3. The script creates a tmux session with 7 windows (14 ROS nodes)
4. After 20 seconds, the startup chime plays

All services are managed by systemd. View their status:

```bash  theme={null}
systemctl status ros-app.service
systemctl status zenoh-router.service
```

***

## Tips

* **Build only what changed.** `innate build maurice_arm` is faster than `innate build`.
* **Check logs in tmux.** Each pane scrolls. `Ctrl+B` then `[` enters scroll mode, `q` exits.
* **Use `ros2 topic echo`** to inspect live data: `ros2 topic echo /cmd_vel`.
* **Use `ros2 node list`** to verify nodes are alive after a restart.

***

## Reference

<CardGroup cols={2}>
  <Card title="Innate CLI" icon="terminal" href="/software/innate-cli">
    Every command, one page.
  </Card>

  <Card title="Foxglove Setup" icon="eye" href="/software/foxglove-setup">
    Browser-based ROS visualization.
  </Card>

  <Card title="ROS2 Topics" icon="diagram-project" href="/software/ros2/topics">
    All published topics on MARS.
  </Card>

  <Card title="ROS2 Debugging" icon="bug" href="/software/ros2/debugging">
    Debugging workflows.
  </Card>
</CardGroup>


---

## Innate CLI

_Source: https://docs.innate.bot/software/innate-cli.md_

# Innate CLI Reference

> Every command you need, on one page.

The `innate` CLI is your control panel. SSH into MARS and start typing.

<Tip>
  `in8` is a zsh alias for `innate`, available in any new shell.
</Tip>

## Default (no args)

| Command  | What it does                                                      |
| -------- | ----------------------------------------------------------------- |
| `innate` | Status dashboard — version, mode, ROS/DDS status, quick reference |

***

## Service management

Start, stop, and inspect all ROS nodes.

| Command                  | What it does                |
| ------------------------ | --------------------------- |
| `innate service start`   | Start all ROS nodes in tmux |
| `innate service stop`    | Kill the tmux session       |
| `innate service restart` | Stop + start                |
| `innate service view`    | Attach to the tmux session  |

### Top-level shortcuts

| Command          | Same as                  |
| ---------------- | ------------------------ |
| `innate view`    | `innate service view`    |
| `innate restart` | `innate service restart` |

***

## Build

Smart build that does the right thing automatically. If ROS nodes are running, it stops them, builds, and restarts them. If nodes aren't running, it just builds. If the build fails, nodes are not restarted.

| Command                  | What it does                                         |
| ------------------------ | ---------------------------------------------------- |
| `innate build`           | Build full workspace (stops/starts nodes if running) |
| `innate build pkg1 pkg2` | Build specific packages only                         |
| `innate clean`           | Remove `build/`, `install/`, `log/`                  |

### Examples

```bash  theme={null}
innate build maurice_arm       # build one package (restarts nodes if they're running)
innate build                   # build everything
innate clean && innate build   # full clean rebuild
```

***

## Diagnostics & updates

| Command                                 | What it does                                          |
| --------------------------------------- | ----------------------------------------------------- |
| `innate diag`                           | Hardware check (servos, PCB, lidar, cameras, speaker) |
| `innate update check [--dev]`           | Check for available updates                           |
| `innate update apply [version] [--dev]` | Apply updates (optionally pin a specific version)     |
| `innate update status`                  | Show version + service info                           |

<Note>
  See [Updates and Maintenance](/robots/mars/updates-and-maintenance) for details.
</Note>

***

## Quick reference card

```
innate                          → status dashboard
innate service start            → launch ROS nodes
innate service stop             → kill all nodes
innate service restart          → stop + start
innate service view             → attach to tmux
innate view                     → shortcut for above
innate restart                  → shortcut for above
innate build [pkg ...]          → build (stops/starts nodes if running)
innate clean                    → rm build/install/log
innate diag                     → hardware diagnostics
innate update check [--dev]     → check for updates
innate update apply [version] [--dev] → apply updates
innate update status            → version + service info
in8 ...                         → alias for innate
```

***

## Tmux navigation

When you run `innate view`, you're inside a tmux session. Here's how to move around:

| Keys                    | Action                                       |
| ----------------------- | -------------------------------------------- |
| `Ctrl+B` then `0`–`6`   | Switch to window 0–6                         |
| `Ctrl+B` then `←` / `→` | Switch between left/right panes              |
| `Ctrl+B` then `[`       | Enter scroll mode (navigate with arrow keys) |
| `q`                     | Exit scroll mode                             |
| `Ctrl+B` then `D`       | Detach from tmux (nodes keep running)        |

See [Advanced Development](/software/advanced-development#reading-the-tmux-windows) for a breakdown of what runs in each window.


---

## Foxglove Setup

_Source: https://docs.innate.bot/software/foxglove-setup.md_

# Foxglove Setup

> Visualize ROS2 topics from any machine using Foxglove.

Foxglove lets you see what your robot sees — camera feeds, LiDAR scans, navigation costmaps, TF frames — all from a browser. Works on macOS, Windows, and Linux.

## How it works

MARS runs a **Foxglove Bridge** node that exposes ROS2 topics over WebSocket. You connect to it from [Foxglove](https://foxglove.dev/) on your laptop.

```
MARS (ROS2 topics) → Foxglove Bridge (WebSocket :8765) → Your browser
```

***

## Setup

<Steps>
  <Step title="SSH into MARS">
    ```bash  theme={null}
    ssh jetson1@<YOUR-ROBOT-IP>
    ```
  </Step>

  <Step title="Install Foxglove Bridge (if not already installed)">
    ```bash  theme={null}
    sudo apt install ros-humble-foxglove-bridge
    ```
  </Step>

  <Step title="Start the bridge">
    ```bash  theme={null}
    ros2 launch foxglove_bridge foxglove_bridge_launch.xml
    ```

    The bridge listens on port `8765` by default.
  </Step>

  <Step title="Open Foxglove in your browser">
    Go to [app.foxglove.dev](https://app.foxglove.dev).

    Click **Open connection** → **Foxglove WebSocket** → enter:

    ```
    ws://<YOUR-ROBOT-IP>:8765
    ```
  </Step>

  <Step title="Add panels">
    Once connected, add visualization panels:

    * **Image** panel → select `/oak/rgb/image_raw` for the camera feed
    * **3D** panel → see TF frames, LiDAR, and navigation paths
    * **Plot** panel → graph any numeric topic over time
    * **Raw Messages** panel → inspect any topic's raw data
  </Step>
</Steps>

***

## Useful topics to visualize

| Topic                | Type          | What you see                   |
| -------------------- | ------------- | ------------------------------ |
| `/oak/rgb/image_raw` | Image         | Main camera feed               |
| `/scan`              | LaserScan     | LiDAR sweep                    |
| `/odom`              | Odometry      | Robot position and velocity    |
| `/cmd_vel`           | Twist         | Velocity commands being sent   |
| `/map`               | OccupancyGrid | SLAM map                       |
| `/battery_state`     | BatteryState  | Battery voltage and percentage |
| `/tf`                | TF            | All coordinate frames          |

***

## RViz alternative (Linux only)

If you're on a Linux machine with ROS2 Humble installed, you can use RViz directly. It connects to MARS over Zenoh DDS — no bridge needed.

Make sure your machine is on the same network and Zenoh discovery can reach the robot. Then:

```bash  theme={null}
source /opt/ros/humble/setup.bash
rviz2
```

Add displays for the topics you care about. RViz gives you the most complete visualization experience but requires a native Linux + ROS2 setup.

***

## Troubleshooting

<AccordionGroup>
  <Accordion title="Can't connect to WebSocket">
    * Verify MARS and your laptop are on the same network.
    * Check the bridge is running: `ros2 node list | grep foxglove`.
    * Try the IP address directly instead of `.local` hostname.
    * Make sure port `8765` isn't blocked by a firewall.
  </Accordion>

  <Accordion title="No topics showing up">
    * The bridge only exposes topics that are actively published. Make sure ROS nodes are running: `innate view`.
    * Try `ros2 topic list` on the robot to confirm topics exist.
  </Accordion>

  <Accordion title="High latency on camera feed">
    * Image topics are bandwidth-heavy. Use a wired Ethernet connection for the best experience.
    * In Foxglove, reduce the image panel's update rate or use compressed image topics if available.
  </Accordion>
</AccordionGroup>


---

## Inputs

_Source: https://docs.innate.bot/software/inputs.md_

# Inputs

Inputs let you send additional data asynchronously to BASIC while an agent is running.

They are useful when integrating external signals such as added sensors (for example directional microphone or air-quality sensor), network events (for example incoming emails or webhook alerts), and internal robot status events. The most important part is that an input can send live feedback to BASIC while the agent is executing.

## Minimal input example (stripped down)

```python  theme={null}
import threading
from brain_client.input_types import InputDevice

class AlertsInput(InputDevice):
    def __init__(self):
        super().__init__()
        self._stop = threading.Event()

    @property
    def name(self) -> str:
        return "alerts_input"

    def on_open(self):
        self._stop.clear()

        def loop():
            while not self._stop.is_set():
                events = self._poll_events()  # your sensor/API hook
                for event_text in events:
                    # Async feedback to BASIC during agent execution
                    self.send_data(event_text, data_type="chat_in")
                self._stop.wait(1.0)

        threading.Thread(target=loop, daemon=True).start()

    def on_close(self):
        self._stop.set()

    def _poll_events(self):
        return []
```

## Attach it to an agent

```python  theme={null}
def get_inputs(self) -> list[str]:
    return ["alerts_input"]
```

When this agent starts, `on_open()` is called and BASIC begins receiving these asynchronous updates.

For more details:

* [Definition](/software/inputs/definition)
* [Example: Microphone](/software/inputs/example-microphone)


---
