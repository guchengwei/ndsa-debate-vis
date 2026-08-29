import json

import pytest

import app as ndsa


def selectable_claims():
    return list(dict.fromkeys(option["value"] for option in ndsa.update_options()))


def test_dash_shell_serves():
    client = ndsa.server.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"NDSA Debate Visualization" in response.data


def test_extension_round_trip_preserves_argument_state():
    extension, _ = ndsa.load_argument_state("~a>~d")
    restored = ndsa._restore_extension(ndsa._serialize_extension(extension))

    assert restored.arguments == extension.arguments
    assert restored.relation == extension.relation
    assert restored.grounded == extension.grounded
    assert restored.ideal == extension.ideal


@pytest.mark.parametrize("claim", selectable_claims())
def test_every_selectable_claim_renders_a_stable_argument_map(claim):
    extension, separated_premises = ndsa.load_argument_state(claim)

    assert extension.arguments
    assert isinstance(separated_premises, dict)

    positions_a, layers_a = ndsa._layered_positions(extension)
    positions_b, layers_b = ndsa._layered_positions(extension)

    assert positions_a == positions_b
    assert layers_a == layers_b
    assert set(positions_a) == set(extension.arguments)

    figure = ndsa.argument_graph(extension)
    payload = json.loads(figure.to_json())

    assert payload["data"]
    assert payload["layout"]["dragmode"] == "pan"
    assert payload["layout"]["xaxis"]["visible"] is False
    assert payload["layout"]["yaxis"]["visible"] is False


def test_default_argument_opens_dialogical_explanation():
    extension, separated_premises = ndsa.load_argument_state("~a>~d")
    figure, statuses = ndsa.dialogical_graph(extension, 0)
    payload = json.loads(figure.to_json())

    assert payload["data"]
    assert statuses

    _, conclusion, _, claim_text = ndsa._argument_data(extension, 0)
    options = ndsa.build_premise_options(separated_premises, conclusion, claim_text)
    assert options
    assert all(json.loads(option["value"])["conclusion"] == conclusion for option in options)
