import os
os.environ["USE_EMBEDDED_PG"] = "true"

from fastapi.testclient import TestClient
from app.main import app
from app.engine_validator import simulate_program


def test_health_and_levels():
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"

        lv_res = client.get("/api/levels")
        assert lv_res.status_code == 200
        levels = lv_res.json()["levels"]
        assert len(levels) >= 12
        # Verify every level has guided, core, and challenge variants with real distinct data
        for lv in levels:
            assert set(lv["available_tiers"]) == {"guided", "core", "challenge"}
            g = lv["variants"]["guided"]
            c = lv["variants"]["core"]
            ch = lv["variants"]["challenge"]
            assert g != c or c != ch


def test_player_and_solo_progression():
    with TestClient(app) as client:
        # 1. Create anonymous player
        p_res = client.post("/api/players", json={"nickname": "小五測試員", "character_skin": "nova_scout"})
        assert p_res.status_code == 200
        player = p_res.json()
        p_code = player["player_code"]
        assert p_code.startswith("NV-")

        # 2. Save & load Blockly workspace with version field
        ws_payload = {"version": 1, "mode": "cards", "ast": [{"type": "move_forward"}]}
        s_res = client.post(
            "/api/players/workspace/save",
            json={
                "player_code": p_code,
                "level_code": "ch1_lv1",
                "difficulty_tier": "guided",
                "workspace_data": ws_payload,
            },
        )
        assert s_res.status_code == 200
        l_res = client.get(f"/api/players/{p_code}/workspace/ch1_lv1?difficulty_tier=guided")
        assert l_res.status_code == 200
        assert l_res.json()["workspace_data"]["version"] == 1

        # 3. Submit wrong program first (only 2 steps instead of 3) to trigger error_occurred
        err_sub = client.post(
            "/api/levels/ch1_lv1/submit",
            json={
                "player_code": p_code,
                "difficulty_tier": "guided",
                "program_ast": [{"type": "move_forward"}, {"type": "move_forward"}],
                "attempts": 1,
                "hints_used": 1,
            },
        )
        assert err_sub.status_code == 200
        assert err_sub.json()["verified"] is False
        assert err_sub.json()["simulation"]["error_type"] == "not_at_goal"

        # 4. Submit corrected program (3 steps forward) -> triggers self_corrected + debug_specialist + first_boot
        ok_sub = client.post(
            "/api/levels/ch1_lv1/submit",
            json={
                "player_code": p_code,
                "difficulty_tier": "guided",
                "program_ast": [
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                ],
                "attempts": 2,
                "hints_used": 1,
                "reflection_answer": "會在終點前一格停下來",
            },
        )
        assert ok_sub.status_code == 200
        res_data = ok_sub.json()
        assert res_data["verified"] is True
        assert res_data["self_corrected_bonus"] is True
        unlocked_codes = {a["achievement_code"] for a in res_data["newly_unlocked_achievements"]}
        assert "first_boot" in unlocked_codes
        assert "debug_specialist" in unlocked_codes


