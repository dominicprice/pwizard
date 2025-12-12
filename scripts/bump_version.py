import ast
import toml
import sys


def is_assignment_to(stmt: ast.stmt, to: str) -> ast.Assign | None:
    """returns an ast.Assign statement if the given statment is an
    assignment to the given variable name"""
    if not isinstance(stmt, ast.Assign):
        return None
    if len(stmt.targets) != 1:
        return None
    target = stmt.targets[0]
    if not isinstance(target, ast.Name):
        return None
    if target.id != to:
        return None
    return stmt


def parse_version(version_string: str) -> tuple[int, int, int]:
    """returns a three-tuple of a version from a version string of the
    form e.g. 1.2.3"""
    try:
        version = tuple(int(i) for i in version_string.split("."))
    except ValueError:
        raise ValueError("invalid version string: " + version_string)
    if len(version) == 0:
        raise ValueError("empty version string")

    if len(version) == 1:
        return (version[0], 0, 0)
    elif len(version) == 2:
        return (version[0], version[1], 0)
    elif len(version) == 3:
        return (version[0], version[1], version[2])
    raise ValueError("invalid version string: " + version_string)


def stringify_version(ver: tuple[int, int, int]):
    """returns a string from a version tuple"""
    return ".".join(str(v) for v in ver)


if __name__ == "__main__":
    # load pyproject.toml
    with open("pyproject.toml") as f:
        pyproject = toml.load(f)

    # get the current version number
    ver = parse_version(pyproject["project"]["version"])

    # get new version number from arguments
    new_ver = ver
    force = False
    for arg in sys.argv[1:]:
        if arg == "-f":
            force = True
        elif arg == "-p":
            new_ver = (new_ver[0], new_ver[1], new_ver[2] + 1)
        elif arg == "-m":
            new_ver = (new_ver[0], new_ver[1] + 1, 0)
        elif arg == "-M":
            new_ver = (new_ver[0] + 1, 0, 0)
        else:
            new_ver = parse_version(arg)

    # early returns for versions <= current version
    if not force:
        if new_ver == ver:
            print("already at version", stringify_version(ver))
            exit(0)
        elif new_ver < ver and not force:
            print(
                "not downgrading from",
                stringify_version(ver),
                "to",
                stringify_version(new_ver),
                "- provide the -f flag to force downgrade",
            )
            exit(1)

    # update the value in the toml file
    pyproject["project"]["version"] = stringify_version(new_ver)

    # read the __init__.py file
    with open("src/typedre/__init__.py") as f:
        code = ast.parse(f.read())

    # update the value in the __init__ file
    for stmt in code.body:
        if vi := is_assignment_to(stmt, "__version_info__"):
            vi.value = ast.Tuple([ast.Constant(i) for i in new_ver])
        elif v := is_assignment_to(stmt, "__version__"):
            v.value = ast.Constant(stringify_version(new_ver))

    # write all new versions
    with open("pyproject.toml", "w") as f:
        toml.dump(pyproject, f)
    with open("src/typedre/__init__.py", "w") as f:
        f.write(ast.unparse(code))
