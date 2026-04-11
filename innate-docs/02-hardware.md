# Robot Hardware (MARS)

> Physical robot: sensors, arm, compute, calibration, battery, connectivity, extending, troubleshooting, maintenance.

> Source: https://docs.innate.bot · mirrored 2026-04-11 · MARS OS 0.4.5

## Contents

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

---

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