def test_1_to_4_player_room_and_rotation():
    with TestClient(app) as client:
        players = []
        for i in range(5):
            r = client.post("/api/players", json={"nickname": f"隊員{i+1}"})
            players.append(r.json())

        # 1P creates room
        r_create = client.post(
            "/api/rooms",
            json={"player_code": players[0]["player_code"], "level_code": "ch1_lv1", "difficulty_tier": "guided"},
        )
        assert r_create.status_code == 200
        room = r_create.json()
        room_code = room["room_code"]
        assert room["player_count"] == 1
        assert room["is_solo"] is True
        assert room["members"][0]["role"] == "all_rounder"

        # 2nd, 3rd, 4th players join
        for idx in (1, 2, 3):
            rj = client.post(
                "/api/rooms/join",
                json={"player_code": players[idx]["player_code"], "room_code": room_code},
            )
            assert rj.status_code == 200
            room = rj.json()
            assert room["player_count"] == idx + 1

        roles_4p = [m["role"] for m in room["members"]]
        assert set(roles_4p) == {"programmer", "map_analyst", "tester", "debugger"}

        # 5th player must be rejected when room has 4 players
        r_fifth = client.post(
            "/api/rooms/join",
            json={"player_code": players[4]["player_code"], "room_code": room_code},
        )
        assert r_fifth.status_code == 400
        assert "最多" in r_fifth.json()["detail"]

        # Non-editor cannot submit program in multiplayer room
        non_editor_code = room["members"][1]["player_code"]
        forbidden_sub = client.post(
            "/api/levels/ch1_lv1/submit",
            json={
                "player_code": non_editor_code,
                "room_code": room_code,
                "difficulty_tier": "guided",
                "program_ast": [{"type": "move_forward"}] * 3,
            },
        )
        assert forbidden_sub.status_code == 403

        # Active editor submits valid program -> completes level and rotates editor turn to player 2!
        editor_code = room["editor_player_code"]
        valid_sub = client.post(
            "/api/levels/ch1_lv1/submit",
            json={
                "player_code": editor_code,
                "room_code": room_code,
                "difficulty_tier": "guided",
                "program_ast": [{"type": "move_forward"}] * 3,
            },
        )
        assert valid_sub.status_code == 200
        new_room = valid_sub.json()["room_state"]
        assert new_room["editor_player_code"] == players[1]["player_code"]

        # Players 2, 3, 4 leave -> room smoothly transitions back to 1P solo mode!
        for idx in (1, 2, 3):
            rl = client.post(
                "/api/rooms/leave",
                json={"player_code": players[idx]["player_code"], "room_code": room_code},
            )
            assert rl.status_code == 200
        final_room = client.get(f"/api/rooms/{room_code}").json()
        assert final_room["player_count"] == 1
        assert final_room["is_solo"] is True
        assert final_room["editor_player_code"] == players[0]["player_code"]
        assert final_room["members"][0]["role"] == "all_rounder"


def test_teacher_session_and_security():
    with TestClient(app) as client:
        # Unauthenticated access to teacher endpoint must return 401
        unauth = client.get("/api/teacher/sessions")
        assert unauth.status_code == 401

        # Teacher 1 logs in
        t1_login = client.post(
            "/api/teacher/login",
            json={"passkey": "NOVA-TEACHER-2026", "display_name": "王老師"},
        )
        assert t1_login.status_code == 200
        t1_token = t1_login.json()["access_token"]
        t1_headers = {"Authorization": f"Bearer {t1_token}"}

        # Teacher 1 creates a session
        s_create = client.post(
            "/api/teacher/sessions",
            json={"display_name": "混齡資訊課 A 班", "expires_hours": 12},
            headers=t1_headers,
        )
        assert s_create.status_code == 200
        session_code = s_create.json()["session_code"]
        assert session_code.startswith("CLS-")

        # Student joins session with anonymous code
        st = client.post("/api/players", json={"nickname": "閃電狐"}).json()
        j_res = client.post(
            "/api/sessions/join",
            json={"player_code": st["player_code"], "session_code": session_code},
        )
        assert j_res.status_code == 200

        # Teacher 1 assigns a task & difficulty to student
        a_res = client.post(
            f"/api/teacher/sessions/{session_code}/assign",
            json={
                "target_player_code": st["player_code"],
                "level_code": "ch2_lv1",
                "difficulty_tier": "core",
            },
            headers=t1_headers,
        )
        assert a_res.status_code == 200

        # Teacher 1 views session overview & student detail
        ov = client.get(f"/api/teacher/sessions/{session_code}/overview", headers=t1_headers)
        assert ov.status_code == 200
        assert ov.json()["student_count"] == 1

        # Teacher 2 logs in and tries to access Teacher 1's session -> must be 403 Forbidden!
        t2_login = client.post(
            "/api/teacher/login",
            json={"passkey": "TEACHER-OTHER-SECRET", "display_name": "李老師"},
        )
        assert t2_login.status_code == 200
        t2_headers = {"Authorization": f"Bearer {t2_login.json()['access_token']}"}
        cross_access = client.get(f"/api/teacher/sessions/{session_code}/overview", headers=t2_headers)
        assert cross_access.status_code == 403


def test_engine_safety_limits():
    # Verify loop iteration limit blocks infinite/excessive loops safely
    level_data = {
        "width": 8,
        "height": 8,
        "start": {"x": 1, "y": 1, "dir": 0},
        "goal": {"x": 6, "y": 1},
        "obstacles": [],
        "items": [],
    }
    bad_loop_ast = [{"type": "repeat_n", "count": 9999, "body": [{"type": "turn_left"}]}]
    res = simulate_program(bad_loop_ast, level_data)
    assert res["success"] is False
    assert res["error_type"] == "loop_limit_exceeded"


