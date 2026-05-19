from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parent

CLEAN_DIRS = [
    "tmp",
    "__pycache__",
    ".pytest_cache",
    "playwright-report",
    "test-results",
    "moki_logo_blend",
    "moki_seed_previews",
    "moki_style_case",
]

KEEP_DIRS = [
    "moki_logo_source",
    "moki_publish_package",
    "moki_upscaled_repaired",
    "dist",
]


def is_inside_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


def remove_dir(path: Path) -> bool:
    if not is_inside_root(path):
        raise RuntimeError(f"Refusing to delete outside project: {path}")
    if not path.exists():
        return False
    shutil.rmtree(path)
    return True


def main() -> None:
    removed = []
    for name in CLEAN_DIRS:
        path = ROOT / name
        if remove_dir(path):
            removed.append(name)

    print("Cleanup complete.")
    if removed:
        print("Removed:")
        for name in removed:
            print(f"- {name}")
    else:
        print("Nothing to remove.")

    print("Kept:")
    for name in KEEP_DIRS:
        if (ROOT / name).exists():
            print(f"- {name}")


if __name__ == "__main__":
    main()
