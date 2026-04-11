# Agents

> Agents are portable applications that run on MARS. Includes agent definitions, starting agents, examples, and the Chess beta guides.

> Source: https://docs.innate.bot · mirrored 2026-04-11 · MARS OS 0.4.5

## Contents

- [Agents Overview](#agents-overview)
- [Agent Definitions](#agent-definitions)
- [Starting an Agent](#starting-an-agent)
- [Agent Examples](#agent-examples)
- [Chess Agent (Beta)](#chess-agent-beta)
- [Chessboard Calibration (Beta)](#chessboard-calibration-beta)

---

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
