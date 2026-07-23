from pathlib import Path


EXPECTED_VERSIONS = {
    "numpy": "2.0.2",
    "nnunetv2": "2.8.1",
    "optuna": "4.4.0",
}


def read_constraints(path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "==" not in line:
            continue

        package, version = line.split("==", maxsplit=1)
        versions[package.strip()] = version.strip()

    return versions


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    constraints_path = root / "constraints.txt"

    if not constraints_path.exists():
        raise FileNotFoundError("constraints.txt does not exist.")

    actual = read_constraints(constraints_path)
    errors: list[str] = []

    for package, expected_version in EXPECTED_VERSIONS.items():
        actual_version = actual.get(package)

        if actual_version != expected_version:
            errors.append(
                f"{package}: expected={expected_version}, actual={actual_version}"
            )
        else:
            print(f"PASS: {package}=={actual_version}")

    if errors:
        raise RuntimeError(
            "Fixed dependency version check failed:\n"
            + "\n".join(f"- {error}" for error in errors)
        )


if __name__ == "__main__":
    main()
