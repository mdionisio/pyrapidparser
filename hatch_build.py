"""Hatch build hook: generate rapid_ast.py from _rapid_ast.cfg before packaging."""

import os
import subprocess
import sys
from typing import Any

from hatchling.builders.config import BuilderConfig
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class GenerateASTHook(BuildHookInterface[BuilderConfig]):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        subprocess.check_call([sys.executable, "_ast_gen.py"], cwd=self.root)
        if self.target_name == "wheel":
            build_data["force_include"][os.path.join(self.root, "rapid_ast.py")] = "rapid_ast.py"
