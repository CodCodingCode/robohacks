from agents.recon_agent import ReconAgent


def test_recon_agent_exposes_recon_skill_and_microphone_input():
    agent = ReconAgent()

    assert agent.id == "recon_agent"
    assert agent.display_name == "Recon Agent"
    assert agent.get_skills() == ["recon_movement"]
    assert agent.get_inputs() == ["micro"]
    assert "approach_detected_threat" in agent.get_prompt()
    assert "approach_object" in agent.get_prompt()