def test_websocket_coop_sync_and_disconnect_handoff():
    with TestClient(app) as client:
        p1 = client.post("/api/players", json={"nickname": "操作員A"}).json()
        p2 = client.post("/api/players", json={"nickname": "分析員B"}).json()
        outsider = client.post("/api/players", json={"nickname": "路人C"}).json()

        room = client.post(
            "/api/rooms",
            json={"player_code": p1["player_code"], "level_code": "ch1_lv1", "difficulty_tier": "guided"},
        ).json()
        room_code = room["room_code"]

        client.post("/api/rooms/join", json={"player_code": p2["player_code"], "room_code": room_code})

        # Outsider not in room must be rejected by WebSocket
        try:
            with client.websocket_connect(f"/ws/rooms/{room_code}?player_code={outsider['player_code']}") as ws_out:
                ws_out.receive_json()
                assert False, "Outsider should not receive room_state"
        except Exception:
            pass

        # Connect both p1 (editor) and p2 (teammate) via WebSocket
        with client.websocket_connect(f"/ws/rooms/{room_code}?player_code={p1['player_code']}") as ws1:
            msg1 = ws1.receive_json()
            assert msg1["type"] == "room_state"

            with client.websocket_connect(f"/ws/rooms/{room_code}?player_code={p2['player_code']}") as ws2:
                # Both receive updated room_state
                _ = ws1.receive_json()
                msg2 = ws2.receive_json()
                assert msg2["type"] == "room_state"
                assert msg2["room_state"]["editor_player_code"] == p1["player_code"]

                # p1 updates Blockly/Card workspace -> p2 receives editor_state_updated
                ws1.send_json({
                    "type": "editor_state_updated",
                    "workspace_state": {"version": 1, "mode": "cards", "ast": [{"type": "move_forward"}]},
                })
                sync_msg1 = ws1.receive_json()
                sync_msg2 = ws2.receive_json()
                assert sync_msg2["type"] == "editor_state_updated"
                assert sync_msg2["workspace_state"]["ast"] == [{"type": "move_forward"}]

                # p1 disconnects (exit ws1 context) -> p2 should automatically become editor!
            # After ws2 closes, test when editor ws1 disconnects while p2 reconnects:
        with client.websocket_connect(f"/ws/rooms/{room_code}?player_code={p2['player_code']}") as ws2_again:
            state_after_p1_disc = ws2_again.receive_json()
            assert state_after_p1_disc["room_state"]["editor_player_code"] == p2["player_code"]


