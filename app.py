from dashboard import (
    _argument_data,
    _collapse_dialogical_explanation,
    _layered_positions,
    _restore_extension,
    _serialize_extension,
    app as dash_app,
    argument_graph,
    argument_statuses,
    build_premise_options,
    dialogical_graph,
    load_argument_state,
    server,
    update_options,
)

app = server

if __name__ == "__main__":
    dash_app.run_server(debug=False)
