# Innate MARS — Consolidated Documentation

> Source: https://docs.innate.bot — mirrored locally on 2026-04-11 for offline hackathon reference.  
> Covers MARS OS 0.4.5, Cloud Agent 0.2.1, Innate Controller App 1.1.0 (as of April 2026).

> This file is the verbatim concatenation of every page listed in https://docs.innate.bot/llms.txt
> (minus the repeated Mintlify agent-feedback boilerplate and docs-index reminder that appears on every page).
> To report doc issues upstream, POST to `https://docs.innate.bot/_mintlify/feedback/innateinc/agent-feedback`
> with body `{ "path": "/page-path", "feedback": "..." }`.

## Table of Contents

- [Introduction](#introduction)
  - [Intro to MARS](#intro-to-mars)
- [Get Started](#get-started)
  - [Quick Start](#quick-start)
  - [Example Use Cases](#example-use-cases)
- [Hackathon — RoboHacks](#hackathon-robohacks)
  - [RoboHacks Hackathon](#robohacks-hackathon)
- [Robot Hardware (MARS)](#robot-hardware-mars)
  - [MARS Overview & Hardware](#mars-overview-hardware)
  - [Capabilities](#capabilities)
  - [Calibration](#calibration)
  - [Charging & Battery](#charging-battery)
  - [Control & Connectivity](#control-connectivity)
  - [Critical Fixes](#critical-fixes)
  - [Extending MARS](#extending-mars)
  - [FAQ](#faq)
  - [Troubleshooting](#troubleshooting)
  - [Updates & Maintenance](#updates-maintenance)
- [Software — Overview & Setup](#software-overview-setup)
  - [Overview](#overview)
  - [BASIC Agent](#basic-agent)
  - [Development Setup](#development-setup)
  - [MARS Quick Development](#mars-quick-development)
  - [Advanced Development](#advanced-development)
  - [Innate CLI](#innate-cli)
  - [Foxglove Setup](#foxglove-setup)
  - [Inputs](#inputs)
- [Software — Agents](#software-agents)
  - [Agents Overview](#agents-overview)
  - [Agent Definitions](#agent-definitions)
  - [Starting an Agent](#starting-an-agent)
  - [Agent Examples](#agent-examples)
  - [Chess Agent (Beta)](#chess-agent-beta)
  - [Chessboard Calibration (Beta)](#chessboard-calibration-beta)
- [Software — Skills](#software-skills)
  - [Skills Overview](#skills-overview)
  - [Manual Triggering](#manual-triggering)
  - [Policy-Defined Skills](#policy-defined-skills)
  - [Code-Defined Skills](#code-defined-skills)
  - [Body Control Interfaces](#body-control-interfaces)
  - [Navigation Interfaces](#navigation-interfaces)
  - [Robot State](#robot-state)
  - [Digital Skills](#digital-skills)
  - [Physical Skill Examples](#physical-skill-examples)
- [Software — ROS2](#software-ros2)
  - [ROS2 Core](#ros2-core)
  - [Topics](#topics)
  - [Services](#services)
  - [Actions](#actions)
  - [Navigation Stack](#navigation-stack)
  - [Manipulation Stack](#manipulation-stack)
  - [Debugging](#debugging)
- [Training & Policy Development](#training-policy-development)
  - [Training Overview](#training-overview)
  - [Data Collection](#data-collection)
  - [Dataset Format](#dataset-format)
  - [Train ACT Policy](#train-act-policy)
  - [Training Manager](#training-manager)
  - [Evaluate](#evaluate)
  - [Deploy Trained Skill](#deploy-trained-skill)
- [Support](#support)
  - [Contact / Discord](#contact-discord)

---

# Introduction

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

# Robot Hardware (MARS)

## MARS Overview & Hardware

_Source: https://docs.innate.bot/robots/mars.md_

# Overview & Hardware

<img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/mars-overview.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=cb93ef7366c1b403bfe90780497e3b14" alt="" width="2304" height="1368" data-path="images/main/robots/mars-overview.png" />

MARS is a compact mobile manipulator with onboard AI compute, designed as a complete platform for building and sharing real-world robot applications.

## Hardware at a glance

### Sensors

MARS combines complementary perception sources: a forward-facing RGBD camera for scene depth, a gripper-mounted RGB camera for close manipulation, and a 2D LiDAR for localization.

#### Camera matrix

| Spec                   | Forward-Facing RGBD Camera                   | Gripper-Mounted RGB Camera          |
| ---------------------- | -------------------------------------------- | ----------------------------------- |
| Camera type            | Stereo RGBD                                  | RGB                                 |
| Diagonal field of view | 150°                                         | 160°                                |
| Effective range        | 40 cm to 6 m                                 | Close-range manipulation            |
| Depth support          | Yes                                          | No                                  |
| Depth accuracy         | \<2% up to 3.5 m, \<4% to 6.5 m, \<6% to 9 m | N/A                                 |
| Resolution             | N/A                                          | 2MP (1920x1080)                     |
| Frame rate             | N/A                                          | 30 FPS                              |
| Primary role           | Navigation and scene perception              | Visual servoing and grasp alignment |

#### 2D LiDAR

| Property            | Value               |
| ------------------- | ------------------- |
| Coverage            | 360°                |
| Range               | 0.15 m to 6 m       |
| Angular resolution  | \<=1°               |
| Distance resolution | \<0.5 mm            |
| Scan rate           | 10 Hz               |
| Primary use         | SLAM and navigation |

<Card title="ROS2 Topics Reference" href="/software/ros2/topics">
  LiDAR data is exposed on `/scan` as `sensor_msgs/LaserScan` (RPLidar stack).
</Card>

#### Custom sensors

MARS provides two powered USB 3.0 ports for additional sensors/peripherals.

| Port property          | Value                     |
| ---------------------- | ------------------------- |
| USB ports              | 2x USB 3.0                |
| Power output           | 1.2 A per port            |
| Data rate              | Up to 5 Gbps              |
| Hot swap               | Supported                 |
| Backward compatibility | USB 2.0 devices supported |

### Arm

#### Specifications

| Property      | Value                      |
| ------------- | -------------------------- |
| Reach         | 40 cm                      |
| Repeatability | 2 mm                       |
| Payload       | 250 g at maximum extension |

#### Actuators

| Qty | Actuator                  | Model            | Link                                                             |
| --- | ------------------------- | ---------------- | ---------------------------------------------------------------- |
| 2   | Dynamixel XL430 (Robotis) | `XL430-W250-T`   | [Product Page](https://www.robotis.us/dynamixel-xl430-w250-t/)   |
| 1   | Dynamixel XC430 (Robotis) | `XC430-T240BB-T` | [Product Page](https://www.robotis.us/dynamixel-xc430-t240bb-t/) |
| 4   | Dynamixel XL330 (Robotis) | `XL330-M288`     | [Product Page](https://www.robotis.us/dynamixel-xl330-m288-t/)   |

These actuators were chosen for robustness and repeatability. The arm can reliably perform tasks such as chess manipulation (see [Examples](/get-started/mars-example-use-cases)).

### Onboard Computer

MARS ships with a [Jetson Orin Nano Super 8GB Development Kit](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/).

<img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/mars/onboard-computer.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=442b38c0ae7358eb8525f50a9a6f2c5e" alt="" width="679" height="568" data-path="images/main/robots/mars/onboard-computer.png" />

| Component      | Specification                                                       |
| -------------- | ------------------------------------------------------------------- |
| AI performance | Up to 67 TOPS (sparse INT8)                                         |
| GPU            | NVIDIA Ampere architecture with 1024 CUDA cores and 32 Tensor cores |
| CPU            | 6-core ARM Cortex-A78AE v8 (64-bit)                                 |
| Memory         | 8 GB LPDDR5                                                         |
| Storage        | 1 TB SSD (integrated by Innate) + 32 GB microSD (for OS)            |
| Dev kit base   | Jetson Orin Nano Super module and reference carrier board           |

Innate also exposes two additional USB ports for user extensions after core system wiring.

## Platform details

MARS is delivered assembled and calibrated so you can start quickly, while still being open and mod-friendly for deeper customization.

You can buy an assembled MARS and access the open hardware/software repository:

<CardGroup cols={2}>
  <Card title="Innate Website" href="https://innate.bot/">
    Buy assembled MARS units and find product information.
  </Card>

  <Card title="MARS Repository" href="https://innate.bot/mars_repo">
    Open-source hardware and software repository.
  </Card>
</CardGroup>


---

## Capabilities

_Source: https://docs.innate.bot/robots/mars/capabilities.md_

# Capabilities

Core autonomous behavior on MARS is split across navigation, manipulation, and interaction.

## Navigation

MARS supports multiple navigation modes through the Innate Controller App.

<CardGroup cols={3}>
  <Card title="Navigation">
    Uses a pre-built map and LiDAR localization so MARS knows where it is and can place memories spatially.
  </Card>

  <Card title="Mapfree">
    Avoids obstacles using onboard sensing only, without pre-built map localization or mapping.
  </Card>

  <Card title="Mapping">
    Dedicated mode to create and save a new map for later navigation.
  </Card>
</CardGroup>

### Navigation mode

Navigation mode runs on a saved map and localizes with LiDAR. It is the mode to use when you want reliable repeatable paths and spatial memory tied to places in the environment.

### Mapfree mode

Mapfree mode uses the local costmap from onboard sensors and does not require a pre-built map. It is best for fast deployment in new environments, dynamic spaces, simple point-to-point tasks, and outdoor scenarios.

### Mapping mode

<Steps>
  <Step title="Open the Innate Controller App">
    Start from the app home screen.
  </Step>

  <Step title="Go to Configuration -> Mapping">
    Open the mapping configuration screen.
  </Step>

  <Step title="Select Create New Map">
    Start a fresh map for the current environment.
  </Step>

  <Step title="Drive through the environment">
    Move MARS across rooms, transitions, and key landmarks.
  </Step>

  <Step title="Save the map">
    Save once coverage looks complete.
  </Step>
</Steps>

During mapping, keep the arm in a safe resting position, drive slowly for cleaner map quality, and cover corners and doorways.

### For developers

Navigation mode is published on `/nav/current_mode` with values `mapfree`, `mapping`, and `navigation`.

<CardGroup cols={3}>
  <Card title="ROS2 Topics" href="/software/ros2/topics">
    Live streams including `/nav/current_mode`, LiDAR, and state telemetry.
  </Card>

  <Card title="ROS2 Services" href="/software/ros2/services">
    Request/response interfaces for mode and map operations.
  </Card>

  <Card title="ROS2 Actions" href="/software/ros2/actions">
    Long-running goals with feedback and cancellation.
  </Card>
</CardGroup>

## Manipulation

MARS supports two manipulation methods:

1. Standard CV + code-defined skills: use explicit logic and perception pipelines for deterministic task behavior.
2. End-to-end AI policies: train manipulation skills from demonstrations and deploy the trained policy on robot.

<CardGroup cols={2}>
  <Card title="Code + CV Manipulation" href="/software/skills/code-defined-skills">
    Build manipulation behaviors with code-defined skills and robot interfaces.
  </Card>

  <Card title="End-to-End AI Manipulation" href="/training/overview">
    Use foundation models for mobile manipulation with MARS.
  </Card>
</CardGroup>

## Interaction

MARS can interact through movement, listening, and speaking.

<CardGroup cols={3}>
  <Card title="Head Movement" href="/software/skills/code-defined-skills/body-control-interfaces">
    Move and orient the head for active sensing and expressive behavior.
  </Card>

  <Card title="Listening" href="/software/inputs">
    Receive voice and audio context through onboard sensing and input channels.
  </Card>

  <Card title="Speaking" href="/software/basic">
    Speak responses and status naturally while BASIC is running.
  </Card>
</CardGroup>


---

## Calibration

_Source: https://docs.innate.bot/robots/mars/calibration.md_

# Calibration

Calibrate stereo depth to ensure stable obstacle avoidance and navigation behavior.

MARS uses stereo depth for navigation and obstacle avoidance. Because cameras vary slightly across units, each robot must be calibrated.

<Frame caption="How MARS auto-calibrates stereo depth">
  <iframe width="100%" height="420" src="https://www.youtube.com/embed/V-20kHm7PHw" title="Self-calibrating depth camera" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />
</Frame>

If depth calibration is missing (or removed), navigation automatically falls back to non-depth mode. This can help if you suspect depth calibration is hurting navigation quality.

Run calibration:

* After first setup
* After major OS updates that include depth changes
* Any time depth readings appear unstable

## 1) Prepare the calibration board

Download and print:

* [Calibration board PDF](https://github.com/innate-inc/web-docs/blob/main/.gitbook/assets/mars-calibration-board.pdf)

<Frame caption="Print this board at 100% scale.">
  <img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/mars/mars-stereo-calibration-board.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=b56408fcd8ecb9ac1b37a8684c9ee578" width="525" height="406" data-path="images/main/robots/mars/mars-stereo-calibration-board.png" />
</Frame>

Setup notes:

* Print at **100% scale** (no fit-to-page scaling)
* Mount it flat on a letter-sized cardboard backing
* Do not cover checker squares or markers
* Flatness matters more than perfect edge trimming

## 2) Start calibration from the app

<Steps>
  <Step title="Open the Innate Controller App">
    Make sure your phone is connected to the same robot session.
  </Step>

  <Step title="Go to Configuration -> Depth and tap Start calibration">
    Use the **Configuration** tab, open **Depth**, then start calibration.

    <div className="calibration-app-screens">
      <Frame caption="Depth screen">
        <img src="https://mintcdn.com/innateinc/7R5QH0viwWhXaMEa/images/main/robots/mars/depth-calibration-start-screen.png?fit=max&auto=format&n=7R5QH0viwWhXaMEa&q=85&s=12d7541e1c1542058374434048cd8277" width="960" height="2142" data-path="images/main/robots/mars/depth-calibration-start-screen.png" />
      </Frame>

      <Frame caption="Before You Start screen">
        <img src="https://mintcdn.com/innateinc/7R5QH0viwWhXaMEa/images/main/robots/mars/depth-calibration-before-start-screen.png?fit=max&auto=format&n=7R5QH0viwWhXaMEa&q=85&s=9f5835cb705a8ce0d5d7652207943f69" width="960" height="2142" data-path="images/main/robots/mars/depth-calibration-before-start-screen.png" />
      </Frame>
    </div>
  </Step>

  <Step title="Place the board when MARS raises its hand">
    Place the board in front of the hand with the pattern facing the robot head, then hold steady until MARS grabs it.
  </Step>
</Steps>

## 3) Let calibration complete

* Stay clear while MARS runs the sequence
* Wait for completion status in the app
* If it fails, repeat with better board flatness and stability

After completion, run **Configuration** -> **Depth** -> **Check depth** before normal navigation.


---

## Charging & Battery

_Source: https://docs.innate.bot/robots/mars/charging-battery.md_

# Charging the Battery

Charge your battery carefully. Improper charging can be dangerous.

Follow the instructions in the video to make sure you don't encounter any issues or endanger yourself.

<iframe width="100%" height="420" src="https://www.youtube.com/embed/SnGpyMkS0WM" title="Charging the battery guide" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />

## What you need

Use the charger provided with your robot. It includes a balancing cable that fits your battery's white balancing connector into the `3S` port.

## How to charge

<Steps>
  <Step title="Connect battery and balancing cable">
    Plug the charger cable into the battery as shown in the video, including the white balancing connector.
  </Step>

  <Step title="Check battery voltage">
    Confirm the displayed voltage is between **10.5V and 12.6V**.
  </Step>

  <Step title="Set charger mode">
    Set battery type to **LiPo** and number of cells to **3S**.
  </Step>

  <Step title="Start charging">
    Press and hold **Enter** until prompted, then confirm to begin charging.
  </Step>

  <Step title="Monitor during charge">
    Keep voltage in the safe range (**10.5V to 12.6V**) while charging.
  </Step>
</Steps>

## Important warning

**Do not charge the battery if the white balancing connector is not plugged in.** This connector balances the cells and should NOT be disconnected before charging.

If your battery pack shows a bump, the battery is unsafe and should be replaced. Reach out to Innate for more information.


---

## Control & Connectivity

_Source: https://docs.innate.bot/robots/mars/control-and-connectivity.md_

# Control & Connectivity

This page covers app control, leader-arm teleoperation, first-time connectivity, and SSH access.

## Control via App and Leader Arm

MARS (and all Innate robots) are controllable via the Innate app:

<CardGroup cols={2}>
  <Card title="Android APK (Latest)" href="https://cdn.innate.bot/innate-app-latest.apk">
    Direct APK download.
  </Card>

  <Card title="iOS TestFlight" href="https://testflight.apple.com/join/YeChe4A7">
    Open the iOS beta access page.
  </Card>
</CardGroup>

Every MARS robot comes with a leader arm attachable to your phone:

<Frame caption="The arm is plugged in your phone with a double USB-C cable">
  <img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/mars/control-via-app-leader-arm.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=7570aa191ea84b454a47b179996e8aca" width="375" data-path="images/main/robots/mars/control-via-app-leader-arm.png" />
</Frame>

The app automatically recognizes your arm. Press the red **Arm** button to control MARS with the leader arm. For best results, stand behind the robot while teleoperating.

**iOS users:** The leader arm connects via USB-C and is not compatible with iOS devices. Reach out on [Discord](https://discord.com/invite/KtkyT97kc7) for access to a free Android phone for leader arm teleoperation.

## Innate Controller App Overview

The app is available for both iOS and Android so you can control your robot and trigger agents from your phone.

### Current versions (April 2026)

| Component             | Version |
| --------------------- | ------- |
| MARS OS               | `0.4.5` |
| Cloud Agent           | `0.2.1` |
| Innate Controller App | `1.1.0` |

Latest app builds:

<CardGroup cols={2}>
  <Card title="Android APK (Latest)" href="https://cdn.innate.bot/innate-app-latest.apk">
    Direct APK download.
  </Card>

  <Card title="iOS TestFlight" href="https://testflight.apple.com/join/YeChe4A7">
    Open the latest iOS TestFlight build.
  </Card>
</CardGroup>

### Key features

* Drive base control and arm control from phone
* Leader arm teleoperation
* Map-free navigation, mapping mode, and go-to mode
* Video recording and export
* Control the agent running on the robot from the home screen
* Digital skills UI with input validation and feedback

## Connecting to a Robot (Wi-Fi + BLE)

The app connects to your robot via Wi-Fi. It can also work through your phone hotspot.

### First-time connection flow

This is the same onboarding flow covered in [Quick Start](/get-started/mars-quick-start).

<Steps>
  <Step title="Bluetooth pairing">
    The app uses BLE to discover the robot and initialize network setup.
  </Step>

  <Step title="Wi-Fi configuration">
    Select the Wi-Fi network the robot should join. If the robot is not yet
    connected to any Wi-Fi, use screen 2 to pick a network and enter its
    password.
  </Step>

  <Step title="Connect over Wi-Fi">
    Once your phone and robot are on the same network, the app connects over Wi-Fi.
  </Step>
</Steps>

The robot publishes a `.local` hostname (for example `mars-robot.local`) so you can still connect if IP changes.

<CardGroup cols={3}>
  <Card title="1. Discover Robot">
    <img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/innate-controller-app/connect-step-1.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=ae1b4925fb9e31c660977eb8714a49db" alt="Bluetooth discovery step" width="960" height="2142" data-path="images/main/robots/innate-controller-app/connect-step-1.png" />
  </Card>

  <Card title="2. Join Network">
    <img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/innate-controller-app/connect-step-2.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=affe8f5362bfbc9b85d07b7d0fd718fb" alt="Wi-Fi selection step" width="960" height="2142" data-path="images/main/robots/innate-controller-app/connect-step-2.png" />

    If the robot is not connected yet, choose a Wi-Fi network here and set the password.
  </Card>

  <Card title="3. Change Robot Wi-Fi">
    <img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/innate-controller-app/connect-step-3.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=5c2c27c67b2eb842bd91f802fe3d8d56" alt="Change Robot Wi-Fi step" width="960" height="2142" data-path="images/main/robots/innate-controller-app/connect-step-3.png" />
  </Card>
</CardGroup>

Once connected, you can view the current robot IP in **Configuration** -> **WiFi**.

## Connecting via SSH

Default credentials:

* **Username:** `jetson1`
* **Password:** `goodbot`

### Via Wi-Fi

If your robot is on the same network as your computer:

```bash  theme={null}
ssh jetson1@<robot-name>.local
```

Hostname conversion rules:

* Uppercase letters become lowercase
* Spaces/special characters become `-`
* Duplicate hyphens are collapsed
* Leading/trailing hyphens are removed

Examples:

| Robot name | Hostname         | SSH command                  |
| ---------- | ---------------- | ---------------------------- |
| `My Robot` | `my-robot.local` | `ssh jetson1@my-robot.local` |
| `MARS_01`  | `mars-01.local`  | `ssh jetson1@mars-01.local`  |
| `Test Bot` | `test-bot.local` | `ssh jetson1@test-bot.local` |

If unnamed, default hostname is:

```bash  theme={null}
ssh jetson1@mars.local
```

### Via Ethernet (preferred wired method)

Connect Ethernet between computer and robot, then SSH:

```bash  theme={null}
ssh jetson1@192.168.50.2
```

Set your computer Ethernet interface to static IPv4:

* IP: `192.168.50.1`
* Netmask: `255.255.255.0`
* Gateway: empty
* DNS: empty

### Via USB-C (last resort)

USB-C is not recommended and should only be used when Wi-Fi and Ethernet are unavailable.

```bash  theme={null}
ssh jetson1@192.168.55.1
```


---

## Critical Fixes

_Source: https://docs.innate.bot/robots/mars/critical-fixes.md_

# Critical Fixes

Use this page for required one-off fixes on specific robot batches.

## Available critical fixes

* [Critical Fix (MARS IDs 1-11)](/robots/mars/troubleshooting/critical-fix-before-jan-16)


---

## Extending MARS

_Source: https://docs.innate.bot/robots/mars/extending-mars.md_

# Extending MARS

MARS was designed for hardware extensibility through several features:

* Most GPIO pins are available on the onboard Jetson Orin Nano. You can connect I2C, SPI, UART sensors this way.
  * We have noticed using the UART peripheral causes audio artifacts because of the way the Jetson's interfaces are designed, but it still works.

* Unused GPIO from the microcontroller is broken out on the PCB.
  The microcontroller communicates with the Jetson through I2C and you can see that on its [firmware repo](https://github.com/innate-inc/mars-firmware).

* Four USB-A extension ports are available: two directly on the Jetson and two powered ports on the top USB hub.
  * You can use sensors like additional USB cameras, NFC readers, mics, or even microcontrollers to interface other sensors.

* There are screw terminals for both 12V and 5V power.

* The hardware is [open-sourced](https://github.com/innate-inc/mars) in order to be easier to modify, in particular the end-effector.

We describe below how we recommend to extend MARS on the hardware side.

## Changing the end-effector

The end effector by default is a gripper (opposable thumbs).

By nature of robot learning, if you change the end effector to any other shape, you will have to recollect your data for your manipulation models, but nothing else in the operating system needs to change if you still use the last actuator.

Examples of two different types of end effectors we used without changing the code:

<CardGroup cols={2}>
  <Card title="MARS v1 gripper">
    <img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/mars/extending-mars-1319.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=ccb8efa0eccf8b6dba8bbe48619210b7" alt="MARS v1 gripper" width="2304" height="2363" data-path="images/main/robots/mars/extending-mars-1319.png" />
  </Card>

  <Card title="One-side moving gripper">
    <img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/robots/mars/extending-mars-1320.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=3a0e4172bef179599102223b64b6d20e" alt="One-side moving gripper" width="2304" height="2659" data-path="images/main/robots/mars/extending-mars-1320.png" />
  </Card>
</CardGroup>

## Adding sensors and effectors on the USB and GPIOs

Users can integrate additional sensors on the available ports. For any added device, make sure it is mounted and installed properly on the robot. You can then feed data into the BASIC OS by creating a `Sensor` object in the SDK (TBD).

Some sensors we have already tried and work plug-and-play on MARS:

* TONOR directional microphone ([\$29 on Amazon](https://www.amazon.com/dp/B0CSCT63BL?ref=fed_asin_title)) - MARS already has a built-in microphone inside the arm. This optional add-on improves directional pickup. Just plug it in and make sure it's selected in the inputs tab of tmux when you start an agent.

* Blackiot [Polverine Air Quality Sensor](https://blackiot.swiss/polverine).

#### Example: Adding a directional microphone (optional)

MARS can already listen with its built-in microphone. If you want more directional pickup, plug in a directional microphone and follow the [Example: Microphone](/software/inputs/example-microphone) guide.

<iframe width="100%" height="420" src="https://www.youtube.com/embed/Da_vpacFfvM" title="Microphone extension demo" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />


---

## FAQ

_Source: https://docs.innate.bot/robots/mars/faq.md_

# FAQ

<Accordion title="chevron-rightHow do I find my MARS ID?">
  Your MARS ID is a unique number assigned to your robot. There are two ways to find it:

  **Via Bluetooth**

  When you turn on your robot and look for it in the Innate app's Bluetooth connections screen, the robot will appear with a name like **"MARS the 1st"**, **"MARS the 2nd"**, etc. The number in the name is your MARS ID.

  For example:

  * "MARS the 1st" → MARS ID **1**

  * "MARS the 5th" → MARS ID **5**

  * "MARS the 12th" → MARS ID **12**

  **Via robot\_info.json**

  If you can SSH into your robot, you can also find the ID in the robot info file:

  ```bash  theme={null}
    cat ~/innate-os-data/robot_info.json
  ```

  Look for the `robot_id` field in the JSON output.
</Accordion>

***

## More questions?

If you have other questions not covered here, reach out on [Discord](https://discord.com/invite/KtkyT97kc7) or email [axel@innate.bot](mailto:axel@innate.bot).


---

## Troubleshooting

_Source: https://docs.innate.bot/robots/mars/troubleshooting.md_

# Troubleshooting

This page explains how to diagnose issues on your MARS robot by inspecting the running processes.

***

## Connect via SSH

First, [SSH into your robot](/robots/mars/connecting-via-ssh).

***

## Access the OS tmux session

MARS runs its software stack inside a `tmux` session. To attach to it:

```bash  theme={null}
tmux attach
```

If there are multiple sessions, you can list them with `tmux ls` and attach to the correct one.

***

## Navigate tmux to find issues

:::note This section is for advanced users familiar with ROS2. If you're not comfortable with ROS, simply reach out to us on [Discord](https://discord.com/invite/KtkyT97kc7) and we'll help you diagnose the issue. :::

Once inside the tmux session, you'll see multiple windows or panes, each running a different ROS2 node or process.

### Basic tmux navigation

* **Switch windows:** `Ctrl+b` then `n` (next) or `p` (previous)

* **List windows:** `Ctrl+b` then `w`

* **Switch panes:** `Ctrl+b` then arrow keys

* **Scroll up:** `Ctrl+b` then `[`, then use arrow keys or Page Up/Down. Press `q` to exit scroll mode.

### Finding a problematic node

1. Cycle through the windows and panes to see which processes are running.

2. Look for error messages, stack traces, or nodes that have crashed or are restarting.

3. Use scroll mode to review recent output and identify what went wrong.

***

## App can reach Wi-Fi but robot services are not launched

If your robot is connected to Wi-Fi and the app shows a service launch failure screen, the ROS2 core likely did not start correctly.

1. [SSH into your robot](/robots/mars/connecting-via-ssh).

   Default password: `goodbot`

2. Rerun the post-update recovery script:

```bash  theme={null}
sudo ~/innate-os/scripts/update/post_update.sh
```

Sudo password: `goodbot`

3. Wait for the script to finish, then retry the connection from the app.

This usually resolves failures caused by an interrupted or incomplete post-update startup.

***

## Common Hardware Issues

### Arm Goes Limp / Servos Not Holding Position

If the arm loses tension and goes limp (servos not holding their position), this is typically a servo communication issue that can be resolved by rebooting the arm:

**Option 1: Reboot via the App (Recommended)**

1. Open the Innate Controller App

2. Go to **Configuration**

3. Select the **Dev** tab

4. Tap **Reboot Arm**

> **Note:** Place the arm in a resting position before rebooting. The app will display an image showing the correct arm position.

**Option 2: Full Robot Restart**

1. Unplug the robot's power

2. Wait a few seconds

3. Plug it back in

The arm should regain tension and hold position after either of these steps.

### Arm Restart Notifications

If the arm encounters an issue during operation (such as a servo communication failure), the app will display a notification prompting you to restart the arm. Follow the notification instructions to recover.

### Arm Overload Protection

MARS monitors the arm's servo load in real-time. If the arm is overloaded (e.g., carrying too heavy of an object or encountering an obstruction), the system will detect this and may reduce torque to protect the servos. If you notice reduced arm performance:

1. Remove any heavy objects from the gripper

2. Clear any obstructions

3. Reboot the arm via the app if needed

### iOS Arm Control

**iOS Users:** The leader arm connects via USB-C and is not compatible with iOS devices (for now). If you have an iPhone, please reach out to Innate on [Discord](https://discord.com/invite/KtkyT97kc7) to get access to a free Android phone for leader arm teleoperation.

***

## Low Battery Warning

The app displays a pulsing **Battery Low** warning when the robot's battery voltage drops below 10.53V. When you see this warning:

1. Stop any active tasks

2. Park the robot in a safe place

3. Connect the charger

Avoid running system updates or intensive operations when the battery is low.

***

## Contact us

When you identify an issue, please reach out to us on [Discord](https://discord.com/invite/KtkyT97kc7) with:

* The name of the node or process that is failing

* Any error messages or stack traces you see

* What you were doing when the issue occurred

We'll help you resolve it as quickly as possible.


---

## Updates & Maintenance

_Source: https://docs.innate.bot/robots/mars/updates-and-maintenance.md_

# Updates and Maintenance

Keep your robot stable and current with software updates, safe charging, and core configuration checks.

## Updating MARS

Use `innate update` on the robot to fetch and apply MARS OS updates.

Updating will:

* Fetch the latest compatible Innate OS version
* Apply code and configuration changes
* Restart robot software services

If update notes include stereo-depth changes, run [Calibration](/robots/mars/calibration) before normal navigation.

### Prerequisites

* You can access the robot over SSH
* The `innate` CLI is available on the robot
* The robot has internet access

### Basic workflow

```bash  theme={null}
innate update status
innate update check
innate update apply
```

Use `status` to verify current version, `check` to view available updates, and `apply` to install.

During `apply`, services may restart and the robot can be temporarily unresponsive.

If update commands fail, retry once and capture:

* The command you ran
* Full terminal error output

## Charging the Battery

Charging has a dedicated page with full safety instructions and a step-by-step procedure.

<Card title="Charging the Battery" href="/robots/mars/charging-battery">
  Open the dedicated charging guide.
</Card>

## Changing the Voice

MARS uses [Cartesia](https://cartesia.ai/) for text-to-speech.

### Method 1: `.env` (recommended)

1. SSH into the robot.
2. Edit `.env`:

```bash  theme={null}
nano ~/innate-os/.env
```

3. Add or update:

```bash  theme={null}
CARTESIA_VOICE_ID=your-voice-id-here
```

4. Restart robot services.

### Method 2: launch file (advanced)

1. Edit launch file:

```bash  theme={null}
~/innate-os/ros2_ws/src/brain/brain_client/launch/brain_client.launch.py
```

2. Update `cartesia_voice_id` default value.
3. Build and restart:

```bash  theme={null}
innate build
```

You can use existing Cartesia voices or create a custom voice:

<Card title="Cartesia Docs" href="https://docs.cartesia.ai/get-started/overview">
  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
    <img src="https://mintcdn.com/innateinc/Iz9Yze2d1_xbvYKc/images/logos/services/cartesia-light.png?fit=max&auto=format&n=Iz9Yze2d1_xbvYKc&q=85&s=d31494e24a248f8d24ef918dd3590d40" alt="Cartesia logo" width="18" height="18" className="block dark:hidden" data-path="images/logos/services/cartesia-light.png" />

    <img src="https://mintcdn.com/innateinc/Iz9Yze2d1_xbvYKc/images/logos/services/cartesia-dark.png?fit=max&auto=format&n=Iz9Yze2d1_xbvYKc&q=85&s=3e68dd057b24af3c151d894ea598e5fc" alt="Cartesia logo" width="18" height="18" className="hidden dark:block" data-path="images/logos/services/cartesia-dark.png" />

    <span>Voice library, custom voice cloning, and setup guides.</span>
  </div>
</Card>


---

# Software — Overview & Setup

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

# Software — Agents

## Agents Overview

_Source: https://docs.innate.bot/software/agents.md_

# Introduction

An agent defines who your robot is and what it can do. Without an agent, a robot is just hardware waiting for instructions. With an agent, it becomes a security guard, a tour guide, a friendly greeter etc.

## What is an Agent?

An agent is a Python class that defines three things together: the **skills** the robot can execute, the **inputs** it listens to, and the **prompt** that defines behavior and tone. When you activate an agent, the robot adopts that identity. The same hardware can run very different agents with distinct personalities and capabilities.

## Agents as Portable Applications

Agents are designed to be shareable. Write an agent once, and anyone with an Innate robot can use it—just drop the Python file into the agents folder.

No configuration files. No complex setup. Just Python.

For OS 0.4.5, the built-in agents come from `innate-os/agents` and appear on the **Home** screen in the Innate Controller App.

<CardGroup cols={2}>
  <Card title="No Prompt (`basic_agent`)">
    Minimal default behavior with `navigate_to_position` and no prompt text.
  </Card>

  <Card title="Demo Agent (`demo_agent`)">
    Friendly interactive demo agent with navigation, waving, and gaze.
  </Card>

  <Card title="J3SO (`j3so_directive`)">
    Character-style conversational agent with navigation.
  </Card>

  <Card title="Security Guard (`security_guard_agent`)">
    Patrol-oriented agent with door opening and email alert behavior.
  </Card>

  <Card title="Chess Piece Agent (`chess_piece_agent`)">
    Chess gameplay agent using piece manipulation and move detection.
  </Card>

  <Card title="Chess Self-Play Agent (`chess_self_play_agent`)">
    Autonomous self-play chess agent with narrated moves.
  </Card>

  <Card title="Board Calibration Agent (`board_calibration_agent`)">
    Guided workflow agent for chess board corner calibration.
  </Card>
</CardGroup>

<img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/software/agents-overview.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=cd5a12cc763264a6ac9d5af22f93492d" alt="Built-in agents in the app" style={{ maxWidth: "360px", width: "100%", display: "block", margin: "16px auto" }} width="960" height="2142" data-path="images/main/software/agents-overview.png" />

## Chess beta guides

* [Chess (beta)](/software/agents/chess-beta)
* [Chessboard calibration (beta)](/software/agents/chessboard-calibration-beta)

## System Architecture

Agents integrate into the following architecture:

```text  theme={null}
┌─────────────────────────────────────────────────────────────────┐
│                        Cloud AI                                  │
│            Processes vision and makes decisions                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                    Brain Client (ROS 2)                          │
│       Manages agents, executes skills, bridges cloud ↔ robot     │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐    ┌───────▼───────┐    ┌──────▼──────┐
│    Agents     │    │    Skills     │    │   Inputs    │
│ (Personality) │    │  (Actions)    │    │  (Sensors)  │
└───────────────┘    └───────────────┘    └─────────────┘
```

The cloud AI receives camera feeds and input data. It reads the agent's prompt to understand the robot's role, checks available skills to know what actions are possible, then decides what to do. The robot executes accordingly.

Your agent is the contract between you and the AI—it defines who the robot is and what it can do.

## Design Philosophy

Traditional robotics software often requires deep expertise to modify. Agents take a different approach: they're designed to be readable and modifiable.

You can look at an agent file and immediately understand what it does. You can modify it, experiment, and iterate quickly. The goal is to let you focus on building interesting robot behaviors rather than wrestling with infrastructure.


---

## Agent Definitions

_Source: https://docs.innate.bot/software/agents/definitions.md_

# Anatomy of an Agent

export const AgentOptionalMethodsTable = () => {
  const rows = [{
    method: "display_icon",
    returns: "str",
    purpose: "Path to a 32x32 pixel icon."
  }, {
    method: "get_inputs()",
    returns: "List[str]",
    purpose: "Input devices to activate (for example: [\"micro\"])."
  }, {
    method: "uses_gaze()",
    returns: "bool",
    purpose: "Enable person-tracking eye movement."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Method</th>
            <th>Returns</th>
            <th>Purpose</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.method}>
              <td>
                <span className="interface-method-pill">{row.method}</span>
              </td>
              <td>
                <span className="interface-param-badge">
                  {row.returns}
                </span>
              </td>
              <td>{row.purpose}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

export const AgentCoreMethodsTable = () => {
  const rows = [{
    method: "id",
    returns: "str",
    purpose: "Unique identifier (snake_case)."
  }, {
    method: "display_name",
    returns: "str",
    purpose: "Human-readable name shown in the app."
  }, {
    method: "get_skills()",
    returns: "List[str]",
    purpose: "Skills this agent can use."
  }, {
    method: "get_prompt()",
    returns: "str",
    purpose: "Personality and behavioral instructions."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Method</th>
            <th>Returns</th>
            <th>Purpose</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.method}>
              <td>
                <span className="interface-method-pill">{row.method}</span>
              </td>
              <td>
                <span className="interface-param-badge">
                  {row.returns}
                </span>
              </td>
              <td>{row.purpose}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

Every agent follows the same structure. Once you understand it, you can create any agent you need.

## File Location

Agents are stored in `~/agents` on your robot. The system automatically discovers Python files in this directory—no registration or configuration required.

Add a file, and the agent appears. Remove it, and the agent disappears.

## Core Interface

Every agent implements four methods:

<AgentCoreMethodsTable />

Optional methods:

<AgentOptionalMethodsTable />

## Minimal Example

The simplest possible agent:

```python  theme={null}
from typing import List
from brain_client.agent_types import Agent

class MyAgent(Agent):
    @property
    def id(self) -> str:
        return "my_agent"

    @property
    def display_name(self) -> str:
        return "My Agent"

    def get_skills(self) -> List[str]:
        return []

    def get_prompt(self) -> str:
        return "You are a robot."
```

This agent loads and runs, but does very little—it has no skills and a minimal prompt.

## Complete Example

A functional agent with skills, inputs, and a detailed prompt:

```python  theme={null}
from typing import List
from brain_client.agent_types import Agent

class HelloWorld(Agent):
    """Greets visitors with a friendly wave."""

    @property
    def id(self) -> str:
        return "hello_world"

    @property
    def display_name(self) -> str:
        return "Hello World"

    @property
    def display_icon(self) -> str:
        return "assets/hello_world.png"

    def get_skills(self) -> List[str]:
        return ["navigate_to_position", "wave"]

    def get_inputs(self) -> List[str]:
        return ["micro"]

    def get_prompt(self) -> str:
        return """
You are a friendly robot who greets people.

- Speak in a casual, warm tone
- If you don't see anyone, turn around to look for them
- When you see a person, wave and say hello
- Respond to what people say to you
"""

    def uses_gaze(self) -> bool:
        return True
```

This agent combines navigation and waving skills, microphone input, a friendly prompt, and gaze tracking for more natural interaction.

## Writing Effective Prompts

The prompt determines how the robot behaves. Skills define what's *possible*; the prompt defines what *actually happens*.

A good prompt defines personality, goals, constraints, and strategy in plain language. Be specific. The AI interprets your prompt literally, and vague instructions produce inconsistent behavior.

## Template

Copy and modify this template for new agents:

```python  theme={null}
from typing import List
from brain_client.agent_types import Agent

class MyCustomAgent(Agent):
    """One-line description of what this agent does."""

    @property
    def id(self) -> str:
        return "my_custom_agent"

    @property
    def display_name(self) -> str:
        return "My Custom Agent"

    @property
    def display_icon(self) -> str:
        return "assets/my_icon.png"  # Optional

    def get_skills(self) -> List[str]:
        return [
            "navigate_to_position",
            "wave",
            "turn_and_move",
        ]

    def get_inputs(self) -> List[str]:
        return ["micro"]

    def get_prompt(self) -> str:
        return """
Describe who the robot is and what it should do.
Be explicit about personality, goals, strategy, and constraints.
"""

    def uses_gaze(self) -> bool:
        return True
```

Save this as `my_agent.py` in `~/agents`, and the system will load it automatically.


---

## Starting an Agent

_Source: https://docs.innate.bot/software/agents/starting-an-agent.md_

# Starting an Agent

Once you've created an agent, you can activate it through the Controller App or directly on the robot.

## Using the Controller App

Open the **Innate Controller App**, connect to your robot on the same network, then go to the **Home** screen and tap an agent card to activate it. To switch agents, tap a different card. To stop the current one, use the stop button.

<img src="https://mintcdn.com/innateinc/hx7RaA7br-n-YY5y/images/main/software/agents/starting-an-agent.png?fit=max&auto=format&n=hx7RaA7br-n-YY5y&q=85&s=d31991a0dbdc6dfb93788ca131246682" alt="Starting an agent from the app" style={{ maxWidth: "360px", width: "100%", display: "block", margin: "16px auto" }} width="960" height="2142" data-path="images/main/software/agents/starting-an-agent.png" />

## Setting a Default Agent

You can configure an agent to start automatically when the robot boots.

In the Controller App, go to **Home**, long-press an agent card, and select **Set as default**. The app marks it as default. To remove it, long-press again and select **Remove default**.

## Activation Sequence

When you activate an agent, the runtime loads its skills, opens its inputs, uploads the prompt, enables gaze if configured, and starts the perception/decision loop. This typically completes in about one second.

## Switching Between Agents

Switching is immediate: the current agent is torn down, the new one is loaded, and in-progress actions from the previous agent are cancelled rather than completed.

## Troubleshooting

### Agent doesn't appear in the app

Check that the file is in `~/agents`, then on the app **Home** screen swipe down (pull-to-refresh) to reload the agent list. If it still does not appear, verify the file imports without Python errors and inspect runtime logs using the [Troubleshooting guide](/robots/mars/troubleshooting#navigate-tmux-to-find-issues).

### Agent won't start

Check robot logs for startup errors (see [Troubleshooting](/robots/mars/troubleshooting#navigate-tmux-to-find-issues)), confirm every skill listed in `get_skills()` exists, and ensure the prompt is valid for the behavior you expect.

### Agent starts but robot is unresponsive

Usually this is a prompt or wiring issue. Tighten the prompt wording, verify required skills are in `get_skills()`, and confirm necessary inputs (for example `micro`) are present in `get_inputs()`.


---

## Agent Examples

_Source: https://docs.innate.bot/software/agents/agent-examples.md_

# Agent Examples

These examples demonstrate different agent patterns. Use them as starting points for your own implementations.

<AccordionGroup>
  <Accordion title="Security Guard" defaultOpen={true}>
    A patrol agent that monitors for intruders and sends email alerts.

    ```python  theme={null}
    from typing import List
    from brain_client.agent_types import Agent

    class SecurityGuardAgent(Agent):
        """Patrols the premises and alerts on unauthorized visitors."""

        @property
        def id(self) -> str:
            return "security_guard"

        @property
        def display_name(self) -> str:
            return "Security Guard"

        @property
        def display_icon(self) -> str:
            return "assets/security_guard.png"

        def get_skills(self) -> List[str]:
            return [
                "navigate_to_position",
                "open_door",
                "send_email",
            ]

        def get_inputs(self) -> List[str]:
            return ["micro"]

        def get_prompt(self) -> str:
            return """You are a security guard robot. Maintain a vigilant,
    professional demeanor at all times.

    Patrol route:
    1. Start in the living room
    2. Check the kitchen
    3. Move to the bedroom
    4. Inspect the back door
    5. Return to start and repeat

    Patrol behavior:
    - Move deliberately through each area
    - Observe carefully before proceeding
    - Open doors that block your path
    - Identify anyone who shouldn't be present

    Intruder protocol:
    - Do not confront
    - Send email to owner@example.com immediately
    - Include location and description of what you observed

    Maintain professional alertness throughout your patrol."""
    ```

    Key pattern: the prompt includes a specific route, clear behavior guidelines, and explicit edge-case handling.
  </Accordion>

  <Accordion title="Object Collector">
    A task-focused agent that finds and collects specific items.

    ```python  theme={null}
    from typing import List
    from brain_client.agent_types import Agent

    class SockCollector(Agent):
        """Collects socks from the floor and places them in the laundry basket."""

        @property
        def id(self) -> str:
            return "sock_collector"

        @property
        def display_name(self) -> str:
            return "Sock Collector"

        def get_skills(self) -> List[str]:
            return [
                "navigate_to_position",
                "pick_up_object",
                "drop_object",
            ]

        def get_inputs(self) -> List[str]:
            return ["micro"]

        def get_prompt(self) -> str:
            return """You are a tidying robot. Your task: find socks on the
    floor and place them in the laundry basket.

    Procedure:
    1. Scan the room for socks on the floor
    2. Navigate to a visible sock
    3. Pick it up
    4. Navigate to the laundry basket (white wicker basket near the
       bedroom door)
    5. Drop the sock in
    6. Repeat until no socks remain

    Guidelines:
    - Check under furniture edges where socks tend to accumulate
    - If a sock is unreachable, skip it and continue
    - Perform a final sweep when you believe you're done"""
    ```

    Key pattern: single-purpose objective with a concrete procedure and practical fallback rules.
  </Accordion>

  <Accordion title="Tour Guide">
    An interactive agent that engages with visitors and provides guided tours.

    ```python  theme={null}
    from typing import List
    from brain_client.agent_types import Agent

    class TourGuide(Agent):
        """Welcomes visitors and provides guided tours of the space."""

        @property
        def id(self) -> str:
            return "tour_guide"

        @property
        def display_name(self) -> str:
            return "Tour Guide"

        def get_skills(self) -> List[str]:
            return ["navigate_to_position", "wave"]

        def get_inputs(self) -> List[str]:
            return ["micro"]

        def get_prompt(self) -> str:
            return """You are a tour guide robot. Be warm, knowledgeable,
    and attentive to your guests.

    Greeting:
    1. Wave and welcome approaching visitors
    2. Ask if they would like a tour
    3. Begin the tour if they accept

    Tour route:
    - Entrance: Brief history of the building
    - Main hall: Notable artwork and features
    - Workshop: Current projects and activities
    - Lounge: Conclude and offer to answer questions

    Interaction style:
    - Speak clearly at a comfortable pace
    - Allow time for guests to observe each area
    - Answer questions thoroughly
    - Maintain eye contact during conversation

    If a guest needs to leave early, thank them for visiting."""

        def uses_gaze(self) -> bool:
            return True
    ```

    Key pattern: gaze-enabled social interaction with route and dialogue structure.
  </Accordion>

  <Accordion title="Passive Observer">
    A minimal agent that monitors quietly and only engages when addressed.

    ```python  theme={null}
    from typing import List
    from brain_client.agent_types import Agent

    class QuietObserver(Agent):
        """Observes the environment and responds only when addressed."""

        @property
        def id(self) -> str:
            return "quiet_observer"

        @property
        def display_name(self) -> str:
            return "Quiet Observer"

        def get_skills(self) -> List[str]:
            return ["navigate_to_position"]

        def get_inputs(self) -> List[str]:
            return ["micro"]

        def get_prompt(self) -> str:
            return """You are an observant robot with a calm presence.

    Behavior:
    - Remain quiet unless directly addressed
    - When spoken to, respond briefly and thoughtfully
    - Rotate in place slowly to observe your surroundings
    - Do not navigate away unless requested

    Maintain a non-intrusive presence in the room."""

        def uses_gaze(self) -> bool:
            return True
    ```

    Key pattern: minimal skill set with a restrained prompt for passive behavior.
  </Accordion>
</AccordionGroup>

## Combining Patterns

These examples represent reusable patterns you can mix depending on your use case: patrol + alert, search + manipulate, navigate + interact, and observe + respond. In practice, most production agents combine at least two of these patterns.

For chess-specific setup and calibration:

* [Chess (beta)](/software/agents/chess-beta)
* [Chessboard calibration (beta)](/software/agents/chessboard-calibration-beta)


---

## Chess Agent (Beta)

_Source: https://docs.innate.bot/software/agents/chess-beta.md_

# Chess (Beta)

MARS chess is playable end-to-end and currently in beta.

This page covers setup and runtime behavior for `chess_agent`. For the dedicated chessboard calibration workflow, go to [Chessboard calibration (beta)](/software/agents/chessboard-calibration-beta).

## Before you start

* Make sure arm control and cameras are working.
* Keep the chessboard fixed in one position while playing.
* Use the app Home screen to start agents.
* Configure Gemini for move detection.

## Configure Gemini key

`detect_opponent_move` loads `GEMINI_API_KEY` from `~/innate-os/skills/.env.scan`.

Create or update this file on the robot:

```bash  theme={null}
cat > ~/innate-os/skills/.env.scan <<'EOF_ENV'
GEMINI_API_KEY=your_key_here
EOF_ENV
```

## Agents and skills used

`chess_agent` uses:

* `pick_up_piece_simple`
* `detect_opponent_move`
* `update_chess_state`
* `recalibrate_manual`
* `arm_utils`
* `reset_chess_game`
* `head_emotion`

For first setup (or after board movement), run the top-corner calibration flow in [Chessboard calibration (beta)](/software/agents/chessboard-calibration-beta).

## Start a game

1. Run [Chessboard calibration (beta)](/software/agents/chessboard-calibration-beta) if needed.
2. Start `chess_agent`.
3. Call `reset_chess_game(robot_color="white")`.
4. Human plays Black, robot plays White.

Calibration and reset are skill calls. Trigger them from the app Skills screen or through ROS 2 action calls as documented in [Chessboard calibration (beta)](/software/agents/chessboard-calibration-beta).

Game state is stored in `~/chess_game_state.json`.

## Recommended physical validation

Before real play, test placement accuracy:

1. Place a spare pawn on `A4`.
2. Keep `H5` empty.
3. Run:

```python  theme={null}
pick_up_piece_simple(square="A4", place_square="H5", piece="pawn", is_capture=False, speed=1.5)
```

4. If placement is off, run manual recalibration and test again.

This is a physical calibration check only. Do not treat it as game state.

## Runtime move loop

The expected cycle is:

1. Human makes a move.
2. Run `detect_opponent_move(robot_color="white")`.
3. Run `update_chess_state(move_uci="...")` for the detected move.
4. Decide robot move.
5. Run `pick_up_piece_simple(...)` for physical execution.
6. Run `update_chess_state(move_uci="...")` for the robot move.

## Castling behavior

Physical castling requires two motion calls:

* king move (`E1 -> G1` or `E1 -> C1`)
* rook move (`H1 -> F1` or `A1 -> D1`)

Board state still updates once with the king UCI castling move (`e1g1` or `e1c1`).

## Troubleshooting

* Move detection fails:
  * verify `GEMINI_API_KEY` in `~/innate-os/skills/.env.scan`
  * verify wrist camera view is unobstructed
* Piece placement drifts:
  * run [Chessboard calibration (beta)](/software/agents/chessboard-calibration-beta#quick-manual-recalibration-for-drift)
* Reset fails with calibration error:
  * run full board calibration first
* Arm hardware issue:
  * run `arm_utils(command="reboot_arm")`


---

## Chessboard Calibration (Beta)

_Source: https://docs.innate.bot/software/agents/chessboard-calibration-beta.md_

# Chessboard calibration (beta)

This calibration is for chess manipulation only (not depth/navigation calibration).

Chess calibration uses top corners `A8` and `H8` with `recalibrate_manual`, then computes `A1` and `H1` automatically and saves all corners to `~/board_calibration.json`.

## Calibration process

<Steps>
  <Step title="Fix board position">
    Put the chessboard in its final position. Do not move it during calibration.
  </Step>

  <Step title="Enable manual arm movement">
    Set the arm to manual/limp mode so you can position the end effector by hand.
  </Step>

  <Step title="Position for A8 and record">
    Move the end effector to the center of `A8` and record that top corner reference.

    <Frame caption="Target pose example: end effector centered on A8">
      <img src="https://mintcdn.com/innateinc/M6z0XunIsu34mN-3/images/main/software/agents/chess-calibration-a8-end-effector.jpg?fit=max&auto=format&n=M6z0XunIsu34mN-3&q=85&s=59e1b2c7d71abee4b9430f04cc199f6a" alt="End effector centered over A8 square for calibration" style={{ maxWidth: "420px", width: "100%", margin: "0 auto", display: "block" }} width="4032" height="3024" data-path="images/main/software/agents/chess-calibration-a8-end-effector.jpg" />
    </Frame>
  </Step>

  <Step title="Position for H8 and record">
    Move the end effector to the center of `H8` and record that second top-corner reference.
  </Step>

  <Step title="Finish and verify">
    Re-enable holding torque. Verify `~/board_calibration.json` contains `top_left`, `top_right`, `bottom_left`, and `bottom_right`.
  </Step>
</Steps>

## 1) Manual triggering

Trigger the skills from the app or CLI.

### App

* Open **Innate Controller App** -> **Skills** -> **Digital Skills**
* Run:
  * `arm_utils` with `command=torque_off`
  * `recalibrate_manual` with `corner=A8`
  * `recalibrate_manual` with `corner=H8`
  * `arm_utils` with `command=torque_on`

### CLI (ROS2 today)

Use ROS2 actions for now. A simpler dedicated CLI is coming soon.

```bash  theme={null}
ros2 action send_goal /execute_primitive brain_messages/action/ExecutePrimitive \
  '{primitive_type: arm_utils, inputs: "{\"command\":\"torque_off\"}"}' --feedback

ros2 action send_goal /execute_primitive brain_messages/action/ExecutePrimitive \
  '{primitive_type: recalibrate_manual, inputs: "{\"corner\":\"A8\"}"}' --feedback

ros2 action send_goal /execute_primitive brain_messages/action/ExecutePrimitive \
  '{primitive_type: recalibrate_manual, inputs: "{\"corner\":\"H8\"}"}' --feedback

ros2 action send_goal /execute_primitive brain_messages/action/ExecutePrimitive \
  '{primitive_type: arm_utils, inputs: "{\"command\":\"torque_on\"}"}' --feedback
```

## 2) Agentic triggering

Run `chess_agent`. It can guide you through calibration and trigger the same skill sequence with you (`torque_off` -> `A8` -> `H8` -> `torque_on`) before play.

If calibration quality drifts during use, rerun the same sequence manually.


---

# Software — Skills

## Skills Overview

_Source: https://docs.innate.bot/software/skills.md_

# Introduction

Skills are atomic robot capabilities that BASIC chains together to accomplish complex, long-horizon behaviors. Each skill encodes a single capability—physical (manipulation, navigation) or digital (emails, API calls)—that can be combined with others to form coherent action sequences.

When BASIC receives a request like "check on grandma," it decomposes this into a skill chain: navigate to bedroom → look around → send picture via email → speak reassurance. Four skills, one coherent behavior.

## Two Types of Skills

Skills are defined in one of two ways.

<AccordionGroup>
  <Accordion title="Code-Defined Skills" defaultOpen={true}>
    Code-defined skills are Python classes with explicit logic. The runtime injects declared interfaces, and BASIC reads your signature/docstrings to call the skill correctly.

    ```python  theme={null}
    import math
    from brain_client.skill_types import Skill, SkillResult, Interface, InterfaceType

    class LookAround(Skill):
        mobility = Interface(InterfaceType.MOBILITY)
        head = Interface(InterfaceType.HEAD)

        @property
        def name(self):
            return "look_around"

        def execute(self, num_directions: int = 4):
            """Rotate and scan the environment."""
            if self.mobility is None or self.head is None:
                return "Required interfaces not available", SkillResult.FAILURE

            num_directions = max(1, num_directions)
            self.head.set_position(-15)
            self.mobility.rotate((2 * math.pi) / num_directions)
            return "Scan complete", SkillResult.SUCCESS

        def cancel(self):
            return "Cancelled"
    ```

    Use this style when you want deterministic physical control, digital/API operations, explicit sequencing, or custom sensor processing.
  </Accordion>

  <Accordion title="Policy-Defined Skills (End-to-End)">
    Policy-defined skills are learned policies trained from demonstrations. For manipulation, the current workflow uses ACT (Action Chunking with Transformers).

    ```json  theme={null}
    {
      "name": "pick_cup",
      "type": "learned",
      "guidelines": "Use when you need to pick up a cup",
      "execution": {
        "model_type": "act_policy",
        "checkpoint": "policy_step_50000.pth"
      }
    }
    ```

    Use this style when behavior is easier to learn from data than encode by hand, especially for visuomotor manipulation.
  </Accordion>
</AccordionGroup>

## Skill Directories

Skills are auto-discovered from two directories:

| Directory           | Purpose                         |
| ------------------- | ------------------------------- |
| `~/skills/`         | Your custom skills              |
| `innate-os/skills/` | Built-in templates and examples |

| Skill Type     | Format                                    |
| -------------- | ----------------------------------------- |
| Code-defined   | `*.py` Python class extending `Skill`     |
| Policy-defined | `<name>/metadata.json` + model checkpoint |

No registration required. Drop a file in the right place and the robot loads it on startup.


---

## Manual Triggering

_Source: https://docs.innate.bot/software/skills/manual-triggering.md_

# Manual Triggering

You can trigger skills manually through the Innate Controller App, bypassing the AI agent. This is useful for testing, debugging, or directly controlling the robot.

## Using the Skills Tab for Code-Defined Skills

1. Open the **Innate Controller App**

2. Navigate to the **Skills** tab -> Digital Skills.

3. Select a skill then press **Execute**

The robot will execute the skill without going through the agent's reasoning loop.

For skills that take parameters, the app shows input fields for each argument.

## Directly in Manual Control for Policy-Defined Skills

1. Go to the **Home** tab

2. Press **Manual**

3. Select a skill in the dropdown then press the ▶️ button.

The robot will execute the skill without going through the agent's reasoning loop.

## When to Use Manual Triggering

| Use Case           | Description                                   |
| ------------------ | --------------------------------------------- |
| **Testing**        | Verify a skill works before deploying         |
| **Debugging**      | Isolate skill behavior from agent logic       |
| **Direct control** | Run a specific action without voice/chat      |
| **Demos**          | Trigger skills on demand during presentations |


---

## Policy-Defined Skills

_Source: https://docs.innate.bot/software/skills/policy-defined-skills.md_

# Policy-Defined Skills

Policy-defined skills are neural network policies that run end-to-end—taking sensor input and directly outputting robot actions. Unlike code-defined skills where you write explicit logic, policy-defined skills learn behaviors from demonstration.

This approach works well for manipulation tasks where the variability of real-world scenarios makes explicit programming impractical.

## Two Types of Policies

| Type        | Definition                               | Use Case                          |
| ----------- | ---------------------------------------- | --------------------------------- |
| **Learned** | Neural network trained on demonstrations | Tasks requiring visual adaptation |
| **Replay**  | Recorded action sequence                 | Repeatable, fixed motions         |

## Learned Skills (ACT Policy)

Learned skills use **Action Chunking with Transformers (ACT)**—a neural network architecture that takes camera images and joint positions as input, and outputs action sequences.

### Metadata Structure

```json  theme={null}
{
    "name": "pick_socks",
    "type": "learned",
    "guidelines": "Use when you need to pick up socks from the floor",
    "execution": {
        "model_type": "act_policy",
        "checkpoint": "act_policy_step_135000.pth",
        "stats_file": "dataset_stats.pt",
        "action_dim": 10,
        "duration": 45.0,
        "start_pose": [-0.015, -0.399, 1.456, -1.135, -0.023, 0.833]
    }
}
```

### Execution Flow

1. **Load Policy**: Neural network checkpoint loaded into GPU memory

2. **Move to Start Pose**: Arm moves to consistent initial configuration

3. **Inference Loop (25Hz)**: Every 40ms:

   * Capture images from both cameras

   * Read current joint positions

   * Run policy forward pass

   * Output: 6 joint commands + 2 base velocity commands

4. **Progress Monitoring**: Early termination when progress > 95%

5. **End Pose**: Optionally return to safe configuration

### Key Characteristics

* **Reactive**: Continuously adjusts based on visual feedback

* **Adaptive**: Handles variation in object position, lighting, orientation

* **Coordinated**: Can move arm and base simultaneously

## Replay Skills

Replay skills play back pre-recorded action sequences. Simpler than learned skills, but deterministic and reliable.

### Metadata Structure

```json  theme={null}
{
    "name": "wave",
    "type": "replay",
    "guidelines": "Use when greeting someone or saying hello",
    "execution": {
        "model_type": "replay",
        "replay_file": "episode_0.h5",
        "replay_frequency": 50.0,
        "start_pose": [1.577, -0.6, 1.477, -0.738, 0.0, 0.0],
        "end_pose": [1.577, -0.6, 1.477, -0.738, 0.0, 0.0]
    }
}
```

### Execution Flow

1. **Load Recording**: H5 file containing timestamped actions

2. **Move to Start Pose**: Arm moves to recorded initial position

3. **Playback (50Hz)**: Execute recorded actions in sequence

4. **End Pose**: Return to specified configuration

## Execution Pipeline

Both skill types are executed by the **BehaviorServer**:

```text  theme={null}
BASIC calls skill
       |
       v
PrimitiveExecutionActionServer
       |
       v (physical skill detected)
BehaviorServer.ExecuteBehavior
       |
       +-- Learned --> Load policy, run inference loop
       |
       +-- Replay ---> Load H5 file, playback loop
       |
       v
Robot hardware (/mars/arm/commands, /cmd_vel)
```

## Creating New Skills

### Learned Skill Workflow

1. **Collect Demonstrations**: Teleoperate robot through task 10-100 times

2. **Train Policy**: Run ACT training pipeline to produce checkpoint

3. **Create Metadata**: Add `metadata.json` with execution parameters

4. **Deploy**: Place in `skills/<name>/` directory

### Replay Skill Workflow

1. **Record Episode**: Teleoperate through motion once, save to H5

2. **Create Metadata**: Add `metadata.json` with replay parameters

3. **Deploy**: Place in `skills/<name>/` directory

## Demonstration Quality

The quality of learned skills depends directly on demonstration quality:

| Good Demonstrations           | Poor Demonstrations         |
| ----------------------------- | --------------------------- |
| Consistent starting positions | Variable starting positions |
| Smooth, deliberate motions    | Hesitant, jerky motions     |
| Varied object positions       | Always same position        |
| Include error recovery        | Only perfect executions     |

## Skill Selection Guide

| Scenario                            | Recommended Type |
| ----------------------------------- | ---------------- |
| Task requires visual adaptation     | **Learned**      |
| Object position varies              | **Learned**      |
| Motion must be identical every time | **Replay**       |
| Simple gesture (wave, point)        | **Replay**       |
| Faster development cycle            | **Replay**       |


---

## Code-Defined Skills

_Source: https://docs.innate.bot/software/skills/code-defined-skills.md_

# Overview

export const SkillResultsTable = () => {
  const rows = [{
    status: "SUCCESS",
    meaning: "Skill completed its task."
  }, {
    status: "FAILURE",
    meaning: "Something went wrong."
  }, {
    status: "CANCELLED",
    meaning: "Skill was interrupted via cancel()."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Meaning</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.status}>
              <td>
                <span className="interface-param-badge">{row.status}</span>
              </td>
              <td>{row.meaning}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

export const SkillCoreMethodsTable = () => {
  const rows = [{
    method: "name",
    purpose: "Unique identifier the agent uses to call this skill."
  }, {
    method: "guidelines()",
    purpose: "Natural language instructions for when and how to use the skill."
  }, {
    method: "execute()",
    purpose: "The actual behavior. The signature defines the skill parameters."
  }, {
    method: "cancel()",
    purpose: "Clean shutdown when the user or agent interrupts."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Method</th>
            <th>Purpose</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.method}>
              <td>
                <span className="interface-method-pill">{row.method}</span>
              </td>
              <td>{row.purpose}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

Code-defined skills are Python classes that implement robot behaviors with explicit logic. The AI agent reads your code's function signature and docstrings to understand what the skill does and how to call it.

## Design Principles

The skill SDK is designed to be **pythonic**—you should be able to read a skill and immediately understand what it does.

### 1. The Agent Reads Your Code

The AI agent understands your skill through its Python signature:

```python  theme={null}
def execute(self, target: str, speed: float = 0.5):
    """Move toward the target object.

    Args:
        target: Object to approach (e.g., "cup", "person")
        speed: Movement speed in m/s
    """
```

The agent sees `execute(target: str, speed: float = 0.5)` and knows exactly how to call your skill. Type hints matter—they're your API contract with the AI.

### 2. One-Line Declarations

Dependencies are declared as class attributes, not boilerplate in `__init__`:

```python  theme={null}
class MySkill(Skill):
    # Hardware access - one line
    mobility = Interface(InterfaceType.MOBILITY)

    # Sensor data - one line
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)
```

The system automatically injects what you declare. No manual wiring.

### 3. Direct Access

Once declared, use your dependencies as normal Python attributes:

```python  theme={null}
def execute(self):
    if self.image:                    # Latest camera frame, updated at 50Hz
        self.mobility.rotate(0.5)     # Rotate 0.5 radians
```

No callbacks, no message passing, no ROS complexity. Just Python.

## The Skill Class

Every code-defined skill extends `Skill` and implements these methods:

```python  theme={null}
from brain_client.skill_types import Skill, SkillResult

class MySkill(Skill):
    @property
    def name(self):
        return "my_skill"  # Unique identifier

    def guidelines(self):
        """Tell the agent when to use this skill."""
        return "Use when you need to [do something specific]"

    def execute(self, param1: str, param2: float = 1.0):
        """Do the thing. Agent calls this with parsed arguments."""
        # Your logic here
        return "Result message", SkillResult.SUCCESS

    def cancel(self):
        """Stop gracefully when interrupted."""
        return "Cancelled"
```

<SkillCoreMethodsTable />

## Skill Results

Return a tuple of `(message, status)` from `execute()`:

```python  theme={null}
from brain_client.skill_types import SkillResult

def execute(self):
    if success:
        return "Task completed", SkillResult.SUCCESS
    elif self._cancelled:
        return "Interrupted by user", SkillResult.CANCELLED
    else:
        return "Something went wrong", SkillResult.FAILURE
```

<SkillResultsTable />

## Feedback

Send progress updates during long-running skills. The agent reads feedback in real-time and can act on it—for example, canceling the skill or triggering another one immediately:

```python  theme={null}
def execute(self):
    for i in range(10):
        self._send_feedback(f"Step {i+1}/10")
        # ... do work ...
    return "Done", SkillResult.SUCCESS
```

## Next Steps

* [**Navigation Interfaces**](/software/skills/code-defined-skills/navigation-interfaces) — Mobility control, rotation, velocity commands

* [**Body Control Interfaces**](/software/skills/code-defined-skills/body-control-interfaces) — Arm manipulation, head movement, IK

* [**Robot State**](/software/skills/code-defined-skills/robot-state) — Camera, odometry, map, sensor data

* [**Physical Skill Examples**](/software/skills/code-defined-skills/physical-skill-examples) — Full-body behaviors combining navigation + manipulation

* [**Digital Skills**](/software/skills/code-defined-skills/digital-skills) — APIs, email, web services


---

## Body Control Interfaces

_Source: https://docs.innate.bot/software/skills/code-defined-skills/body-control-interfaces.md_

# Body Control Interfaces

export const HeadTiltAnglesTable = () => {
  const rows = [{
    angle: "-25deg",
    view: "Floor and objects below."
  }, {
    angle: "0deg",
    view: "Straight ahead."
  }, {
    angle: "+15deg",
    view: "Faces and shelves above."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Angle</th>
            <th>View</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.angle}>
              <td>
                <span className="interface-param-badge">{row.angle}</span>
              </td>
              <td>{row.view}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

export const HeadInterfaceMethods = () => {
  const rows = [{
    method: "set_position()",
    params: [{
      name: "angle",
      type: "int"
    }],
    desc: "Set head tilt angle (from -25deg to +15deg)."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Method</th>
            <th>Parameters</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.method}>
              <td>
                <span className="interface-method-pill">{row.method}</span>
              </td>
              <td>
                {row.params?.length ? <div className="interface-method-params">
                    {row.params.map(param => <span key={`${row.method}-${param.name}`} className="interface-param-badge">
                        {param.name}
                        {param.type ? <span className="interface-param-type">: {param.type}</span> : null}
                      </span>)}
                  </div> : <span className="interface-no-params">None</span>}
              </td>
              <td>{row.desc}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

export const ManipulationInterfaceMethods = () => {
  const rows = [{
    method: "move_to_cartesian_pose()",
    params: [{
      name: "x",
      type: "float"
    }, {
      name: "y",
      type: "float"
    }, {
      name: "z",
      type: "float"
    }, {
      name: "roll",
      type: "float"
    }, {
      name: "pitch",
      type: "float"
    }, {
      name: "yaw",
      type: "float"
    }, {
      name: "duration",
      type: "float"
    }],
    desc: "Move the end-effector to a target Cartesian pose."
  }, {
    method: "goto_joint_state()",
    params: [{
      name: "joints",
      type: "list[float]"
    }],
    desc: "Move the arm to a target joint configuration (6 values)."
  }, {
    method: "get_current_orientation_rpy()",
    params: [],
    desc: "Get current end-effector orientation as roll/pitch/yaw values."
  }, {
    method: "get_current_end_effector_pose()",
    params: [],
    desc: "Get current end-effector pose (position + quaternion)."
  }, {
    method: "solve_ik()",
    params: [{
      name: "x",
      type: "float"
    }, {
      name: "y",
      type: "float"
    }, {
      name: "z",
      type: "float"
    }, {
      name: "roll",
      type: "float"
    }, {
      name: "pitch",
      type: "float"
    }, {
      name: "yaw",
      type: "float"
    }, {
      name: "timeout",
      type: "float"
    }],
    desc: "Solve inverse kinematics for a target pose without moving the arm."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Method</th>
            <th>Parameters</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.method}>
              <td>
                <span className="interface-method-pill">{row.method}</span>
              </td>
              <td>
                {row.params?.length ? <div className="interface-method-params">
                    {row.params.map(param => <span key={`${row.method}-${param.name}`} className="interface-param-badge">
                        {param.name}
                        {param.type ? <span className="interface-param-type">: {param.type}</span> : null}
                      </span>)}
                  </div> : <span className="interface-no-params">None</span>}
              </td>
              <td>{row.desc}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

The `ManipulationInterface` and `HeadInterface` give you direct control over the robot's arm and head. Use these for manipulation tasks, gestures, and camera positioning.

## ManipulationInterface

Declare the interface at class level:

```python  theme={null}
from brain_client.skill_types import Skill, Interface, InterfaceType

class MySkill(Skill):
    manipulation = Interface(InterfaceType.MANIPULATION)
```

### Methods

<ManipulationInterfaceMethods />

### Cartesian Control

Move the end-effector to a specific position and orientation:

```python  theme={null}
# Move to position (x, y, z) with orientation (roll, pitch, yaw)
self.manipulation.move_to_cartesian_pose(
    x=0.2, y=0.0, z=0.3,
    roll=0.0, pitch=0.0, yaw=0.0,
    duration=2.0
)
```

### Joint Control

Move directly to joint angles (6 joints):

```python  theme={null}
# Move to joint configuration [j1, j2, j3, j4, j5, j6]
self.manipulation.goto_joint_state([0, -0.5, 1.5, -1.0, 0, 0])
```

### Reading State

```python  theme={null}
# Get current end-effector pose
pose = self.manipulation.get_current_end_effector_pose()
# Returns: {'position': [x, y, z], 'orientation': [qx, qy, qz, qw]}

# Get orientation as roll/pitch/yaw
rpy = self.manipulation.get_current_orientation_rpy()
# Returns: {'roll': r, 'pitch': p, 'yaw': y}
```

### Inverse Kinematics

Check if a pose is reachable before moving:

```python  theme={null}
joints = self.manipulation.solve_ik(
    x=0.2, y=0.0, z=0.3,
    roll=0.0, pitch=0.0, yaw=0.0,
    timeout=1.0
)
if joints:
    self.manipulation.goto_joint_state(joints)
else:
    return "Pose unreachable", SkillResult.FAILURE
```

## HeadInterface

Control camera tilt:

```python  theme={null}
from brain_client.skill_types import Skill, Interface, InterfaceType

class MySkill(Skill):
    head = Interface(InterfaceType.HEAD)
```

### Methods

<HeadInterfaceMethods />

### Tilt Angles

<HeadTiltAnglesTable />

```python  theme={null}
self.head.set_position(-15)  # Look down at objects
self.head.set_position(0)    # Look straight ahead
self.head.set_position(10)   # Look up at faces
```

## Example: Wave

A skill that waves the arm:

```python  theme={null}
from brain_client.skill_types import Skill, SkillResult, Interface, InterfaceType
import time

class Wave(Skill):
    manipulation = Interface(InterfaceType.MANIPULATION)

    @property
    def name(self):
        return "wave"

    def guidelines(self):
        return "Use to wave at someone in greeting."

    def execute(self, times: int = 3):
        # Wave positions
        wave_left = [0.5, -0.3, 1.0, -0.5, 0.5, 0]
        wave_right = [0.5, -0.3, 1.0, -0.5, -0.5, 0]

        for i in range(times):
            if self._cancelled:
                return "Wave cancelled", SkillResult.CANCELLED

            self.manipulation.goto_joint_state(wave_left)
            time.sleep(0.3)
            self.manipulation.goto_joint_state(wave_right)
            time.sleep(0.3)

        return f"Waved {times} times", SkillResult.SUCCESS

    def cancel(self):
        self._cancelled = True
        return "Wave cancelled"
```

## Example: LookAtObject

A skill that adjusts head to look at objects:

```python  theme={null}
from brain_client.skill_types import Skill, SkillResult, Interface, InterfaceType

class LookAtObject(Skill):
    head = Interface(InterfaceType.HEAD)

    @property
    def name(self):
        return "look_at_object"

    def guidelines(self):
        return "Use to tilt camera to look at objects on the floor or shelves."

    def execute(self, location: str = "floor"):
        angles = {
            "floor": -25,
            "table": -10,
            "ahead": 0,
            "face": 10,
            "shelf": 15
        }

        angle = angles.get(location, 0)
        self.head.set_position(angle)

        return f"Looking at {location}", SkillResult.SUCCESS

    def cancel(self):
        return "Cannot cancel head movement"
```


---

## Navigation Interfaces

_Source: https://docs.innate.bot/software/skills/code-defined-skills/navigation-interfaces.md_

# Navigation Interfaces

export const NavigationUseCasesTable = () => {
  const rows = [{
    scenario: "Go to a saved location",
    recommendation: "Use built-in behavior (agent handles it)."
  }, {
    scenario: "Survey surroundings",
    recommendation: "Create a custom skill with rotate()."
  }, {
    scenario: "Follow a person",
    recommendation: "Create a custom skill with send_cmd_vel()."
  }, {
    scenario: "Fine positioning for manipulation",
    recommendation: "Create a custom skill."
  }, {
    scenario: "Patrol a route",
    recommendation: "Create a custom skill."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Scenario</th>
            <th>Recommendation</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.scenario}>
              <td>{row.scenario}</td>
              <td>{row.recommendation}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

export const NavigationInterfaceMethods = () => {
  const rows = [{
    method: "rotate()",
    params: [{
      name: "angle_radians",
      type: "float"
    }],
    desc: "Rotate in place (blocking, uses Nav2)."
  }, {
    method: "send_cmd_vel()",
    params: [{
      name: "linear_x",
      type: "float"
    }, {
      name: "angular_z",
      type: "float"
    }, {
      name: "duration",
      type: "float"
    }],
    desc: "Publish velocity commands (non-blocking)."
  }, {
    method: "rotate_in_place()",
    params: [{
      name: "angular_speed",
      type: "float"
    }, {
      name: "duration",
      type: "float"
    }],
    desc: "Rotate at a fixed angular speed for a set duration."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Method</th>
            <th>Parameters</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.method}>
              <td>
                <span className="interface-method-pill">{row.method}</span>
              </td>
              <td>
                {row.params?.length ? <div className="interface-method-params">
                    {row.params.map(param => <span key={`${row.method}-${param.name}`} className="interface-param-badge">
                        {param.name}
                        {param.type ? <span className="interface-param-type">: {param.type}</span> : null}
                      </span>)}
                  </div> : <span className="interface-no-params">None</span>}
              </td>
              <td>{row.desc}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

The `MobilityInterface` gives you direct control over the robot base—rotation, velocity commands, and movement. Use it for custom navigation behaviors that complement the built-in navigation.

## Core Navigation (Built-in)

The robot comes with built-in navigation that the agent calls *innately*. You don't need to implement this—it works out of the box.

**Do not modify** the core `navigate_to_position` skill. It's a system-level skill that the agent uses automatically. Modifying it could break navigation behavior.

When you tell the robot "go to the kitchen," the agent automatically:

1. Translates "kitchen" to map coordinates (if the location is saved)

2. Calls the built-in navigation skill

3. Monitors progress and handles obstacles

## MobilityInterface

Declare the interface at class level:

```python  theme={null}
from brain_client.skill_types import Skill, Interface, InterfaceType

class MySkill(Skill):
    mobility = Interface(InterfaceType.MOBILITY)
```

### Methods

<NavigationInterfaceMethods />

### Examples

```python  theme={null}
import math

# Rotate 90 degrees (blocking)
self.mobility.rotate(math.pi / 2)

# Drive forward for 2 seconds (non-blocking)
self.mobility.send_cmd_vel(linear_x=0.1, angular_z=0.0, duration=2.0)

# Spin in place
self.mobility.rotate_in_place(angular_speed=0.5, duration=3.0)
```

## When to Use

<NavigationUseCasesTable />

## Example: LookAround

A skill that rotates to survey the environment:

```python  theme={null}
from brain_client.skill_types import Skill, SkillResult, Interface, InterfaceType
import math

class LookAround(Skill):
    mobility = Interface(InterfaceType.MOBILITY)

    @property
    def name(self):
        return "look_around"

    def guidelines(self):
        return "Use when the robot needs to look in multiple directions."

    def execute(self, num_directions: int = 4):
        rotation_per_step = (2 * math.pi) / num_directions

        for i in range(num_directions):
            if self._cancelled:
                return "Survey cancelled", SkillResult.CANCELLED

            self._send_feedback(f"Looking direction {i+1}/{num_directions}")
            self.mobility.rotate(rotation_per_step)

        return "Survey complete", SkillResult.SUCCESS

    def cancel(self):
        self._cancelled = True
        return "Survey cancelled"
```


---

## Robot State

_Source: https://docs.innate.bot/software/skills/code-defined-skills/robot-state.md_

# Robot State

export const RobotStateAvailableTable = () => {
  const rows = [{
    state: "Camera Image",
    typeEnum: "RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64",
    description: "Latest frame (base64 JPEG)."
  }, {
    state: "Odometry",
    typeEnum: "RobotStateType.LAST_ODOM",
    description: "Position, orientation, and velocity."
  }, {
    state: "Map",
    typeEnum: "RobotStateType.LAST_MAP",
    description: "Occupancy grid."
  }, {
    state: "Head Position",
    typeEnum: "RobotStateType.LAST_HEAD_POSITION",
    description: "Head tilt angle."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>State</th>
            <th>Type Enum</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.typeEnum}>
              <td>{row.state}</td>
              <td>
                <span className="interface-param-badge">{row.typeEnum}</span>
              </td>
              <td>{row.description}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

The `RobotState` descriptor gives you access to sensor data—camera images, odometry, maps, and more. Declared state is **automatically updated at 50Hz** while your skill runs.

## Declaration

Declare state dependencies as class attributes:

```python  theme={null}
from brain_client.skill_types import Skill, RobotState, RobotStateType

class MySkill(Skill):
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)
    odom = RobotState(RobotStateType.LAST_ODOM)
```

The system injects and updates these values automatically. Always check for `None` on first access.

## Available State

<RobotStateAvailableTable />

## Camera Image

The main camera image as a base64-encoded JPEG:

```python  theme={null}
class MySkill(Skill):
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    def execute(self):
        if not self.image:
            return "No image available", SkillResult.FAILURE

        # Decode base64 to bytes
        import base64
        image_bytes = base64.b64decode(self.image)

        # Use with PIL
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))

        # Or send to vision API
        response = vision_api.analyze(self.image)
```

## Odometry

Current position, orientation, and velocity:

```python  theme={null}
class MySkill(Skill):
    odom = RobotState(RobotStateType.LAST_ODOM)

    def execute(self):
        if self.odom:
            x = self.odom.pose.pose.position.x
            y = self.odom.pose.pose.position.y
            # orientation as quaternion
            qz = self.odom.pose.pose.orientation.z
            qw = self.odom.pose.pose.orientation.w
```

## Map

The occupancy grid map:

```python  theme={null}
class MySkill(Skill):
    map_data = RobotState(RobotStateType.LAST_MAP)

    def execute(self):
        if self.map_data:
            width = self.map_data.info.width
            height = self.map_data.info.height
            resolution = self.map_data.info.resolution
            data = self.map_data.data  # 1D array of occupancy values
```

## Head Position

Current head tilt angle:

```python  theme={null}
class MySkill(Skill):
    head_pos = RobotState(RobotStateType.LAST_HEAD_POSITION)

    def execute(self):
        if self.head_pos:
            current_angle = self.head_pos
            # Returns int: -25 to +15
```

## Example: CaptureImages

A skill that captures images while rotating:

```python  theme={null}
from brain_client.skill_types import (
    Skill, SkillResult, Interface, InterfaceType, RobotState, RobotStateType
)
import math

class CaptureImages(Skill):
    mobility = Interface(InterfaceType.MOBILITY)
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    @property
    def name(self):
        return "capture_images"

    def guidelines(self):
        return "Use to capture images from multiple directions."

    def execute(self, num_directions: int = 4):
        images = []
        rotation_step = (2 * math.pi) / num_directions

        for i in range(num_directions):
            if self._cancelled:
                return "Capture cancelled", SkillResult.CANCELLED

            # Capture current frame
            if self.image:
                images.append(self.image)
                self._send_feedback(f"Captured {i+1}/{num_directions}")

            # Rotate to next position
            if i < num_directions - 1:
                self.mobility.rotate(rotation_step)

        return f"Captured {len(images)} images", SkillResult.SUCCESS

    def cancel(self):
        self._cancelled = True
        return "Capture cancelled"
```

## Example: MonitorPosition

A skill that tracks robot movement:

```python  theme={null}
from brain_client.skill_types import Skill, SkillResult, RobotState, RobotStateType
import math
import time

class MonitorPosition(Skill):
    odom = RobotState(RobotStateType.LAST_ODOM)

    @property
    def name(self):
        return "monitor_position"

    def guidelines(self):
        return "Use to monitor robot position for a duration."

    def execute(self, duration: float = 5.0):
        if not self.odom:
            return "Odometry not available", SkillResult.FAILURE

        start_x = self.odom.pose.pose.position.x
        start_y = self.odom.pose.pose.position.y
        start_time = time.time()

        while time.time() - start_time < duration:
            if self._cancelled:
                return "Monitoring cancelled", SkillResult.CANCELLED

            x = self.odom.pose.pose.position.x
            y = self.odom.pose.pose.position.y
            distance = math.sqrt((x - start_x)**2 + (y - start_y)**2)

            self._send_feedback(f"Moved {distance:.2f}m from start")
            time.sleep(0.5)

        return f"Monitoring complete", SkillResult.SUCCESS

    def cancel(self):
        self._cancelled = True
        return "Monitoring cancelled"
```


---

## Digital Skills

_Source: https://docs.innate.bot/software/skills/code-defined-skills/digital-skills.md_

# Digital Skills

export const DigitalStateTypesTable = () => {
  const rows = [{
    stateType: "LAST_MAIN_CAMERA_IMAGE_B64",
    description: "Latest camera frame (base64 JPEG)."
  }, {
    stateType: "LAST_ODOM",
    description: "Current odometry."
  }, {
    stateType: "LAST_MAP",
    description: "Occupancy grid."
  }, {
    stateType: "LAST_HEAD_POSITION",
    description: "Head tilt angle."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>State Type</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.stateType}>
              <td>
                <span className="interface-param-badge">{row.stateType}</span>
              </td>
              <td>{row.description}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

export const DigitalSendEmailParametersTable = () => {
  const rows = [{
    parameter: "subject",
    type: "str",
    required: "Yes",
    description: "Email subject line."
  }, {
    parameter: "message",
    type: "str",
    required: "Yes",
    description: "Email body content."
  }, {
    parameter: "recipients",
    type: "list[str]",
    required: "No",
    description: "Recipients (defaults to configured list)."
  }];
  return <div className="interface-methods-table-wrap">
      <table className="interface-methods-table">
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Type</th>
            <th>Required</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => <tr key={row.parameter}>
              <td>
                <span className="interface-method-pill">{row.parameter}</span>
              </td>
              <td>
                <span className="interface-param-badge">{row.type}</span>
              </td>
              <td>
                <span className="interface-param-badge">{row.required}</span>
              </td>
              <td>{row.description}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
};

Digital skills enable the robot to interact with external services—sending emails, making API calls, retrieving information. These are always code skills, implementing explicit protocols and handling authentication, errors, and network conditions.

## Characteristics

Unlike physical skills that deal with real-world variability, digital skills operate in a deterministic domain:

* **Protocol-based**: Follow defined APIs and standards

* **Atomic**: Many operations cannot be cancelled once started

* **Reliable**: Once working, behavior is consistent

* **Network-dependent**: Must handle connectivity issues

## Built-in Skills

### SendEmail

Sends email notifications, typically for alerts or status updates.

```python  theme={null}
class SendEmail(Skill):
    @property
    def name(self):
        return "send_email"

    def guidelines(self):
        return (
            "Use to send an emergency email notification. Provide a subject and "
            "message. You can optionally provide a list of recipients, otherwise "
            "it will be sent to the default list. This should be used when a "
            "potential emergency is detected and assistance might be required."
        )

    def execute(self, subject: str, message: str, recipients: list[str] = None):
        # Send via SMTP
        # Returns (message, SkillResult)
```

**Parameters:**

<DigitalSendEmailParametersTable />

### SendPictureViaEmail

Sends an email with the robot's current camera view attached.

```python  theme={null}
class SendPictureViaEmail(Skill):
    # Declare camera image dependency - updated at 50Hz while skill runs
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    def execute(self, subject: str, message: str, recipient: str = None):
        if not self.image:
            return "No image available to send", SkillResult.FAILURE
        # Attach image and send
```

This skill demonstrates **state dependencies**—using the `RobotState` descriptor to declare required robot state that the system updates at 50Hz.

### RetrieveEmails

Fetches recent emails from configured account.

```python  theme={null}
class RetrieveEmails(Skill):
    def guidelines(self):
        return (
            "Use to retrieve recent emails from the configured email account. "
            "Provide the number of emails to retrieve (default is 5). "
            "Returns email subjects and content."
        )

    def execute(self, count: int = 5):
        # Connect to IMAP, fetch emails
        # Returns formatted email list
```

## Creating Digital Skills

### Template

```python  theme={null}
import os
from brain_client.skill_types import Skill, SkillResult

class MyDigitalSkill(Skill):
    def __init__(self, logger):
        super().__init__(logger)
        self.api_key = os.environ.get("SERVICE_API_KEY")
        if not self.api_key:
            raise ValueError("SERVICE_API_KEY not configured")

    @property
    def name(self):
        return "my_digital_skill"

    def guidelines(self):
        return "Use when [describe appropriate use cases]"

    def execute(self, param: str):
        try:
            # Call external service
            result = self._call_service(param)
            return f"Success: {result}", SkillResult.SUCCESS
        except TimeoutError:
            return "Service timed out", SkillResult.FAILURE
        except Exception as e:
            return f"Error: {e}", SkillResult.FAILURE

    def cancel(self):
        return "Operation cannot be cancelled"
```

### Best Practices

**Authentication**

* Store credentials in environment variables or secret managers

* Never hardcode passwords or API keys

* Validate credentials at initialization

**Error Handling**

```python  theme={null}
def execute(self, query: str):
    try:
        response = self.client.call(query, timeout=10)
        return f"Result: {response}", SkillResult.SUCCESS
    except RateLimitError:
        return "Rate limit exceeded", SkillResult.FAILURE
    except NetworkError:
        return "Network unavailable", SkillResult.FAILURE
    except Exception as e:
        return f"Unexpected error: {e}", SkillResult.FAILURE
```

**Timeouts**

* Always set explicit timeouts on network calls

* Prevent blocking indefinitely on slow services

**Idempotency**

* Design operations to be safely retryable when possible

* Consider partial failure scenarios

## Requesting Robot State

Skills declare sensor data dependencies using the `RobotState` descriptor:

```python  theme={null}
from brain_client.skill_types import RobotState, RobotStateType

class MySkill(Skill):
    # Declare state dependencies at class level
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)
    odom = RobotState(RobotStateType.LAST_ODOM)

    def execute(self):
        if self.image:
            # Use the latest camera frame
            pass
```

The system automatically updates declared state at 50Hz while your skill runs. Always check for `None` on first access.

Available state types:

<DigitalStateTypesTable />

See [Robot State](/software/skills/code-defined-skills/robot-state) for more details on the RobotState system.

## Cancellation

Many digital operations are atomic and cannot be meaningfully cancelled:

```python  theme={null}
def cancel(self):
    return "Email sending is an atomic operation that cannot be canceled once started"
```

BASIC understands this limitation and factors it into planning decisions.


---

## Physical Skill Examples

_Source: https://docs.innate.bot/software/skills/code-defined-skills/physical-skill-examples.md_

# Physical Skill Examples

Complete examples of skills that combine navigation, manipulation, and sensor data to create full-body robot behaviors.

## ScanAndWave

Rotate to find a person, then wave:

```python  theme={null}
from brain_client.skill_types import (
    Skill, SkillResult, Interface, InterfaceType, RobotState, RobotStateType
)
import math

class ScanAndWave(Skill):
    """Rotate to scan for people, then wave when found."""

    mobility = Interface(InterfaceType.MOBILITY)
    manipulation = Interface(InterfaceType.MANIPULATION)
    head = Interface(InterfaceType.HEAD)
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    @property
    def name(self):
        return "scan_and_wave"

    def guidelines(self):
        return "Use when greeting someone in the room."

    def execute(self):
        self._cancelled = False

        # Look up to see faces
        self.head.set_position(10)

        # Scan 360 degrees
        for i in range(8):
            if self._cancelled:
                return "Cancelled", SkillResult.CANCELLED

            self._send_feedback(f"Scanning direction {i+1}/8")

            if self.image:
                # Check for person (simplified - use vision API in practice)
                person_detected = self._detect_person(self.image)
                if person_detected:
                    self._wave()
                    return "Found person and waved", SkillResult.SUCCESS

            self.mobility.rotate(math.pi / 4)

        return "No person found", SkillResult.SUCCESS

    def _detect_person(self, image):
        # Placeholder - integrate with vision API
        return False

    def _wave(self):
        wave_left = [0.5, -0.3, 1.0, -0.5, 0.5, 0]
        wave_right = [0.5, -0.3, 1.0, -0.5, -0.5, 0]

        for _ in range(3):
            self.manipulation.goto_joint_state(wave_left)
            self.manipulation.goto_joint_state(wave_right)

    def cancel(self):
        self._cancelled = True
        self.mobility.send_cmd_vel(0, 0)
        return "Scan cancelled"
```

## PickupRoutine

Position, look down, and prepare arm for pickup:

```python  theme={null}
from brain_client.skill_types import (
    Skill, SkillResult, Interface, InterfaceType, RobotState, RobotStateType
)

class PickupRoutine(Skill):
    """Position robot and arm for object pickup."""

    mobility = Interface(InterfaceType.MOBILITY)
    manipulation = Interface(InterfaceType.MANIPULATION)
    head = Interface(InterfaceType.HEAD)
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    # Safe arm positions
    HOME_POSE = [0, -0.5, 1.5, -1.0, 0, 0]
    READY_POSE = [0, -0.3, 1.0, -0.8, 0, 0]

    @property
    def name(self):
        return "pickup_routine"

    def guidelines(self):
        return "Use to prepare for picking up an object in front of the robot."

    def execute(self, approach_distance: float = 0.3):
        self._cancelled = False

        # Step 1: Safe starting position
        self._send_feedback("Moving arm to safe position")
        self.manipulation.goto_joint_state(self.HOME_POSE)

        if self._cancelled:
            return "Cancelled", SkillResult.CANCELLED

        # Step 2: Look down at target area
        self._send_feedback("Looking at target area")
        self.head.set_position(-20)

        # Step 3: Approach slowly
        self._send_feedback("Approaching target")
        self.mobility.send_cmd_vel(linear_x=0.05, angular_z=0, duration=approach_distance / 0.05)

        if self._cancelled:
            return "Cancelled", SkillResult.CANCELLED

        # Step 4: Move arm to ready position
        self._send_feedback("Preparing arm")
        self.manipulation.goto_joint_state(self.READY_POSE)

        return "Ready for pickup", SkillResult.SUCCESS

    def cancel(self):
        self._cancelled = True
        self.mobility.send_cmd_vel(0, 0)
        return "Pickup routine cancelled"
```

## PatrolAndMonitor

Patrol between positions while monitoring camera:

```python  theme={null}
from brain_client.skill_types import (
    Skill, SkillResult, Interface, InterfaceType, RobotState, RobotStateType
)
import time

class PatrolAndMonitor(Skill):
    """Rotate between positions and capture images."""

    mobility = Interface(InterfaceType.MOBILITY)
    head = Interface(InterfaceType.HEAD)
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    @property
    def name(self):
        return "patrol_and_monitor"

    def guidelines(self):
        return "Use for surveillance - rotates and captures images at each position."

    def execute(self, positions: int = 4, duration: float = 30.0):
        self._cancelled = False
        images = []
        rotation_per_position = (2 * 3.14159) / positions
        start_time = time.time()

        while time.time() - start_time < duration:
            for i in range(positions):
                if self._cancelled:
                    return f"Patrol cancelled. Captured {len(images)} images.", SkillResult.CANCELLED

                # Scan head up and down at each position
                for angle in [-15, 0, 10]:
                    self.head.set_position(angle)
                    time.sleep(0.5)

                    if self.image:
                        images.append(self.image)
                        self._send_feedback(f"Captured image {len(images)}")

                # Rotate to next position
                self.mobility.rotate(rotation_per_position)

        return f"Patrol complete. Captured {len(images)} images.", SkillResult.SUCCESS

    def cancel(self):
        self._cancelled = True
        self.mobility.send_cmd_vel(0, 0)
        return "Patrol cancelled"
```

## InspectObject

Approach an object and examine it from multiple angles:

```python  theme={null}
from brain_client.skill_types import (
    Skill, SkillResult, Interface, InterfaceType, RobotState, RobotStateType
)
import math

class InspectObject(Skill):
    """Move around an object to inspect it from multiple angles."""

    mobility = Interface(InterfaceType.MOBILITY)
    head = Interface(InterfaceType.HEAD)
    image = RobotState(RobotStateType.LAST_MAIN_CAMERA_IMAGE_B64)

    @property
    def name(self):
        return "inspect_object"

    def guidelines(self):
        return "Use to examine an object from multiple angles. Robot should be near the object."

    def execute(self, angles: int = 4):
        self._cancelled = False
        images = []
        rotation_per_angle = (2 * math.pi) / angles

        # Look down at object
        self.head.set_position(-15)

        for i in range(angles):
            if self._cancelled:
                return "Inspection cancelled", SkillResult.CANCELLED

            self._send_feedback(f"Capturing angle {i+1}/{angles}")

            # Capture from current angle
            if self.image:
                images.append(self.image)

            # Orbit around (rotate, then strafe)
            self.mobility.rotate(rotation_per_angle)

        return f"Inspection complete - {len(images)} views captured", SkillResult.SUCCESS

    def cancel(self):
        self._cancelled = True
        self.mobility.send_cmd_vel(0, 0)
        return "Inspection cancelled"
```

## GoHomePosition

Return to a safe home configuration:

```python  theme={null}
from brain_client.skill_types import Skill, SkillResult, Interface, InterfaceType

class GoHomePosition(Skill):
    """Return arm and head to home positions."""

    manipulation = Interface(InterfaceType.MANIPULATION)
    head = Interface(InterfaceType.HEAD)

    HOME_ARM = [0, -0.5, 1.5, -1.0, 0, 0]

    @property
    def name(self):
        return "go_home_position"

    def guidelines(self):
        return """
        Use to return the robot's arm and head to safe home positions.
        Do not use if carrying something.
        """

    def execute(self):
        self._cancelled = False

        # Arm first (priority for safety)
        self._send_feedback("Moving arm to home")
        self.manipulation.goto_joint_state(self.HOME_ARM)

        if self._cancelled:
            return "Cancelled", SkillResult.CANCELLED

        # Then head
        self._send_feedback("Centering head")
        self.head.set_position(0)

        return "Home position reached", SkillResult.SUCCESS

    def cancel(self):
        self._cancelled = True
        return "Go home cancelled"
```


---

# Software — ROS2

## ROS2 Core

_Source: https://docs.innate.bot/software/ros2-core.md_

# ROS2 Overview

## Do I need to know ROS2?

**For most developers: no.** The Agent and Skill abstractions handle all the ROS2 complexity for you. You can build powerful robot applications without ever touching a ROS2 topic or service directly.

However, if you're a roboticist who wants low-level access to sensor data, custom motion control, or integration with other ROS2 systems, MARS gives you full access to the underlying ROS2 layer.

***

## What is ROS2?

ROS2 (Robot Operating System 2) is a middleware framework for robotics. It provides:

* **Topics**: Pub/sub messaging for streaming data (camera images, odometry, commands)

* **Services**: Request/response calls for one-off operations (turn on lights, get status)

* **Actions**: Long-running tasks with feedback (navigate to a point, execute a trajectory)

MARS runs ROS2 Humble on Ubuntu 22.04, with Zenoh as the DDS (networking) layer.

***

## Architecture Overview

The Innate OS has two main package groups:

### Brain (the "thinking" layer)

* **brain\_client**: The main orchestrator that runs agents, loads skills, and bridges to BASIC (cloud agent)

* **brain\_messages**: Custom message types for the brain system

* **manipulation**: Behavior server for arm control using learned policies

### Maurice Bot (the "body" layer)

* **maurice\_bringup**: Hardware initialization (cameras, battery, UART)

* **maurice\_arm**: Arm kinematics and motion planning (MoveIt2)

* **maurice\_nav**: Navigation stack (Nav2, SLAM)

* **maurice\_cam**: Camera drivers (OAK-D via DepthAI)

* **maurice\_msgs**: Custom messages for MARS hardware

* And several more for simulation, logging, and Bluetooth provisioning

***

## Common Use Cases

**"I want to read raw camera data"** → Subscribe to `/oak/rgb/image_raw` (sensor\_msgs/Image)

**"I want to manually drive the robot"** → Publish to `/cmd_vel` (geometry\_msgs/Twist)

**"I want to check battery level"** → Subscribe to `/battery_state` (sensor\_msgs/BatteryState)

**"I want to move the arm to a specific position"** → Use the `/goto_js` service or MoveIt2 interfaces (see advanced docs)

***

## Visualization

You can visualize ROS2 data with either RViz or Foxglove. If you are on Linux, RViz is the standard option. If you are not on Linux, use **Foxglove** with the Foxglove Bridge running on MARS.

### RViz (Linux)

Use RViz to inspect frames, point clouds, LiDAR, trajectories, and robot state directly from a Linux ROS2 workstation.

### Foxglove Bridge (non-Linux)

If you do not have Linux, run Foxglove Bridge on the robot and connect from [Foxglove](https://app.foxglove.dev).

Typical flow:

<Steps>
  <Step title="SSH into MARS">
    Connect to the robot over SSH on the same network.
  </Step>

  <Step title="Start Foxglove Bridge">
    Run the Foxglove Bridge node on MARS so topics are exposed over WebSocket.
  </Step>

  <Step title="Open Foxglove and connect">
    In your browser, open [app.foxglove.dev](https://app.foxglove.dev) and connect to the robot bridge endpoint.
  </Step>
</Steps>

***

## Going Deeper

Use these ROS2 sections:

* [Topics](/software/ros2/topics)
* [Services](/software/ros2/services)
* [Actions](/software/ros2/actions)
* [Navigation Stack](/software/ros2/navigation-stack)
* [Manipulation Stack](/software/ros2/manipulation-stack)
* [Debugging](/software/ros2/debugging)


---

## Topics

_Source: https://docs.innate.bot/software/ros2/topics.md_

# Topics

export const RosTopicsInterface = () => {
  const topicSections = [{
    id: "mobility",
    title: "Mobility",
    rows: [{
      topic: "/cmd_vel",
      dir: "SUB",
      msgType: "geometry_msgs/Twist",
      desc: "Velocity commands for robot base motion."
    }, {
      topic: "/odom",
      dir: "PUB",
      msgType: "nav_msgs/Odometry",
      desc: "Odometry estimate (position, orientation, and velocity)."
    }]
  }, {
    id: "system",
    title: "System",
    rows: [{
      topic: "/battery_state",
      dir: "PUB",
      msgType: "sensor_msgs/BatteryState",
      desc: "Battery level, voltage, and charging status."
    }, {
      topic: "/scan",
      dir: "PUB",
      msgType: "sensor_msgs/LaserScan",
      desc: "LiDAR scan data from the RPLidar stack."
    }]
  }, {
    id: "cameras",
    title: "Cameras",
    rows: [{
      topic: "/mars/main_camera/image",
      dir: "PUB",
      msgType: "sensor_msgs/Image",
      desc: "Main front-facing RGB stream."
    }, {
      topic: "/mars/arm/image_raw",
      dir: "PUB",
      msgType: "sensor_msgs/Image",
      desc: "Gripper-mounted RGB camera feed for manipulation."
    }, {
      topic: "/oak/rgb/image_raw",
      dir: "PUB",
      msgType: "sensor_msgs/Image",
      desc: "Alternative camera topic from OAK-D pipeline."
    }]
  }, {
    id: "arm",
    title: "Arm",
    rows: [{
      topic: "/mars/arm/state",
      dir: "PUB",
      msgType: "sensor_msgs/JointState",
      desc: "Current arm joint states from robot actuators."
    }, {
      topic: "/mars/arm/commands",
      dir: "SUB",
      msgType: "std_msgs/Float64MultiArray",
      desc: "Direct arm joint command input topic."
    }, {
      topic: "/leader/state",
      dir: "PUB",
      msgType: "sensor_msgs/JointState",
      desc: "Leader arm joint states when teleoperation is enabled."
    }, {
      topic: "/joint_states",
      dir: "PUB",
      msgType: "sensor_msgs/JointState",
      desc: "Combined joint state stream for robot visualization and tools."
    }]
  }, {
    id: "brain",
    title: "Brain",
    rows: [{
      topic: "/ws_messages",
      dir: "SUB",
      msgType: "std_msgs/String",
      desc: "Incoming WebSocket payloads from cloud-side orchestration."
    }, {
      topic: "/ws_outgoing",
      dir: "PUB",
      msgType: "std_msgs/String",
      desc: "Outgoing WebSocket payloads emitted by robot-side brain client."
    }]
  }];
  return <AccordionGroup>
      {topicSections.map(section => <Accordion key={section.id} title={section.title} defaultOpen={section.id === "mobility" || section.id === "system"}>
          <div className="ros-topic-table-wrap">
            <table className="ros-topic-table">
              <thead>
                <tr>
                  <th>Topic Name</th>
                  <th>Dir</th>
                  <th>Message Type</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {section.rows.map(row => <tr key={row.topic}>
                    <td>
                      <span className="ros-topic-code ros-topic-path">{row.topic}</span>
                    </td>
                    <td>
                      <span className={`ros-topic-tag ${row.dir === "PUB" ? "ros-topic-tag-pub" : "ros-topic-tag-sub"}`}>
                        {row.dir}
                      </span>
                    </td>
                    <td>
                      <span className="ros-topic-code ros-topic-msg">{row.msgType}</span>
                    </td>
                    <td>{row.desc}</td>
                  </tr>)}
              </tbody>
            </table>
          </div>
        </Accordion>)}
    </AccordionGroup>;
};

Use ROS2 topics for streaming robot state and continuous commands.

## Topic Interface

<RosTopicsInterface />

## How to read PUB/SUB

The **Dir** column is from the robot runtime perspective. `PUB` means MARS publishes that topic and you subscribe to it. `SUB` means MARS subscribes to that topic and you can publish commands to it.

## Quick commands

```bash  theme={null}
ros2 topic list
ros2 topic list -t
ros2 topic echo /battery_state
ros2 topic hz /scan
ros2 topic info /cmd_vel
```

<CardGroup cols={2}>
  <Card title="Services" href="/software/ros2/services">
    Request/response interfaces for map, system, and runtime control.
  </Card>

  <Card title="Actions" href="/software/ros2/actions">
    Long-running goal APIs with feedback and cancellation.
  </Card>
</CardGroup>


---

## Services

_Source: https://docs.innate.bot/software/ros2/services.md_

# Services

export const RosServicesInterface = () => {
  const serviceSections = [{
    id: "arm-control",
    title: "Arm Control",
    rows: [{
      service: "/mars/arm/goto_js",
      type: "maurice_msgs/GotoJS",
      desc: "Move arm joints to target positions over a specified duration."
    }, {
      service: "/mars/head/set_ai_position",
      type: "std_srvs/Trigger",
      desc: "Set the head to the default AI viewing position."
    }]
  }, {
    id: "navigation-maps",
    title: "Navigation and Maps",
    rows: [{
      service: "/grid_localize",
      type: "maurice_msgs/GridLocalize",
      desc: "Estimate robot pose on map from current scan."
    }, {
      service: "/change_map",
      type: "brain_messages/ChangeMap",
      desc: "Switch the active saved map."
    }, {
      service: "/save_map",
      type: "brain_messages/SaveMap",
      desc: "Save the current mapping session."
    }, {
      service: "/delete_map",
      type: "brain_messages/DeleteMap",
      desc: "Delete a saved map."
    }, {
      service: "/change_navigation_mode",
      type: "brain_messages/ChangeNavigationMode",
      desc: "Switch between mapfree, mapping, and navigation modes."
    }]
  }, {
    id: "system",
    title: "System",
    rows: [{
      service: "/light_command",
      type: "maurice_msgs/LightCommand",
      desc: "Control LED mode, interval, and RGB color."
    }, {
      service: "/shutdown",
      type: "maurice_msgs/Shutdown",
      desc: "Trigger robot shutdown sequence."
    }, {
      service: "/set_robot_name",
      type: "maurice_msgs/SetRobotName",
      desc: "Set display name used by app and hostname conversion."
    }, {
      service: "/trigger_update",
      type: "maurice_msgs/TriggerUpdate",
      desc: "Trigger update flow on the robot."
    }]
  }, {
    id: "brain-agent",
    title: "Brain and Agent Runtime",
    rows: [{
      service: "/get_available_primitives",
      type: "brain_messages/GetAvailablePrimitives",
      desc: "List available skills (primitives)."
    }, {
      service: "/get_available_directives",
      type: "brain_messages/GetAvailableDirectives",
      desc: "List available agents (directives)."
    }, {
      service: "/get_available_behaviors",
      type: "brain_messages/GetAvailableBehaviors",
      desc: "List available learned manipulation behaviors."
    }, {
      service: "/reset_brain",
      type: "brain_messages/ResetBrain",
      desc: "Reset brain runtime state."
    }, {
      service: "/set_directive_on_startup",
      type: "brain_messages/SetDirectiveOnStartup",
      desc: "Choose which agent should auto-load at boot."
    }, {
      service: "/get_chat_history",
      type: "brain_messages/GetChatHistory",
      desc: "Retrieve BASIC conversation history."
    }]
  }, {
    id: "data-recording",
    title: "Data Recording",
    rows: [{
      service: "/new_task",
      type: "brain_messages/ManipulationTask",
      desc: "Start recording a new manipulation task."
    }, {
      service: "/new_episode",
      type: "std_srvs/Trigger",
      desc: "Start a new episode inside current task."
    }, {
      service: "/save_episode",
      type: "std_srvs/Trigger",
      desc: "Save current episode."
    }, {
      service: "/cancel_episode",
      type: "std_srvs/Trigger",
      desc: "Discard current episode."
    }, {
      service: "/end_task",
      type: "std_srvs/Trigger",
      desc: "Finalize current task recording."
    }, {
      service: "/get_task_metadata",
      type: "brain_messages/GetTaskMetadata",
      desc: "Read metadata for a recording task."
    }, {
      service: "/get_dataset_info",
      type: "brain_messages/GetDatasetInfo",
      desc: "Read dataset summary and statistics."
    }]
  }];
  return <AccordionGroup>
      {serviceSections.map((section, idx) => <Accordion key={section.id} title={section.title} defaultOpen={idx < 2}>
          <div className="ros-topic-table-wrap">
            <table className="ros-topic-table">
              <thead>
                <tr>
                  <th>Service Name</th>
                  <th>Type</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {section.rows.map(row => <tr key={row.service}>
                    <td>
                      <span className="ros-topic-code ros-topic-path">{row.service}</span>
                    </td>
                    <td>
                      <span className="ros-topic-code ros-topic-msg">{row.type}</span>
                    </td>
                    <td>{row.desc}</td>
                  </tr>)}
              </tbody>
            </table>
          </div>
        </Accordion>)}
    </AccordionGroup>;
};

Use ROS2 services for request/response operations.

## Service Interface

<RosServicesInterface />

## When to use a service

Use a service when you need a single request/response interaction (for example "do this now and return success/failure"). Use [Topics](/software/ros2/topics) for continuous streaming and [Actions](/software/ros2/actions) for long-running operations with progress/cancel.

## Quick commands

```bash  theme={null}
ros2 service list
ros2 service list -t
ros2 service type /mars/arm/goto_js
ros2 interface show maurice_msgs/srv/GotoJS
ros2 service call /mars/head/set_ai_position std_srvs/srv/Trigger {}
```

## Common call examples

### Set LED color

```bash  theme={null}
ros2 service call /light_command maurice_msgs/srv/LightCommand \
  "{mode: 1, interval: 0, r: 64, g: 31, b: 251}"
```

### Move arm in joint space

```bash  theme={null}
ros2 service call /mars/arm/goto_js maurice_msgs/srv/GotoJS \
  "{data: {data: [0.0, -0.8, 1.2, -0.6, 0.0, 0.0]}, time: 2000}"
```

### Switch navigation mode

```bash  theme={null}
ros2 service call /change_navigation_mode brain_messages/srv/ChangeNavigationMode \
  "{mode: navigation}"
```

<CardGroup cols={2}>
  <Card title="Topics" href="/software/ros2/topics">
    Streaming state and command channels.
  </Card>

  <Card title="Actions" href="/software/ros2/actions">
    Long-running tasks with feedback and cancellation.
  </Card>
</CardGroup>


---

## Actions

_Source: https://docs.innate.bot/software/ros2/actions.md_

# Actions

export const RosActionsInterface = () => {
  const actionSections = [{
    id: "navigation-actions",
    title: "Navigation Actions",
    rows: [{
      action: "/navigate_to_pose",
      type: "nav2_msgs/NavigateToPose",
      desc: "Navigate to a target pose in map frame with feedback and result."
    }, {
      action: "/follow_waypoints",
      type: "nav2_msgs/FollowWaypoints",
      desc: "Execute a sequence of map waypoints."
    }]
  }, {
    id: "manipulation-actions",
    title: "Manipulation Actions",
    rows: [{
      action: "/execute_behavior",
      type: "brain_messages/ExecuteBehavior",
      desc: "Execute a learned manipulation behavior with runtime feedback."
    }, {
      action: "/execute_policy",
      type: "brain_messages/ExecutePolicy",
      desc: "Run a policy for a configured duration."
    }, {
      action: "/execute_primitive",
      type: "brain_messages/ExecutePrimitive",
      desc: "Execute a skill/primitive with JSON inputs."
    }]
  }];
  return <AccordionGroup>
      {actionSections.map((section, idx) => <Accordion key={section.id} title={section.title} defaultOpen={idx === 0}>
          <span className="ros-topic-badge">{section.rows.length} actions</span>
          <div className="ros-topic-table-wrap" style={{
    marginTop: "10px"
  }}>
            <table className="ros-topic-table">
              <thead>
                <tr>
                  <th>Action Name</th>
                  <th>Type</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {section.rows.map(row => <tr key={row.action}>
                    <td>
                      <span className="ros-topic-code ros-topic-path">{row.action}</span>
                    </td>
                    <td>
                      <span className="ros-topic-code ros-topic-msg">{row.type}</span>
                    </td>
                    <td>{row.desc}</td>
                  </tr>)}
              </tbody>
            </table>
          </div>
        </Accordion>)}
    </AccordionGroup>;
};

Use ROS2 actions for long-running tasks with feedback and cancellation.

## Action Interface

<RosActionsInterface />

## When to use an action

Actions are useful when execution takes time and you need progress updates, cancellation, and a final result (for example navigation goals or manipulation routines). For one-shot RPC, use [Services](/software/ros2/services); for continuous streams, use [Topics](/software/ros2/topics).

## Quick commands

```bash  theme={null}
ros2 action list
ros2 action list -t
ros2 action info <action_name>
```

## Send goal examples

### Navigate to a pose

```bash  theme={null}
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: 1.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}" \
  --feedback
```

### Execute a learned manipulation behavior

```bash  theme={null}
ros2 action send_goal /execute_behavior brain_messages/action/ExecuteBehavior \
  "{behavior_name: pick_socks, behavior_config: \"{}\"}" \
  --feedback
```

### Execute a skill (primitive)

```bash  theme={null}
ros2 action send_goal /execute_primitive brain_messages/action/ExecutePrimitive \
  "{primitive_type: wave, inputs: \"{}\"}" \
  --feedback
```

<CardGroup cols={2}>
  <Card title="Navigation Stack" href="/software/ros2/navigation-stack">
    Planner/controller details and navigation runtime behavior.
  </Card>

  <Card title="Manipulation Stack" href="/software/ros2/manipulation-stack">
    Behavior execution and manipulation runtime details.
  </Card>
</CardGroup>


---

## Navigation Stack

_Source: https://docs.innate.bot/software/ros2/navigation-stack.md_

# Navigation Stack

MARS navigation is built on Nav2 plus MARS-specific wrappers.

## What to know

* `/cmd_vel` drives base motion
* `/odom` and `/scan` are core for localization and obstacle avoidance
* App navigation modes map to ROS2-level behavior mode changes

## Validate navigation signals

```bash  theme={null}
ros2 topic echo /odom
ros2 topic echo /scan
```

For mode behavior from the app side, see [Capabilities](/robots/mars/capabilities).


---

## Manipulation Stack

_Source: https://docs.innate.bot/software/ros2/manipulation-stack.md_

# Manipulation Stack

MARS manipulation combines arm interfaces, controllers, and learned policy execution.

## What to know

* Arm state is exposed through joint-state topics
* Motion commands can be sent through arm services/interfaces
* Learned manipulation policies are deployed as skills in the higher-level stack

## Useful checks

```bash  theme={null}
ros2 topic echo /joint_states
ros2 topic echo /mars/arm/state
```

For high-level usage, see [Capabilities](/robots/mars/capabilities).


---

## Debugging

_Source: https://docs.innate.bot/software/ros2/debugging.md_

# Debugging

Use SSH + tmux + ROS2 CLI to debug quickly on robot.

## Basic workflow

1. SSH into MARS.
2. Attach to runtime session with `tmux attach`.
3. Inspect active nodes, topics, and logs.

## Useful commands

```bash  theme={null}
ros2 node list
ros2 topic list
ros2 service list
ros2 doctor
```

For hardware/runtime issue patterns, see [Troubleshooting](/robots/mars/troubleshooting).

For visualization workflows (RViz and Foxglove Bridge), see [ROS2 Overview](/software/ros2-core#visualization).


---

# Training & Policy Development

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

# Support

## Contact / Discord

_Source: https://docs.innate.bot/support/contact-discord.md_

# Contact / Discord

Need help from the team?

* Discord: [Join the Innate community](https://discord.com/invite/KtkyT97kc7)
* Email: [axel@innate.bot](mailto:axel@innate.bot)

When reporting an issue, include:

* robot ID
* software version
* exact error message
* what you were doing right before the issue


---

# API Reference

## OpenAPI Specification

_Source: https://docs.innate.bot/api-reference/openapi.json_

The full OpenAPI JSON is not inlined here — fetch it directly from the URL above for the machine-readable API schema.
