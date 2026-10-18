# Third party notices

pyrapidparser is released under the BSD 3-Clause license (see `LICENSE`). It is not
affiliated with, endorsed by or sponsored by ABB. ABB, RAPID, IRC5, RobotStudio and the
names of the ABB robots are trademarks of ABB; they are used only to say which language
and which robots the project is about.

## Code derived from pycparser

`plyparser.py`, `_ast_gen.py`, `_rapid_ast.cfg` and parts of the lexer and of `ast_gen.py`
come from [pycparser](https://github.com/eliben/pycparser) by Eli Bendersky (BSD license):

    Copyright (C) 2008-2012, Eli Bendersky
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification,
    are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list
      of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this
      list of conditions and the following disclaimer in the documentation and/or other
      materials provided with the distribution.
    * Neither the name of Eli Bendersky nor the names of its contributors may be used
      to endorse or promote products derived from this software without specific prior
      written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
    EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
    OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
    SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
    TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
    BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
    ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
    DAMAGE.

## Dependencies (not distributed with the project)

| Package | License |
| ------- | ------- |
| [PLY](https://github.com/dabeaz/ply) | BSD |
| [Pinocchio](https://github.com/stack-of-tasks/pinocchio) (`pin`) | BSD-2-Clause |
| numpy, scipy | BSD |
| [xacro](https://github.com/ros/xacro) | BSD |
| [MeshCat](https://github.com/meshcat-dev/meshcat-python) | MIT |
| development: hatch (MIT), mypy (MIT), ruff (MIT), pytest (MIT), cadquery (Apache-2.0), manifold3d (Apache-2.0) | |

All of them can be combined with a BSD-3-Clause project. gmsh (GPL), used only by the
optional script `models/irb460_110_240/build_cad.py`, is not a dependency: it is
installed by the user, and nothing of it is distributed.

## Robot models

- `third_party/abb` (git submodule): the ROS-Industrial package
  [ros-industrial/abb](https://github.com/ros-industrial/abb), Apache-2.0 and BSD-3-Clause
  (see the repository). It is a separate repository: it is not copied into the wheel.
- `models/`: the models written for this project (URDF and JSON) are under the license
  of the project. The CAD files and the manuals of ABB are copyright of ABB, they are not
  in the repository and are not distributed (`doc/abb/official/` and `models/*/cad/` are
  ignored by git).
