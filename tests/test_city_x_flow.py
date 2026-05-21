import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace


APP_DIR = Path(__file__).resolve().parents[1] / "examples" / "swm_roleplay"
APP_PATH = APP_DIR / "streamlit_app.py"


def _load_app_module():
    module_name = "city_x_streamlit_app_test"
    if module_name in sys.modules:
        del sys.modules[module_name]
    sys.path.insert(0, str(APP_DIR))
    try:
        spec = importlib.util.spec_from_file_location(module_name, APP_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


class FakeState(dict):
    __getattr__ = dict.get

    def __setattr__(self, key, value):
        self[key] = value


@contextmanager
def _noop_spinner(_msg=""):
    yield


class FakeStreamlit:
    def __init__(self):
        self.session_state = FakeState()

    def rerun(self):
        return None

    def spinner(self, msg=""):
        return _noop_spinner(msg)


def _make_stakeholder(app, role_id, name):
    thresholds = {
        dim: f"{name} threshold for {app.SECTION_LABELS[dim]}"
        for dim in app.NEGOTIABLE_DIMENSIONS
    }
    return SimpleNamespace(
        id=role_id,
        display_name=name,
        public_profile=SimpleNamespace(
            title=f"{name} title",
            primary_goal=f"{name} primary goal",
            hidden_goal="",
            background=f"{name} background",
            opening_position=f"{name} opening position",
        ),
        negotiation=SimpleNamespace(
            minimum_thresholds=thresholds,
            minimum_requirements=[f"{name} minimum requirement"],
            red_lines=[f"{name} red line"],
        ),
        private_info=[],
    )


def _make_fake_runtime(app):
    stakeholders = [
        _make_stakeholder(app, "national_government", "National Government"),
        _make_stakeholder(app, "municipal_government", "Municipal Government"),
        _make_stakeholder(app, "private_sector_company", "Private Sector Company"),
        _make_stakeholder(app, "ngo_civil_society", "NGO / Civil Society"),
        _make_stakeholder(app, "community_member", "Community Leader"),
        _make_stakeholder(app, "informal_sector_worker", "Informal Sector Worker"),
    ]

    class FakeScenario:
        def __init__(self):
            self.stakeholders = stakeholders
            self.proposal_dimensions = [
                {"id": "core_action", "label": "Core action"},
                {"id": "timeline", "label": "Timeline"},
                *[
                    {"id": dim, "label": app.SECTION_LABELS[dim]}
                    for dim in app.NEGOTIABLE_DIMENSIONS
                ],
            ]
            self.narrative = {
                "public_crisis": "Test crisis",
                "deadline_days": 60,
                "if_no_agreement": "A unilateral decision follows.",
            }
            self.events = [{"id": "test_event", "announcement": "A test event changes the pressure."}]

        def stakeholder_map(self):
            return {stakeholder.id: stakeholder for stakeholder in self.stakeholders}

    dialog = SimpleNamespace(turns=[], notes={})
    game = SimpleNamespace(
        scenario=FakeScenario(),
        human_roles=["community_member"],
        moderator_role="national_government",
        dialog=dialog,
        active_proposal=None,
        final_votes={},
        outcome=None,
    )
    return SimpleNamespace(game=game, agents={role_id: object() for role_id in app.ROUND1_ORDER})


def _fake_roleplay_engine_module():
    def create_roleplay_runtime(session):
        return session

    def create_working_proposal(game, proposer_role_id, dimensions):
        proposal = SimpleNamespace(
            proposer_role_id=proposer_role_id,
            dimensions=dict(dimensions),
            version=1,
            amendment_history=[],
        )
        game.active_proposal = proposal
        return proposal

    def amend_working_proposal(game, proposer_role_id, amendments, note=""):
        if game.active_proposal is None:
            create_working_proposal(game, proposer_role_id, amendments)
        else:
            game.active_proposal.dimensions.update(amendments)
            game.active_proposal.version += 1
            game.active_proposal.amendment_history.append(
                {"proposer_role_id": proposer_role_id, "note": note, "amendments": dict(amendments)}
            )
        return game.active_proposal

    def record_final_vote(game, role_id, label):
        game.final_votes[role_id] = SimpleNamespace(role_id=role_id, label=label)

    def resolve_game_outcome(game):
        endorsements = sum(1 for vote in game.final_votes.values() if vote.label == "yes")
        game.outcome = SimpleNamespace(
            outcome="win" if endorsements >= 4 else "lose",
            endorsements=endorsements,
            detail="Proposal passed." if endorsements >= 4 else "Proposal failed.",
        )

    return SimpleNamespace(
        create_roleplay_runtime=create_roleplay_runtime,
        create_working_proposal=create_working_proposal,
        amend_working_proposal=amend_working_proposal,
        record_final_vote=record_final_vote,
        resolve_game_outcome=resolve_game_outcome,
    )


def test_init_game_uses_local_city_x_paths(monkeypatch):
    app = _load_app_module()
    app.st = FakeStreamlit()
    app.ensure_state()
    app._moderator_text = lambda *args, **kwargs: "Test moderator notice"

    captured = {}
    fake_runtime = _make_fake_runtime(app)

    def fake_load_and_prepare_roleplay_session(scenario_path, rules_path, human_roles, model, think):
        captured["scenario_path"] = scenario_path
        captured["rules_path"] = rules_path
        captured["human_roles"] = human_roles
        captured["model"] = model
        captured["think"] = think
        return fake_runtime

    monkeypatch.setitem(
        sys.modules,
        "sdialog.roleplay",
        SimpleNamespace(load_and_prepare_roleplay_session=fake_load_and_prepare_roleplay_session),
    )
    monkeypatch.setitem(sys.modules, "sdialog.roleplay_engine", _fake_roleplay_engine_module())

    app.init_game("vertexai:gemini-2.5-flash", "community_member", False)

    assert captured["scenario_path"] == app.local_city_x_scenario_path()
    assert captured["rules_path"] == app.local_city_x_rules_path()
    assert app.st.session_state.stage == "role_reveal"
    assert app.st.session_state.runtime is fake_runtime
    assert app.st.session_state.proposal_form["core_action"]
    assert app.st.session_state.proposal_form["timeline"]


def test_round_flow_reaches_outcome_with_stubbed_ai(monkeypatch):
    app = _load_app_module()
    app.st = FakeStreamlit()
    app.ensure_state()
    app.st.session_state.runtime = _make_fake_runtime(app)
    app.st.session_state.stage = "round2_bids"
    app.st.session_state.proposal_form = dict(app.PREFILLED_DIMENSIONS)

    engine_module = _fake_roleplay_engine_module()
    monkeypatch.setitem(sys.modules, "sdialog.roleplay_engine", engine_module)
    app._moderator_text = lambda *args, **kwargs: "Moderator notice"
    app._synthesize_dimension_proposal = lambda dim: app.st.session_state.proposal_form.get(dim, "")
    app._sync_proposal_to_game = lambda: None
    app._generate_round2_bid = lambda role_id, *_args: f"{role_id} priority bid"
    app._generate_ai_reaction = lambda dim, _move, _text: (
        "municipal_government",
        f"Reaction on {app.SECTION_LABELS[dim]}",
    )
    app._generate_ai_flags = lambda dims: {
        role_id: {
            dim: {
                "flag": "accept_with_condition" if dim == "livelihoods" else "accept",
                "reason": f"{role_id} comment on {dim}",
            }
            for dim in dims
        }
        for role_id in app.ai_roles()
    }
    app._generate_ai_final_votes = lambda: {
        role_id: {"vote": "conditional_endorsement", "reason": "Good enough to proceed."}
        for role_id in app.ai_roles()
    }
    app._evaluate_goal_achievement = lambda: {
        role_id: {"rating": "partially_achieved", "explanation": "Some goals were met."}
        for role_id in app.ROUND1_ORDER
    }

    texts = {
        "financing": "Emergency fund with national and operator contributions.",
        "community_health_protections": "Independent monitoring and clinics within 30 days.",
        "livelihoods": "Worker transition income and protected access for 24 months.",
        "monitoring_and_enforcement": "Independent oversight, monthly reports, and penalties.",
    }

    app._do_collect_bids(
        "community_health_protections",
        "Health pressure is immediate.",
        "My priority is Community health protections because health pressure is immediate.",
    )
    assert app.st.session_state.round2_human_bid is not None
    assert len(app.st.session_state.round2_ai_bids) == len(app.ai_roles())

    app.st.session_state.stage = "round2_table"
    for dim in app.NEGOTIABLE_DIMENSIONS:
        app._submit_dimension_move(dim, texts[dim])
        app._advance_round2_dimension()

    assert app.st.session_state.stage == "round2_flagging"

    app._do_lock_flags({dim: "accept" for dim in app.NEGOTIABLE_DIMENSIONS})
    assert app.st.session_state.stage == "round2_results"
    assert app.st.session_state.round3_dimensions == [
        "financing",
        "livelihoods",
        "monitoring_and_enforcement",
    ]

    app.st.session_state.stage = "round3"
    while app.st.session_state.stage == "round3":
        dim = app._current_round3_dimension()
        app._submit_round3_move(dim, texts[dim])
        app._advance_round3_dimension()

    assert app.st.session_state.stage == "final_vote"

    app._do_final_vote("unconditional_endorsement")
    assert app.st.session_state.stage == "outcome"
    assert app.game().outcome is not None
    assert app.game().outcome.outcome == "win"
    assert len(app.st.session_state.final_vote_labels) == len(app.ROUND1_ORDER)
    assert len(app.st.session_state.goal_evaluations) == len(app.ROUND1_ORDER)
