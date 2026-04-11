# Hackathon & Getting Started

> Read this first. RoboHacks-specific setup, the quick start for powering on MARS, and example use cases to understand what the robot can do.

> Source: https://docs.innate.bot · mirrored 2026-04-11 · MARS OS 0.4.5

## Contents

**Intro to MARS**
- [Intro to MARS](#intro-to-mars)

**Hackathon — RoboHacks**
- [RoboHacks Hackathon](#robohacks-hackathon)

**Get Started**
- [Quick Start](#quick-start)
- [Example Use Cases](#example-use-cases)

---

# Intro to MARS

## Intro to MARS

_Source: https://docs.innate.bot/index.md_

# Intro to MARS

<img src="https://mintcdn.com/innateinc/nu2qSXxGbvX3rZfh/images/home-hero.png?fit=max&auto=format&n=nu2qSXxGbvX3rZfh&q=85&s=90aec90764c2f156ef8b97174f2d3dd8" alt="" width="2972" height="876" data-path="images/home-hero.png" />

MARS is an open-source physical AI Agent Platform built by Innate. It can talk and listen to you, navigate around, and pursue tasks with its arm. MARS is the first robot tailored to create agentic applications for your home.

<CardGroup cols={3}>
  <Card title="Latest MARS OS Versions">
    As of **April 2026**:

    * **MARS OS:** `0.4.5`
    * **Cloud Agent:** `0.2.1`
    * **Innate Controller App:** `1.1.0`
  </Card>

  <Card title="Chat with the Innate Team">
    Questions, feedback, or debugging help?

    Join our Discord: [discord.com/invite/KtkyT97kc7](https://discord.com/invite/KtkyT97kc7)
  </Card>

  <Card title="GitHub Repos" icon="github" href="https://github.com/innate-inc">
    OSS repositories are currently in closed beta.

    Reach out on [Discord](https://discord.com/invite/KtkyT97kc7) to request access.
  </Card>
</CardGroup>

<img src="https://mintcdn.com/innateinc/nu2qSXxGbvX3rZfh/images/mars-face.png?fit=max&auto=format&n=nu2qSXxGbvX3rZfh&q=85&s=c5a8423719877e1a915be33a152ef594" alt="MARS face" style={{ width: "50%", display: "block", margin: "0 auto" }} width="1570" height="784" data-path="images/mars-face.png" />

***

## Get Started

Start building with MARS.

<CardGroup cols={3}>
  <Card title="Quick Start" icon="rocket" href="/get-started/mars-quick-start">
    Get your robot up and running. Connect your MARS, control it with the app,
    and run your first pre-built agent.
  </Card>

  <Card title="Examples" icon="camera" href="/get-started/mars-example-use-cases">
    Watch MARS in action with security patrol, sock cleaning, chess playing, and
    more real-world demos.
  </Card>

  <Card title="MARS Capabilities" icon="microchip" href="/robots/mars/capabilities">
    Explore what MARS can do across mobility, manipulation, sensing, memory, and
    autonomous operation modes.
  </Card>
</CardGroup>


---

# Hackathon — RoboHacks

## RoboHacks Hackathon

_Source: https://docs.innate.bot/hackathon/robohacks.md_

# RoboHacks Hackathon

> Everything you need to get started at the Innate RoboHacks hackathon.

Welcome to **RoboHacks**, the Innate hackathon! This page collects the resources, repos, and setup instructions you need to hit the ground running.

## Connect to the hackathon WiFi

All robots have been pre-configured to connect to the **Robot Wifi** network at YC. Your laptop and phone must be on the same network to connect to your MARS.

<Info>
  The WiFi password is pinned in [Discord](https://discord.com/invite/KtkyT97kc7). Make sure you are connected before attempting to SSH or use the Innate Controller App.
</Info>

## Update your robot first

<Warning>
  Run this **before** you start hacking. Your robot must be on the latest OS to
  work with the hackathon tooling.
</Warning>

<Steps>
  <Step title="Apply the hackathon dev release">
    Once the stable update finishes, apply the hackathon-specific release candidate:

    ```bash  theme={null}
    innate update --dev apply 0.5.0-rc10
    ```
  </Step>
</Steps>

## Hackathon resources repository

The **[robohacks-utils](https://github.com/innate-inc/robohacks-utils)** repo is the central hub for hackathon-specific tooling and assets. Clone it to get started:

```bash  theme={null}
git clone https://github.com/innate-inc/robohacks-utils.git
```

Inside you will find:

* **HDF5 → LeRobot converter** (`hdf5_lerobot.py`) — convert recorded HDF5 datasets into the [LeRobot](https://github.com/huggingface/lerobot) format for policy training. Install dependencies with `pip install -r requirements.txt`.
* **STEP files** (`STEP/`) — CAD models of the MARS robot for hardware modifications or custom attachments.
* **Latest Android APK** — attached to the [repo releases](https://github.com/innate-inc/robohacks-utils/releases/download/android-app-rc1/android-app.apk). The iOS app is available on [TestFlight](https://testflight.apple.com/join/YeChe4A7). Leader Arm operation only works on Android. We have some Android phones to share if no one on your team has one.

## Innate OS authentication

To run Innate OS or the simulator on your own machine with access to the voice, agent, and training servers, you need an **Innate service key**.

| Track           | How to get your key                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Robot track** | Look at `~/innate-os/.env` on your robot and copy `INNATE_SERVICE_KEY`. One key per team.                                            |
| **Sim track**   | Ask in the **#innate-cloud-infra** channel on [Discord](https://discord.com/invite/KtkyT97kc7). One key per team — you can share it. |

## Sim track — MARS URDF

If you are on the simulation track, you must integrate the MARS URDF into your submissions. You can find it here:

<Card title="MARS URDF (maurice_sim)" icon="cube" href="https://github.com/innate-inc/innate-os/tree/main/ros2_ws/src/maurice_bot/maurice_sim">
  The simulation description package for the MARS robot, including URDF, meshes,
  and launch files.
</Card>

## Training runs

Track your cloud training runs on Weights & Biases:

<Card title="W&B Dashboard" icon="chart-line" href="https://wandb.ai/vignesh-anand/act-simple/table">
  View training metrics, loss curves, and run comparisons for the ACT policy.
</Card>

***

## Open-source repos & example projects

Innate OS is fully open source. Use these repos and example projects as a starting point for your hack.

### Innate OS

The full operating system that runs on MARS. Explore it to understand how the robot works under the hood — ROS2 nodes, launch files, drivers, and more.

<Card title="innate-os" icon="github" href="https://github.com/innate-inc/innate-os">
  The open-source ROS2-based operating system for MARS.
</Card>

### GraspGen — arbitrary object grasping

GraspGen is a project built on top of Innate OS that uses the depth camera and NVIDIA's GraspGen model to grasp arbitrary objects. It is a great reference for how to:

* Access core robot interfaces through **ROS Bridge** (port 9090)
* Control the robot over **WebSockets**

<Card title="GraspGen" icon="hand" href="https://github.com/innate-inc/GraspGen">
  Depth-camera-based arbitrary object grasper built on Innate OS and NVIDIA
  GraspGen.
</Card>

### Vision-Language Navigation (UniNaVid)

A remote inference server using the **UniNaVid** model for vision-language navigation. The server processes navigation commands with a large VLM, and the client inside Innate OS executes the resulting movements.

* **Server** — remote inference endpoint for navigation commands.
* **Client** — the ROS2 package inside Innate OS that calls the server and executes movement primitives. You can find it at [`ros2_ws/src/cloud/innate_uninavid/`](https://github.com/innate-inc/innate-os/tree/main/ros2_ws/src/cloud/innate_uninavid), along with a corresponding skill at [`skills/navigate_with_vision.py`](https://github.com/innate-inc/innate-os/tree/main/skills/navigate_with_vision.py).

***

## Useful docs pages

<CardGroup cols={2}>
  <Card title="Quick Start" icon="rocket" href="/get-started/mars-quick-start">
    Power up, connect, and control your MARS in minutes.
  </Card>

  <Card title="Development Setup" icon="terminal" href="/software/development-setup">
    SSH in, edit code, restart — the full dev loop.
  </Card>

  <Card title="Agent SDK" icon="robot" href="/software/overview">
    Build agents, skills, and inputs on top of Innate OS.
  </Card>

  <Card title="Manipulation & Training" icon="dumbbell" href="/training/overview">
    Collect data, train policies, and deploy arm skills.
  </Card>
</CardGroup>

## Need help?

Join the Innate Discord for real-time support from the team and other hackers:

<Card title="Discord" icon="discord" href="https://discord.com/invite/KtkyT97kc7">
  Ask questions, share progress, and get debugging help.
</Card>


---

# Get Started

## Quick Start

_Source: https://docs.innate.bot/get-started/mars-quick-start.md_

# Quick Start

Learn how to control MARS with your phone and the controller arm, make it navigate and talk, and trigger autonomous agents & skills made by others

This page describes the experience of receiving your MARS robot for the first time and running it.

If you want a more technical introduction to our SDK and the underlying ROS2 system, please go to:

<Card title="MARS Quick Development" icon="terminal" href="/software/mars-quick-development">
  Go deeper on SDK usage, ROS2, and building your first custom agent.
</Card>

## Prerequisites

* A MARS robot from Innate, configured with your service key.
* The Innate Controller app, downloaded from one of the stores:
  [Android](https://cdn.innate.bot/innate-app-latest.apk) or
  [iOS](https://testflight.apple.com/join/YeChe4A7).

## A quick overview

<iframe width="100%" height="420" src="https://www.youtube.com/embed/_Cw5fGa8i3s" title="MARS quick overview" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

## Powering up and connecting to MARS

<Steps>
  <Step title="Place and power">
    Put MARS on the floor and plug in the battery. The robot powers on automatically.
  </Step>

  <Step title="Install/open the app">
    Use the Innate Controller App on your phone.

    <div style={{ display: "flex", gap: "16px", alignItems: "center", flexWrap: "wrap", marginTop: "8px" }}>
      <a href="https://cdn.innate.bot/innate-app-latest.apk" style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
        <img src="https://mintcdn.com/innateinc/y6xOPci6RdWqfjEK/images/logos/stores/google-play.svg?fit=max&auto=format&n=y6xOPci6RdWqfjEK&q=85&s=9225afe01fa207676fee3e936adc009e" alt="Google Play" width="18" height="18" className="block dark:hidden" data-path="images/logos/stores/google-play.svg" />

        <img src="https://mintcdn.com/innateinc/y6xOPci6RdWqfjEK/images/logos/stores/google-play-dark.svg?fit=max&auto=format&n=y6xOPci6RdWqfjEK&q=85&s=a5494c88237d7f5962faf69fb6f3b73d" alt="Google Play" width="18" height="18" className="hidden dark:block" data-path="images/logos/stores/google-play-dark.svg" />

        <span>Android</span>
      </a>

      <a href="https://testflight.apple.com/join/YeChe4A7" style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
        <img src="https://mintcdn.com/innateinc/y6xOPci6RdWqfjEK/images/logos/stores/app-store.svg?fit=max&auto=format&n=y6xOPci6RdWqfjEK&q=85&s=7716f8b329fdb7bda7046790e58395fe" alt="App Store" width="18" height="18" className="block dark:hidden" data-path="images/logos/stores/app-store.svg" />

        <img src="https://mintcdn.com/innateinc/y6xOPci6RdWqfjEK/images/logos/stores/app-store-dark.svg?fit=max&auto=format&n=y6xOPci6RdWqfjEK&q=85&s=bf915d7cdf29f2efe3f38e60df8b9206" alt="App Store" width="18" height="18" className="hidden dark:block" data-path="images/logos/stores/app-store-dark.svg" />

        <span>iOS</span>
      </a>
    </div>
  </Step>

  <Step title="Connect to your robot">
    Follow the app onboarding flow and connect to your MARS.
  </Step>
</Steps>

<iframe width="100%" height="420" src="https://www.youtube.com/embed/lbwYFGgOh-g" title="Powering up and connecting to MARS" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

## Create your first map

Innate robots have spatial memory, and mapping starts automatically after you connect if no map exists yet.

If you want to create a **new** map later, use the Mapping screen:

<div style={{ display: "flex", gap: "24px", alignItems: "flex-start", flexWrap: "wrap" }}>
  <div style={{ flex: "1 1 420px", minWidth: "300px" }}>
    <Steps>
      <Step title="Open Mapping tab">
        In the app, go to **Configuration** -> **Mapping**.
      </Step>

      <Step title="Create a new map">
        Press **Create New Map** (or the add button) to begin mapping.
      </Step>

      <Step title="Drive and scan">
        Drive around your space and watch the map build in real time.
      </Step>
    </Steps>
  </div>

  <div style={{ flex: "0 1 340px", minWidth: "260px" }}>
    <iframe width="100%" height="560" src="https://www.youtube.com/embed/DiHl1VKuVJ8" title="Create your first MARS map" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />
  </div>
</div>

## Experience the phone control

Once connected, you can verify that MARS is properly running by controling the robot straight through the app.

<Steps>
  <Step title="Open Manual Control">
    Go to the **Manual Control** screen in the app.
  </Step>

  <Step title="Drive and move head">
    Use the joystick for base motion and the slider for head movement.
  </Step>

  <Step title="Test leader arm">
    Plug in the controller arm and toggle arm control to verify MARS mirrors your motion.
  </Step>
</Steps>

<iframe width="100%" height="420" src="https://www.youtube.com/embed/BhP6Z0h69Ho" title="Phone control demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

## Talk to MARS for the first time

MARS can run BASIC, our embodied agent that allows the robot to act in real-time and decide what to do based on what it sees and hears.

Put MARS on a table, in front of you, go to "Agentic" on the app, and ask it what it sees. You should start seeing its thoughts and answers appear in the chat.

<iframe width="100%" height="420" src="https://www.youtube.com/embed/GRWwaOIKmec" title="Talk to MARS demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

## Make MARS navigate

When running BASIC, MARS can navigate. On the agentic screen, ask him things such as "move forward 1m", or "go to the fridge" if the fridge is in sight.

You can also try more complex requests such as "explore until you see a human".

<iframe width="100%" height="420" src="https://www.youtube.com/embed/EsLdogaaA90" title="Navigation demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

## Use an autonomous arm AI skill

<div style={{ display: "flex", gap: "24px", alignItems: "flex-start", flexWrap: "wrap" }}>
  <div style={{ flex: "1 1 420px", minWidth: "300px" }}>
    Innate robots can use "skills" to perform actions in the physical world or the digital world.

    <br />

    <br />

    You can observe which ones are installed by going in the app to Skills (in the tab bar, middle icon) and looking at the list of physical and digital skills installed.

    <br />

    <br />

    To **run an arm skill**, go to Home -> **Manual Control**, and **select a skill in the dropdown.**

    <br />

    <br />

    You can also run an parametric skill (needs input parameters from you) by going in the **Skills tab, selecting "Digital",** picking up a skill, input parameters then press "Execute".
  </div>

  <div style={{ flex: "0 1 320px", minWidth: "260px", marginLeft: "auto" }}>
    <iframe width="100%" height="560" src="https://www.youtube.com/embed/QedY3xoE6A8" title="Triggering an end-to-end skill from the app" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />
  </div>
</div>

## Use an existing agent

BASIC allows to run programs we call "agents" that determine the robot's purpose and abilities. On the app, you can see which ones are already installed.

Examples that come pre-installed:

* **Demo Agent:** An agent that is proactively talking with you, and following your gaze

* **Chess Agent:** An agent to play chess with its arm with you if you put MARS in front of a chess board

* **Security Guard:** An agent that moves around and warns you if it sees someone

* *More coming soon...*

You can also create your own agent:

<Card title="Anatomy of an Agent" icon="robot" href="/software/agents/definitions">
  Learn how an agent is structured and how to define prompts and attached skills.
</Card>

## Congrats, you can control your robot!

Now you know how to run basic controls of the robot from the app.

Next up: Create your first agent and train your first manipulation model, to run them autonomously!

<Card title="MARS Quick Development" icon="terminal" href="/software/mars-quick-development">
  Continue with SDK setup, code-defined skills, and your first custom agent.
</Card>


---

## Example Use Cases

_Source: https://docs.innate.bot/get-started/mars-example-use-cases.md_

# Examples

As an extensible general-purpose robot, MARS can be used for a wide array of use-cases, which can be further increased with additional sensors and effectors.

All the examples below are possible autonomously — some of them might require more data than we have collected so far.

* A Desk Personal Productivity companion that hits you whenever you look at your phone or when it sees you are not working on your screen.

* An Elderly Companion that takes notes during the day of what your grand-parents do and can remind them to take their medicine.

* A floor decluttering robot that takes legos and trash off the floor and in a particular bin in another room.

* A Chess Playing Robot that roasts you while you play (or adopts a different character depending on the user).

* A Security Robot that can open doors and explore the place, and call 911 if it sees someone.

* A food serving robot that can put food in your plate when you show one in front of it.

* A concierge robot that gives indication to visitors, flyers, and drives them to destination.

## Autonomous demos

The videos below show real autonomous deployments of MARS in different situations. All were accomplished with training the arm and running the BASIC agent.

#### Playing Chess

<iframe width="100%" height="420" src="https://www.youtube.com/embed/P6QLCOCABs0" title="Playing chess demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

#### Picking up socks to clean the room

<iframe width="100%" height="420" src="https://www.youtube.com/embed/q8Xb5auUBIs" title="Picking up socks demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

#### Giving tools for work

<iframe width="100%" height="420" src="https://www.youtube.com/embed/_4Qs5WTOMfo" title="Giving tools demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

#### Patroling the house with opening doors

<iframe width="100%" height="420" src="https://www.youtube.com/embed/b7cNKEcER24" title="Patrolling the house demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />


---
