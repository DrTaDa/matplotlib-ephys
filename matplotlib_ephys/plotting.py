"""Electrophysiology plotting functions"""
from decimal import Decimal
import matplotlib.pyplot as plt

from .style import *


def format_float(f):
    """Format a float to a string without trailing zeros.
    From: https://stackoverflow.com/questions/2440692/formatting-floats-without-trailing-zeros"""

    d = Decimal(str(f))
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()


def define_style(style="explore"):
    """Define the plotting style.

    Args:
        style (str or Style): if str, specifies the name of the style to use (amongst: "explore",
            "paper"). If Style, returns the Style object. Warning: these styles are different
            from the matplotlib styles.
    """

    if isinstance(style, str):
        if style == "explore":
            style = ExploreStyle()
        elif style == "paper":
            style = PaperStyle()
        else:
            raise ValueError("Unknown style: {}".format(style))

    return style


def get_n_plots(n_voltage_series, n_current_series, shared_axis):
    """Compute the number of plots to plot.

    Args:
        n_voltage_series (int): number of voltage traces.
        n_current_series (int): number of current traces.
        shared_axis (bool): are the voltage and current traces plotted on the same axis?
    """

    if shared_axis or not n_current_series:
        return n_voltage_series
    else:
        return n_voltage_series + n_current_series


def compute_figsize(n_plots, title, style):
    """Compute the figure size for a plot with n_voltage_series voltage traces and,
    optionally, n_current_series current traces.

    Args:
        n_plots (int): number of plots.
    """

    figsize = [6.4, 4.8 * n_plots]  # TODO: improve this formula

    # TODO: if scale bars I need to add space for them
    if style.scale_bars:
        figsize[0] += 1

    # TODO: if title I need to add space for it
    if title is not None:
        figsize[1] += 1. * style.title_fontsize

    # TODO: if spines, I need to add space for them
    if style.show_spines:
        figsize[0] += 1.
        figsize[1] += 1.

    return figsize


def get_text_bbox(text, axis, debug=False):
    """Get the bounding box of a text object in data coordinates"""

    axis.get_figure().canvas.draw()

    transf = axis.transData.inverted()
    bb = text.get_window_extent(renderer=axis.get_figure().canvas.get_renderer())
    bb_data = bb.transformed(transf)

    if debug:
        print("Bounding Box in data coordinates:", bb_data)
        axis.plot([bb_data.x0, bb_data.x1], [bb_data.y0, bb_data.y0], c="c0")
        axis.plot([bb_data.x0, bb_data.x1], [bb_data.y1, bb_data.y1], c="C0")
        axis.plot([bb_data.x0, bb_data.x0], [bb_data.y0, bb_data.y1], c="C0")
        axis.plot([bb_data.x1, bb_data.x1], [bb_data.y0, bb_data.y1], c="C0")

    return bb_data


def compute_scale_bar_length(axis, is_current=False, bar_length=0.15):
    """Compute the length of a scale bar.

    Args:
        axis (matplotlib axis): axis for which to compute the scale bar length.
        is_current (bool): is the scale bar for the current trace?
        bar_length (float): length of the scale bar as a fraction of the axis length.
    """

    valid_time_bar_length = [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
    valid_voltage_bar_length = [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100]
    valid_current_bar_length = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50]

    # Find the length of the time bar the closest to the valid lengths
    time_limit = axis.get_xlim()
    target_length = bar_length * (time_limit[1] - time_limit[0])
    time_bar_length = min(valid_time_bar_length, key=lambda x: abs(x - target_length))

    # Find the length of the voltage or current bar the closest to the valid lengths
    IV_limit = axis.get_ylim()
    target_length = bar_length * (IV_limit[1] - IV_limit[0])

    if is_current:
        IV_bar_length = min(valid_current_bar_length, key=lambda x: abs(x - target_length))
    else:
        IV_bar_length = min(valid_voltage_bar_length, key=lambda x: abs(x - target_length))

    return time_bar_length, IV_bar_length


def compute_scale_bar_position(axis, time_bar_length, is_current=False):
    """Compute the position of the scale bar.

    Args:
        axis (matplotlib axis): axis for which to compute the scale bar position.
        time_bar_length (float): length of the time scale bar.
        is_current (bool): is the scale bar for the current trace?
    """

    time_limit = axis.get_xlim()
    IV_limit = axis.get_ylim()

    x_pos = time_limit[0] - 1.2 * time_bar_length
    if is_current:
        y_pos = IV_limit[0] + 0.3 * (IV_limit[1] - IV_limit[0])
    else:
        y_pos = IV_limit[0]

    return x_pos, y_pos


