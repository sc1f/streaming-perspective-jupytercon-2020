# Streaming, cross-sectional data visualization in Jupyterlab with Perspective and Apache Arrow

Notebooks, slides, and a fully interactive `perspective-python` and `perspective-workspace` example for my upcoming [JupyterCon2020](http://jupytercon.com/) _Jupyter community: tools and practices_ talk.

### Abstract

Many data visualization libraries are built with static data in mind, where everything is known before the visualization is created. Analyzing data streams in real-time, however, is a crucial part of many industries. Combining JupyterLab’s ease-of-use and flexibility with Perspective, a high-performance streaming data visualization library, users can rapidly prototype, analyze, and visualize results from a multitude of data sources both live and static.
Using real-time stock quotes from the IEX Cloud API, Junyuan Tan demonstrates how Perspective can be used to visualize streaming data, combine real-time information with analysis and data points from various sources, and export data snapshots using Apache Arrow, without leaving the Jupyter Notebook.

Attendees will learn:

* How to accumulate data from a streaming datasource in a Perspective table
* Visualizing, charting and analyzing data in real-time using PerspectiveWidget
* Chaining multiple Perspective tables to create your own augmented, streaming data sources
* Streaming, exporting, and storing data in the Apache Arrow format, and reintegrating that data back into Perspective

A working knowledge of Python is recommended but not required.

### Running the Example

#### Notebooks

You'll need to have [`perspective-python`](https://perspective.finos.org/docs/md/installation.html#python) installed, along with `pyarrow==0.16.0`, `pandas`, `numpy`, and `tornado`.

- `perspective_basics.ipynb` contains a walkthrough of the Perspective library.
- `datasources.ipynb` contain my implementation of non-blocking, multi-process & multi-threaded datasources that interface with the [IEX Cloud API](https://iexcloud.io/)
- `jupytercon.ipynb` contains the main talk notebook where I join the streaming and static datasources with Perspective.

#### Tornado Example

To run the Tornado example, run `python3 tornado_server.py` and navigate to `localhost:8888`.
