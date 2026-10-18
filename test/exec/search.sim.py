"""The simulated cell of search.mod: the probe touches a surface at x = 450 mm."""


def setup(world):
    def probe(world):
        # the sensor goes high when the flange passes the surface
        tcp = world.flange().translation
        world.set_signal("diProbe", 1 if tcp[0] >= 0.45 else 0)

    world.on_step(probe)