def draw_scale_bars(axis, is_current=False, style="explore"):
    """Draw a ms and nA or mV scale bars on the axis

    Args:
        axis (matplotlib axis): axis on which to draw the scale bars.
        is_current (bool): if True, draw a nA scale bar instead of a mV scale bar.
        time_bar_length (float): length of the time scale bar in percentage of the x-axis length.
        IV_bar_length (float): length of the voltage or current scale bar in percentage of the
            y-axis height.
    """

    style = define_style(style)

    time_bar_length, IV_bar_length = compute_scale_bar_length(axis, is_current)
    scale_bar_origin = compute_scale_bar_position(axis, time_bar_length, is_current)

    # Draw the bars
    scale_bar_settings = dict(color="black", linewidth=1, clip_on=False)
    axis.plot(
        [scale_bar_origin[0], scale_bar_origin[0] + time_bar_length],
        [scale_bar_origin[1], scale_bar_origin[1]],
        **scale_bar_settings,
    )
    axis.plot(
        [scale_bar_origin[0], scale_bar_origin[0]],
        [scale_bar_origin[1], scale_bar_origin[1] + IV_bar_length],
        **scale_bar_settings,
    )

    # Add the labels at the origin of the bars
    time_label = axis.text(
        scale_bar_origin[0],
        scale_bar_origin[1],
        f'{format_float(time_bar_length)} ms',
        horizontalalignment="center",
        verticalalignment="bottom",
        fontsize=style.scale_bars_fontsize,
    )

    if is_current:
        iv_label = axis.text(
            scale_bar_origin[0],
            scale_bar_origin[1],
            f'{format_float(IV_bar_length)} nA',
            horizontalalignment="left",
            verticalalignment="center",
            fontsize=style.scale_bars_fontsize,
        )
    else:
        iv_label = axis.text(
            scale_bar_origin[0],
            scale_bar_origin[1],
            f'{format_float(IV_bar_length)} mV',
            horizontalalignment="left",
            verticalalignment="center",
            fontsize=style.scale_bars_fontsize,
        )

    # Move the labels such that they do not overlap with the scale bars
    text_height = get_text_bbox(time_label, axis).height
    time_label.set_position(
        (scale_bar_origin[0] + 0.5 * time_bar_length, scale_bar_origin[1] - 1.8 * text_height)
    )

    text_length = get_text_bbox(iv_label, axis).width
    iv_label.set_position(
        (scale_bar_origin[0] - 1.3 * text_length, scale_bar_origin[1] + 0.5 * IV_bar_length)
    )


def hide_spines(axis):
    """Hide the spines of an axis.

    Args:
        axis (matplotlib axis): axis for which to hide the spines.
    """

    for spine in axis.spines.values():
        spine.set_visible(False)

    axis.set_xticks([])
    axis.set_yticks([])


def plot_trace(
    time_series,
    voltage_series,
    current_series=None,
    title=None,
    axis=None,
    style="explore",
):
    """Plot a single electrophysiological trace (voltage and, optionally, current).

    Args:
        time_series (list or numpy.array): time series in ms.
        voltage_series (list or numpy.array): voltage series in mV.
        current_series (list or numpy.array): current series in nA.
        title (str): title of the plot.
        axis (axis or list of axis): matplotlib axis on which to plot.
        style (str or Style): if str, specifies the name of the style to use (amongst: "explore",
            "paper"). If Style, returns the Style object. Warning: these styles are different
            from the matplotlib styles.
    """

    style = define_style(style)

    n_plots = get_n_plots(
        n_voltage_series=1,
        n_current_series=1 if current_series is not None else 0,
        shared_axis=style.shared_axis
    )

    if axis is None:
        figsize = compute_figsize(n_plots=n_plots, title=title, style=style)
        fig, axis = plt.subplots(n_plots, 1, figsize=figsize)
    else:
        if len(axis) != n_plots:
            raise ValueError(
                "The number of axis provided is not the same as the number of series to plot."
            )
        if isinstance(axis, list):
            fig = axis[0].get_figure()
        else:
            fig = axis.get_figure()

    if current_series is not None:
        axis_current = axis if style.shared_axis else axis[0]
        axis_voltage = axis.twinx() if style.shared_axis else axis[-1]
    else:
        axis_voltage = axis
        axis_current = None

    if current_series is not None:
        axis_current.plot(time_series, current_series, color=style.current_color, alpha=style.current_alpha, linewidth=style.linewidth)
    axis_voltage.plot(time_series, voltage_series, color=style.voltage_color, alpha=style.voltage_alpha, linewidth=style.linewidth)

    # Set the limits of the axis to the limits of the data
    axis_voltage.set_xlim(time_series[0], time_series[-1])
    axis_voltage.set_ylim(voltage_series.min(), voltage_series.max())
    if current_series is not None:
        axis_current.set_xlim(time_series[0], time_series[-1])
        axis_current.set_ylim(current_series.min(), current_series.max())

    if not style.show_spines:
        hide_spines(axis_voltage)
        if axis_current:
            hide_spines(axis_current)

    if style.scale_bars:
        draw_scale_bars(axis_voltage, is_current=False, style=style)
        if axis_current:
            draw_scale_bars(axis_current, is_current=True, style=style)
    else:
        axis_current.set_xlabel("Time (ms)", fontsize=style.label_fontsize)
        axis_voltage.set_xlabel("Time (ms)", fontsize=style.label_fontsize)
        axis_current.set_ylabel("Current (nA)", fontsize=style.label_fontsize)
        axis_voltage.set_ylabel("Voltage (mV)", fontsize=style.label_fontsize)

    if title is not None:
        fig.suptitle(title, fontsize=style.title_fontsize)

    fig.tight_layout()

    return fig, axis