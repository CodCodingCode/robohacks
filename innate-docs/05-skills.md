# Skills

> Code-defined and policy-defined skills — the building blocks agents use to act. Includes all robot interfaces (body, navigation, state) and example skills.

> Source: https://docs.innate.bot · mirrored 2026-04-11 · MARS OS 0.4.5

## Contents

**Skills**
- [Skills Overview](#skills-overview)
- [Manual Triggering](#manual-triggering)
- [Policy-Defined Skills](#policy-defined-skills)
- [Code-Defined Skills](#code-defined-skills)

**Robot Interfaces (Code-Defined Skills)**
- [Body Control Interfaces](#body-control-interfaces)
- [Navigation Interfaces](#navigation-interfaces)
- [Robot State](#robot-state)
- [Digital Skills](#digital-skills)
- [Physical Skill Examples](#physical-skill-examples)

---

# Skills

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

# Robot Interfaces (Code-Defined Skills)

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
