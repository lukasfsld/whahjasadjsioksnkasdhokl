import streamlit.components.v1 as components
import os

_component_func = components.declare_component(
    "body_editor",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
)

def body_editor(params, height=480, key=None):
    """Render the SDF body editor and return two screenshot captures (front + side) as base64 PNGs."""
    result = _component_func(params=params, height=height, key=key, default=None)
    return result
