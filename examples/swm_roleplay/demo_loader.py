import argparse

from sdialog.roleplay import (
    default_city_x_game_rules_path,
    default_city_x_scenario_path,
    load_and_prepare_roleplay_session,
    load_roleplay_game_rules,
    load_roleplay_scenario,
)


def main():
    parser = argparse.ArgumentParser(description="Inspect or prepare an SWM role-play scenario pack.")
    parser.add_argument("--scenario", default=default_city_x_scenario_path(), help="Path to a scenario-pack JSON file.")
    parser.add_argument("--rules", default=default_city_x_game_rules_path(), help="Path to a hidden game-rules JSON file.")
    parser.add_argument(
        "--human-role",
        action="append",
        default=[],
        help="Stakeholder id reserved for a human player. Repeat to add multiple roles.",
    )
    parser.add_argument(
        "--build-agents",
        action="store_true",
        help="Instantiate AI agents for non-human roles using the configured SDialog model.",
    )
    parser.add_argument("--model", default=None, help="Optional model override, for example ollama:qwen2.5:14b.")
    args = parser.parse_args()

    scenario = load_roleplay_scenario(args.scenario)
    rules = load_roleplay_game_rules(args.rules)
    print(f"Scenario: {scenario.title}")
    print(f"Scenario ID: {scenario.scenario_id}")
    print(f"Moderator role: {getattr(scenario.moderator_stakeholder(), 'id', 'none')}")
    print("Opening order:", ", ".join(scenario.opening_turn_order()))
    print("Win threshold:", rules.outcome_thresholds.get("win", {}).get("minimum_endorsements", "unknown"))
    print()
    print("Stakeholders:")
    for stakeholder in scenario.stakeholders:
        print(f"- {stakeholder.id}: {stakeholder.display_name}")

    if not args.build_agents:
        return

    try:
        session = load_and_prepare_roleplay_session(
            args.scenario,
            rules_path=args.rules,
            human_roles=args.human_role,
            model=args.model,
        )
    except Exception as exc:
        print()
        print("Could not build AI agents.")
        print(f"Reason: {exc}")
        print("Make sure Ollama is running and the configured model is available, or pass --model explicitly.")
        return

    print()
    print("Prepared session:")
    print("Human roles:", ", ".join(session.human_roles) or "none")
    print("AI roles:", ", ".join(session.ai_roles) or "none")
    print("Built agents:", ", ".join(session.agents.keys()) or "none")


if __name__ == "__main__":
    main()
