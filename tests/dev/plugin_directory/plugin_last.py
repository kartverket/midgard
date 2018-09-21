from midgard.dev import plugins


@plugins.register_ordered(10)
def plugin_last():
    return "last"
