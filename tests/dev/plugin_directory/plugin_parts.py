from midgard.dev import plugins


@plugins.register
def plugin_default():
    return "default"


@plugins.register
def plugin_next():
    return "next"


@plugins.register_named("named_part")
def plugin_named():
    return "named"


@plugins.register
def plugin_last():
    return "last"
