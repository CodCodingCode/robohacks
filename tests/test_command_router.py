from slam.command_router import route_command


def test_scan_routes_to_recon_skill():
    route = route_command("sweep the area")

    assert route.kind == "skill"
    assert route.skill.action == "scan_room"


def test_forward_routes_to_recon_skill_with_distance_clamp():
    route = route_command("move forward 9 meters")

    assert route.kind == "skill"
    assert route.skill.action == "move_forward"
    assert route.skill.distance_m == 1.0


def test_approach_device_routes_to_threat_skill():
    route = route_command("approach the device")

    assert route.kind == "skill"
    assert route.skill.action == "approach_detected_threat"


def test_approach_named_object_routes_to_object_skill():
    route = route_command("inspect the backpack")

    assert route.kind == "skill"
    assert route.skill.action == "approach_object"
    assert route.skill.target == "backpack"


def test_defusal_manipulation_is_blocked():
    route = route_command("cut red wire")

    assert route.kind == "error"
    assert "Defusal manipulation is not available" in route.text


def test_autonomy_enable_is_blocked():
    route = route_command("autonomy on")

    assert route.kind == "error"
    assert "Autonomous switching is disabled" in route.text


def test_unknown_command_falls_back_to_free_form_executor():
    route = route_command("turn slightly toward the nearest chair")

    assert route.kind == "fallback"