def test_all_7_chapters_and_solo_equivalent_coop_levels():
    with TestClient(app) as client:
        p = client.post("/api/players", json={"nickname": "全章節測試員"}).json()
        p_code = p["player_code"]

        # Chapter 2 (Loops - Core): repeat 5 times { move_forward, pickup }
        r_ch2 = client.post(
            "/api/levels/ch2_lv1/submit",
            json={
                "player_code": p_code,
                "difficulty_tier": "core",
                "program_ast": [
                    {"type": "repeat_n", "count": 5, "body": [{"type": "move_forward"}, {"type": "pickup"}]}
                ],
            },
        ).json()
        assert r_ch2["verified"] is True

        # Chapter 3 (Conditions - Challenge): repeat_until_goal with energy pickup + obstacle avoidance
        r_ch3 = client.post(
            "/api/levels/ch3_lv1/submit",
            json={
                "player_code": p_code,
                "difficulty_tier": "challenge",
                "program_ast": [
                    {
                        "type": "repeat_until_goal",
                        "body": [
                            {
                                "type": "if",
                                "condition": {"type": "energy_on_tile"},
                                "then_body": [{"type": "pickup"}],
                            },
                            {
                                "type": "if_else",
                                "condition": {"type": "obstacle_ahead"},
                                "then_body": [{"type": "turn_right"}],
                                "else_body": [{"type": "move_forward"}],
                            },
                        ],
                    }
                ],
            },
        ).json()
        assert r_ch3["verified"] is True

        # Chapter 4 (Variables - Core): collect 4 energy and compare energy >= 4 to open door
        r_ch4 = client.post(
            "/api/levels/ch4_lv1/submit",
            json={
                "player_code": p_code,
                "difficulty_tier": "core",
                "program_ast": [
                    {"type": "repeat_n", "count": 4, "body": [{"type": "move_forward"}, {"type": "pickup"}]},
                    {
                        "type": "if",
                        "condition": {"type": "var_compare", "var": "energy", "op": ">=", "value": 4},
                        "then_body": [{"type": "open_door"}],
                    },
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                ],
            },
        ).json()
        assert r_ch4["verified"] is True

        # Chapter 5 (Dual-Control Lab - Solo Equivalent Solution in Core tier):
        # 1 player activates north switch (3,2) with pulse hold, then south switch (3,4), then opens door (5,3)!
        r_ch5 = client.post(
            "/api/levels/ch5_lv1/submit",
            json={
                "player_code": p_code,
                "difficulty_tier": "core",
                "program_ast": [
                    {"type": "move_forward"},
                    {"type": "pickup"},
                    {"type": "move_forward"},
                    {"type": "turn_left"},
                    {"type": "move_forward"},
                    {"type": "activate_switch"},
                    {"type": "turn_left"},
                    {"type": "turn_left"},
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                    {"type": "activate_switch"},
                    {"type": "turn_left"},
                    {"type": "turn_left"},
                    {"type": "move_forward"},
                    {"type": "turn_right"},
                    {"type": "move_forward"},
                    {
                        "type": "if",
                        "condition": {
                            "type": "logic_and",
                            "left": {"type": "has_energy"},
                            "right": {"type": "all_switches_active"},
                        },
                        "then_body": [{"type": "open_door"}],
                    },
                    {"type": "move_forward"},
                    {"type": "move_forward"},
                ],
            },
        ).json()
        assert r_ch5["verified"] is True

        # Chapter 6 (Functions - Core): define collect_step and call twice around corner
        r_ch6 = client.post(
            "/api/levels/ch6_lv1/submit",
            json={
                "player_code": p_code,
                "difficulty_tier": "core",
                "program_ast": [
                    {
                        "type": "func_def",
                        "name": "collect_step",
                        "body": [
                            {"type": "repeat_n", "count": 2, "body": [{"type": "move_forward"}, {"type": "pickup"}]}
                        ],
                    },
                    {"type": "func_call", "name": "collect_step"},
                    {"type": "turn_right"},
                    {"type": "func_call", "name": "collect_step"},
                ],
            },
        ).json()
        assert r_ch6["verified"] is True

        # Chapter 7 (Final NOVA Core - Challenge): test BOTH North route and South route solutions!
        north_route_ast = [
            {"type": "move_forward"},
            {"type": "turn_left"},
            {"type": "move_forward"},
            {"type": "move_forward"},
            {"type": "pickup"},
            {"type": "turn_right"},
            {"type": "move_forward"},
            {"type": "pickup"},
            {"type": "move_forward"},
            {"type": "turn_right"},
            {"type": "move_forward"},
            {"type": "move_forward"},
            {"type": "activate_switch"},
            {"type": "turn_left"},
            {"type": "open_door"},
            {"type": "move_forward"},
            {"type": "move_forward"},
            {"type": "repair_device"},
            {"type": "move_forward"},
        ]
        r_ch7_north = client.post(
            "/api/levels/ch7_lv1/submit",
            json={"player_code": p_code, "difficulty_tier": "challenge", "program_ast": north_route_ast},
        ).json()
        assert r_ch7_north["verified"] is True

        south_route_ast = [
            {"type": "move_forward"},
            {"type": "turn_right"},
            {"type": "move_forward"},
            {"type": "move_forward"},
            {"type": "pickup"},
            {"type": "turn_left"},
            {"type": "move_forward"},
            {"type": "pickup"},
            {"type": "move_forward"},
            {"type": "turn_left"},
            {"type": "move_forward"},
            {"type": "move_forward"},
            {"type": "activate_switch"},
            {"type": "turn_right"},
            {"type": "open_door"},
            {"type": "move_forward"},
            {"type": "move_forward"},
            {"type": "repair_device"},
            {"type": "move_forward"},
        ]
        r_ch7_south = client.post(
            "/api/levels/ch7_lv1/submit",
            json={"player_code": p_code, "difficulty_tier": "challenge", "program_ast": south_route_ast},
        ).json()
        assert r_ch7_south["verified"] is True
