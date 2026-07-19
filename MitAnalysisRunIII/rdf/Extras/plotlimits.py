#!/usr/bin/env python3

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline


def read_limits(filename):
    """Read the five-column EFT limit input file."""

    data = np.loadtxt(filename, comments="#")

    if data.ndim == 1:
        data = data.reshape(1, -1)

    if data.shape[1] != 5:
        raise ValueError(
            "Input file must contain five columns:\n"
            "cutoff exp_mTmjj obs_mTmjj exp_m01mjj obs_m01mjj"
        )

    return {
        "cutoff": data[:, 0],
        "exp_mTmjj": data[:, 1],
        "obs_mTmjj": data[:, 2],
        "exp_m01mjj": data[:, 3],
        "obs_m01mjj": data[:, 4],
    }


def make_bspline(x, y, number_of_points=500):
    """
    Create a B-spline curve while ignoring zero values.

    Zero is treated as a missing value.
    """

    mask = np.isfinite(x) & np.isfinite(y) & (y != 0.0)

    x_valid = np.asarray(x[mask], dtype=float)
    y_valid = np.asarray(y[mask], dtype=float)

    order = np.argsort(x_valid)
    x_valid = x_valid[order]
    y_valid = y_valid[order]

    if len(x_valid) == 0:
        return None, None, None, None

    if len(x_valid) == 1:
        return x_valid, y_valid, x_valid, y_valid

    # Use cubic B-spline when at least four points are available.
    # For three points, use a quadratic B-spline.
    # For two points, use a straight line.
    degree = min(3, len(x_valid) - 1)

    x_smooth = np.linspace(
        x_valid.min(),
        x_valid.max(),
        number_of_points,
    )

    if degree == 1:
        y_smooth = np.interp(
            x_smooth,
            x_valid,
            y_valid,
        )
    elif degree == 3:
        spline = make_interp_spline(
            x_valid,
            y_valid,
            k=degree,
            bc_type="natural",
        )
        y_smooth = spline(x_smooth)
    else:
        spline = make_interp_spline(
            x_valid,
            y_valid,
            k=degree,
        )
        y_smooth = spline(x_smooth)

    return x_smooth, y_smooth, x_valid, y_valid


def draw_curve(ax, x, y, label, linestyle, marker):
    """Draw the B-spline line and the actual calculated points."""

    x_smooth, y_smooth, x_points, y_points = make_bspline(x, y)

    if x_smooth is None:
        return

    line, = ax.plot(
        x_smooth,
        y_smooth,
        linestyle=linestyle,
        linewidth=2.4,
        label=label,
    )

    ax.plot(
        x_points,
        y_points,
        linestyle="none",
        marker=marker,
        markersize=5,
        color=line.get_color(),
    )


def plot_limits(operator_name):
    input_file = Path(f"limits_{operator_name}.txt")

    if not input_file.exists():
        raise FileNotFoundError(
            f"Cannot find input file: {input_file}"
        )

    limits = read_limits(input_file)

    cutoff = limits["cutoff"]

    fig, ax = plt.subplots(figsize=(9, 7))

    # Red curves: m_jj × m_T
    draw_curve(
        ax,
        cutoff,
        limits["exp_mTmjj"],
        r"Expected, $m_{jj}\times m_T$",
        linestyle=":",
        marker="o",
    )

    draw_curve(
        ax,
        cutoff,
        limits["obs_mTmjj"],
        r"Observed, $m_{jj}\times m_T$",
        linestyle="-",
        marker="o",
    )

    # Blue curves: m_jj × m_01
    draw_curve(
        ax,
        cutoff,
        limits["exp_m01mjj"],
        r"Expected, $m_{jj}\times m_{01}$",
        linestyle=":",
        marker="s",
    )

    draw_curve(
        ax,
        cutoff,
        limits["obs_m01mjj"],
        r"Observed, $m_{jj}\times m_{01}$",
        linestyle="-",
        marker="s",
    )

    # Assign matching colors to expected and observed pairs.
    lines = ax.get_lines()

    # Each draw_curve creates one line and one marker object.
    lines[0].set_color("red")
    lines[1].set_color("red")

    lines[2].set_color("red")
    lines[3].set_color("red")

    lines[4].set_color("blue")
    lines[5].set_color("blue")

    lines[6].set_color("blue")
    lines[7].set_color("blue")

    ax.set_xlim(1000, 3000)
    ax.set_ylim(bottom=0.0)

    # Only show 1000, 2000 and 3000.
    ax.set_xticks([1000, 2000, 3000])

    ax.set_xlabel(
        r"Clipping cutoff $\Lambda_{\mathrm{cut}}$ [GeV]",
        fontsize=17,
    )

    ax.set_ylabel(
        rf"$|f_{{{operator_name}}}/\Lambda^4|$ [TeV$^{{-4}}$]",
        fontsize=17,
    )

    ax.tick_params(
        axis="both",
        labelsize=14,
        direction="in",
        top=True,
        right=False,
    )

    # CMS labels moved slightly downward.
    ax.text(
        0.00,
        1.015,
        "CMS",
        transform=ax.transAxes,
        fontsize=17,
        fontweight="bold",
        ha="left",
        va="bottom",
    )

    ax.text(
        0.085,
        1.015,
        "Work in progress",
        transform=ax.transAxes,
        fontsize=14,
        fontstyle="italic",
        ha="left",
        va="bottom",
    )

    ax.text(
        1.00,
        1.015,
        r"280 fb$^{-1}$ (13.6 TeV)",
        transform=ax.transAxes,
        fontsize=14,
        ha="right",
        va="bottom",
    )

    ax.legend(
        loc="upper right",
        frameon=False,
        fontsize=13,
        handlelength=3.0,
    )

    fig.tight_layout()

    output_base = f"limits_{operator_name}_vs_cutoff_bspline"

    fig.savefig(
        f"{output_base}.pdf",
        bbox_inches="tight",
    )

    fig.savefig(
        f"{output_base}.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Created: {output_base}.pdf")
    print(f"Created: {output_base}.png")


def main():
    parser = argparse.ArgumentParser(
        description="Plot EFT limits using B-spline interpolation."
    )

    parser.add_argument(
        "operator",
        help="Operator name, for example T0, T1, T2, S0, M0, M1 or M7",
    )

    args = parser.parse_args()

    plot_limits(args.operator)


if __name__ == "__main__":
    main()
