"""
Interactive and Command-Line Interface for ImageAgent.
Built with Rich terminal styling, real-time generation spinners,
and Vector SVG Logo generation capabilities.
"""

import sys
import os
import argparse

# Force UTF-8 encoding on Windows console to prevent UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

try:
    from .agent import ImageAgent
except ImportError:
    from agent import ImageAgent

console = Console(force_terminal=True, legacy_windows=False)


def print_banner():
    banner_text = (
        "[bold cyan]ImageAgent Autonomous Studio[/bold cyan]\n"
        "[dim]Multi-Model Parallel Image Generation & Vector SVG Logo Engine[/dim]\n"
        "[dim cyan]Powered by Gemini 3.1 Flash Lite & Hugging Face ZeroGPU[/dim cyan]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def display_results(manifest: dict):
    console.print()
    console.print(Panel(
        f"[bold green]Original Prompt:[/bold green] {manifest['original_prompt']}\n\n"
        f"[bold magenta]Gemini Enhanced Prompt:[/bold magenta]\n[italic]{manifest['enhanced_prompt']}[/italic]",
        title="[bold]Prompt Engineering Results[/bold]",
        border_style="magenta"
    ))

    # Check for SVG Logo output
    svg_info = manifest.get("svg_logo")
    if svg_info and svg_info.get("success"):
        console.print(Panel(
            f"[bold cyan]Vector SVG File:[/bold cyan] {svg_info.get('svg_path')}\n"
            f"[bold yellow]Source Engine:[/bold yellow] {svg_info.get('source')}\n"
            f"[bold green]Rasterized PNG Reference:[/bold green] {svg_info.get('png_reference_path', 'None')}\n"
            f"[dim]Lossless vector precision with clean geometric paths, gradients, and 0 degradation.[/dim]",
            title="[bold cyan][Vector SVG Logo Generated][/bold cyan]",
            border_style="cyan"
        ))

    table = Table(title="Generated Artwork & Model Manifest", border_style="bright_blue", show_header=True)
    table.add_column("Model / Engine", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Duration", justify="right")
    table.add_column("Saved File Path", style="dim")

    for item in manifest.get("results", []):
        model = item.get("model", "Unknown")
        status = "[green]SUCCESS[/green]" if item.get("success") else "[red]FAILED[/red]"
        dur = f"{item.get('duration_seconds', 0)}s"
        path = item.get("file_path") or item.get("error", "Error")
        table.add_row(model, status, dur, str(path))

    console.print(table)
    console.print(
        f"\n[bold green]Complete![/bold green] Generated {manifest['successful_images']}/{len(manifest['results'])} "
        f"assets in {manifest['total_duration_seconds']}s."
    )
    if "manifest_path" in manifest:
        console.print(f"[dim]Session manifest: {manifest['manifest_path']}[/dim]\n")


def run_pipeline(
    prompt: str,
    reference_image: Optional[str] = None,
    models: Optional[List[str]] = None,
    no_enhance: bool = False,
    generate_svg: bool = False,
    use_svg_as_reference: bool = False,
    use_cloudflare: bool = False,
    wordmark: Optional[str] = None
):
    agent = ImageAgent()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        task1 = progress.add_task("[cyan]Initializing pipeline...", total=None)

        def callback(event, data):
            if event == "generating_svg":
                progress.update(task1, description=f"[cyan]Synthesizing vector SVG logo...")
            elif event == "svg_completed":
                src = data.get("source", "engine")
                progress.console.print(f" [cyan][+][/cyan] Vector SVG synthesized via [bold]{src}[/bold]")
            elif event == "enhancing_prompt":
                progress.update(task1, description=f"[cyan]Enhancing prompt with Gemini 3.1 Flash Lite...")
            elif event == "dispatching_models":
                progress.update(task1, description=f"[yellow]Dispatching parallel generation to {len(data)} models...")
            elif event == "dispatching_cloudflare":
                progress.update(task1, description=f"[cyan]Dispatching to Cloudflare Workers AI edge GPUs...")
            elif event == "completed":
                progress.console.print(f" [green][OK][/green] Completed: [bold]{data}[/bold]")
            elif event == "failed":
                progress.console.print(f" [red][X][/red] Failed: [bold]{data}[/bold]")

        manifest = agent.run(
            user_prompt=prompt,
            reference_image_path=reference_image,
            models=models,
            enhance=not no_enhance,
            generate_svg=generate_svg,
            use_svg_as_reference=use_svg_as_reference,
            use_cloudflare=use_cloudflare,
            wordmark=wordmark,
            progress_callback=callback
        )

    display_results(manifest)


def interactive_mode():
    print_banner()
    while True:
        try:
            prompt = Prompt.ask("\n[bold yellow]Enter image / logo prompt[/bold yellow] (or 'exit' to quit)")
            if prompt.strip().lower() in ["exit", "quit", "q"]:
                console.print("[dim]Goodbye![/dim]")
                break
            if not prompt.strip():
                continue

            is_logo = Confirm.ask("Is this a Logo / Icon / Vector badge?", default=False)
            use_svg_ref = False
            if is_logo:
                use_svg_ref = Confirm.ask("Pass SVG as structural reference to diffusion models for 3D textures?", default=True)

            ref_img = None
            if not is_logo:
                ref_img = Prompt.ask("[dim]Reference image path (optional, press Enter to skip)[/dim]", default="")
                ref_img = ref_img.strip() if ref_img.strip() else None

            use_enhance = Confirm.ask("Enhance prompt with Gemini?", default=True)

            run_pipeline(
                prompt=prompt,
                reference_image=ref_img,
                no_enhance=not use_enhance,
                generate_svg=is_logo,
                use_svg_as_reference=use_svg_ref
            )
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Exiting.[/dim]")
            break


def main():
    parser = argparse.ArgumentParser(description="ImageAgent: Autonomous Multi-Model Image & Vector Logo Generator")
    parser.add_argument("prompt", nargs="?", help="Text prompt for image or logo generation")
    parser.add_argument("-r", "--reference", help="Path to reference image for image-to-image editing")
    parser.add_argument("-m", "--models", nargs="+", help="Specific model Space IDs to use")
    parser.add_argument("--svg", "--logo", action="store_true", dest="svg", help="Generate standalone vector SVG logo")
    parser.add_argument("--svg-reference", action="store_true", help="Generate SVG and pass as reference to diffusion models")
    parser.add_argument("--cf", "--cloudflare", action="store_true", dest="cloudflare", help="Generate image via Cloudflare Workers AI edge GPUs")
    parser.add_argument("--wordmark", type=str, default=None, help="Typeset a clean typographic wordmark/title onto the generated image")
    parser.add_argument("--no-enhance", action="store_true", help="Skip Gemini prompt enhancement")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive studio mode")

    args = parser.parse_args()

    if args.interactive or not args.prompt:
        interactive_mode()
    else:
        print_banner()
        run_pipeline(
            prompt=args.prompt,
            reference_image=args.reference,
            models=args.models,
            no_enhance=args.no_enhance,
            generate_svg=args.svg or args.svg_reference,
            use_svg_as_reference=args.svg_reference,
            use_cloudflare=args.cloudflare,
            wordmark=args.wordmark
        )


if __name__ == "__main__":
    main()
