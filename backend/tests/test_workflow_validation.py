import pytest
from fastapi import HTTPException

from app.api.workflows import Graph, validate_graph


def test_workflow_graph_accepts_registered_foundation_nodes() -> None:
    graph = Graph(
        nodes=[
            {"id": "in", "type": "input"},
            {"id": "approval", "type": "approval"},
            {"id": "out", "type": "output"},
        ],
        edges=[{"from": "in", "to": "approval"}, {"from": "approval", "to": "out"}],
    )
    validate_graph(graph)


def test_workflow_graph_rejects_unregistered_node() -> None:
    graph = Graph(
        nodes=[{"id": "in", "type": "input"}, {"id": "x", "type": "shell"}, {"id": "out", "type": "output"}],
        edges=[{"from": "in", "to": "x"}, {"from": "x", "to": "out"}],
    )
    with pytest.raises(HTTPException, match="no registrados"):
        validate_graph(graph)


@pytest.mark.parametrize(
        ("node", "message"),
    [
        ({"id": "request", "type": "http"}, "requiere url"),
        ({"id": "read", "type": "file_read"}, "requiere path"),
        ({"id": "write", "type": "file_write"}, "requiere path"),
        ({"id": "wait", "type": "delay"}, "requiere seconds"),
        ({"id": "wait", "type": "delay", "seconds": 301}, "entre 0 y 300"),
        ({"id": "loop", "type": "loop"}, "requiere items_field"),
        ({"id": "loop", "type": "loop", "items_field": "items", "max_iterations": 1001}, "entre 1 y 1000"),
    ],
)
def test_workflow_graph_requires_safe_node_configuration(
    node: dict[str, object], message: str
) -> None:
    graph = Graph(
        nodes=[{"id": "in", "type": "input"}, node, {"id": "out", "type": "output"}],
        edges=[{"from": "in", "to": str(node["id"])}, {"from": str(node["id"]), "to": "out"}],
    )
    with pytest.raises(HTTPException, match=message):
        validate_graph(graph)


def test_workflow_graph_accepts_bounded_delay() -> None:
    graph = Graph(
        nodes=[
            {"id": "in", "type": "input"},
            {"id": "wait", "type": "delay", "seconds": 1},
            {"id": "out", "type": "output"},
        ],
        edges=[{"from": "in", "to": "wait"}, {"from": "wait", "to": "out"}],
    )
    validate_graph(graph)


def test_workflow_graph_accepts_bounded_loop() -> None:
    graph = Graph(
        nodes=[
            {"id": "in", "type": "input"},
            {"id": "loop", "type": "loop", "items_field": "items", "max_iterations": 3},
            {"id": "out", "type": "output"},
        ],
        edges=[{"from": "in", "to": "loop"}, {"from": "loop", "to": "out"}],
    )
    validate_graph(graph)
