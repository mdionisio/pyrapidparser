"""The simulated cell of trigger.mod: it writes the position of the flange along x (mm,
in steps of 5 mm) when a signal changes."""


def setup(world):
    def changed(world, name, value):
        x = world.flange().translation[0] * 1000
        print("%s = %d at x = %d" % (name, value, 5 * round(x / 5)))

    world.on_signal(changed)
