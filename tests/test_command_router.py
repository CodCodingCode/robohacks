from slam.command_router import route_command


def test_scan_falls_back_to_brain_agent():
    route = route_command("sweep the area")

    assert route.kind == "fallback"
    assert route.text == "Forward to brain agent"


def test_forward_falls_back_to_brain_agent():
    route = route_command("move forward 9 meters")

    assert route.kind == "fallback"


def test_approach_device_falls_back_to_brain_agent():
    route = route_command("approach the device")

    assert route.kind == "fallback"


def test_approach_named_object_falls_back_to_brain_agent():
    route = route_command("inspect the backpack")

    assert route.kind == "fallback"


def test_move_towards_person_falls_back_to_brain_agent():
    route = route_command("Move towards person")

    assert route.kind == "fallback"


def test_defusal_manipulation_falls_back_to_brain_agent():
    route = route_command("cut red wire")

    assert route.kind == "fallback"


def test_autonomy_enable_is_blocked():
    route = route_command("autonomy on")

    assert route.kind == "error"
    assert "Autonomous switching is disabled" in route.text


def test_stop_routes_locally():
    route = route_command("stop")

    assert route.kind == "stop"
    assert route.text == "Holding position"


def test_say_routes_locally():
    route = route_command("say hello")

    assert route.kind == "speak"
    assert route.text == "hello"


def test_unknown_command_falls_back_to_brain_agent():
    route = route_command("turn slightly toward the nearest chair")

    assert route.kind == "fallback"
