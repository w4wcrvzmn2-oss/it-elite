"""CLI entry point for green-planner."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from app import __version__
from app.config import load_config
from app.debug_viz import generate_debug_map
from app.dxf.reader import inspect_dxf
from app.dxf.writer import validate_output_dxf
from app.interpretation.generator import format_report_summary, load_interpretation
from app.pipeline import PipelineError, run_pipeline

app = typer.Typer(
    name="green-planner",
    help="Automatic green planting layout from DXF geobase",
    add_completion=False,
)
console = Console()


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """Green Planner CLI."""
    if version:
        console.print(f"green-planner {__version__}")
        raise typer.Exit()


@app.command("inspect")
def inspect_cmd(
    input: Path = typer.Option(..., "--input", "-i", help="Input DXF file"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
) -> None:
    """Inspect DXF file: layers, entities, bounding box."""
    _setup_logging(verbose)
    try:
        info = inspect_dxf(input)
    except Exception as e:
        console.print(f"[red]ERROR:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"\n[bold]DXF Inspection:[/bold] {info['filepath']}")
    console.print(f"File size: {info['file_size_bytes']:,} bytes")
    console.print(f"Total entities: {info['total_entities']}")
    console.print(f"Entity types: {', '.join(info['entity_types'])}")
    if info.get("units"):
        u = info["units"]
        console.print(
            f"Units: {u['units_name']} (INSUNITS={u['insunits']}, "
            f"scale_hint={u['scale_hint']})"
        )
    if info["bounding_box"]:
        bb = info["bounding_box"]
        console.print(f"Bounding box: ({bb[0]:.2f}, {bb[1]:.2f}) - ({bb[2]:.2f}, {bb[3]:.2f})")
        if info.get("extent_width") and info.get("extent_height"):
            console.print(
                f"Extent: {info['extent_width']} × {info['extent_height']} "
                f"({info['units']['units_name'] if info.get('units') else 'units'})"
            )

    table = Table(title="Layers")
    table.add_column("Layer", style="cyan")
    table.add_column("Entities", justify="right")
    table.add_column("Types")
    table.add_column("BBox")

    for name, layer in sorted(info["layers"].items()):
        bbox_str = ""
        if layer["bounding_box"]:
            b = layer["bounding_box"]
            bbox_str = f"({b[0]:.1f},{b[1]:.1f})-({b[2]:.1f},{b[3]:.1f})"
        table.add_row(
            name,
            str(layer["number_of_entities"]),
            ", ".join(layer["entity_types"]),
            bbox_str,
        )

    console.print(table)


@app.command("process")
def process_cmd(
    input: Path = typer.Option(..., "--input", "-i", help="Input DXF file"),
    output: Path = typer.Option(..., "--output", "-o", help="Output DXF file"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config YAML file"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
) -> None:
    """Process DXF and generate planting layout."""
    _setup_logging(verbose)

    if not input.exists():
        console.print(f"[red]ERROR:[/red] Input file not found: {input}")
        raise typer.Exit(1)

    console.print(f"[bold]Processing:[/bold] {input}")
    try:
        result = run_pipeline(input, output, config)
    except PipelineError as e:
        console.print(f"[red]ERROR:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]ERROR:[/red] {e}")
        logging.exception("Unexpected error")
        raise typer.Exit(1)

    console.print(f"\n[green]Done![/green] Processing time: {result.processing_time_sec:.2f}s")
    console.print(f"  Output DXF:       {result.output_dxf}")
    console.print(f"  Interpretation:   {result.interpretation_json}")
    console.print(f"  Run report:       {result.run_report_json}")
    console.print(f"  Accepted:         {len(result.accepted_plantings)}")
    console.print(f"  Rejected:         {len(result.rejected_plantings)}")


@app.command("validate")
def validate_cmd(
    input: Path = typer.Option(..., "--input", "-i", help="Output DXF to validate"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config YAML file"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
) -> None:
    """Validate output DXF has planting layers."""
    _setup_logging(verbose)
    cfg = load_config(config)

    try:
        result = validate_output_dxf(input, cfg)
    except Exception as e:
        console.print(f"[red]ERROR:[/red] {e}")
        raise typer.Exit(1)

    if result["valid"]:
        console.print(f"[green]Valid[/green] — {result['planting_entities']} planting entities found")
    else:
        console.print("[red]Invalid[/red] — no planting entities found")
        raise typer.Exit(1)

    console.print(f"Planting layers: {', '.join(result['planting_layers_present'])}")


@app.command("report")
def report_cmd(
    input: Path = typer.Option(..., "--input", "-i", help="Interpretation JSON file"),
) -> None:
    """Display interpretation report summary."""
    if not input.exists():
        console.print(f"[red]ERROR:[/red] File not found: {input}")
        raise typer.Exit(1)

    try:
        report = load_interpretation(input)
    except Exception as e:
        console.print(f"[red]ERROR:[/red] {e}")
        raise typer.Exit(1)

    console.print(format_report_summary(report))


@app.command("debug")
def debug_cmd(
    input: Path = typer.Option(..., "--input", "-i", help="Input DXF file"),
    output: Path = typer.Option(..., "--output", "-o", help="Output PNG file"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config YAML file"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose logging"),
) -> None:
    """Generate debug visualization map."""
    _setup_logging(verbose)

    if not input.exists():
        console.print(f"[red]ERROR:[/red] Input file not found: {input}")
        raise typer.Exit(1)

    try:
        generate_debug_map(input, output, config)
    except Exception as e:
        console.print(f"[red]ERROR:[/red] {e}")
        logging.exception("Debug visualization failed")
        raise typer.Exit(1)

    console.print(f"[green]Debug map saved:[/green] {output}")


def main_entry() -> None:
    """Entry point for setuptools."""
    app()


if __name__ == "__main__":
    main_entry()
