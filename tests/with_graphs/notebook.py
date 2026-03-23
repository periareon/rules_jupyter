# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Graph Rendering Test
# Validates that matplotlib and plotly graphs survive the report pipeline.

# %%
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 50)
plt.figure(figsize=(8, 4))
plt.plot(x, np.sin(x))
plt.title("Matplotlib Test")
plt.show()

# %%
import plotly.graph_objects as go

fig = go.Figure(data=go.Scatter(x=list(range(10)), y=[i**2 for i in range(10)]))
fig.update_layout(title="Plotly Test")
fig.show()
