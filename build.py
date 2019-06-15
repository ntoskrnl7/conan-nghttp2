#!/usr/bin/env python
# -*- coding: utf-8 -*-


import copy
from bincrafters import build_template_default

if __name__ == "__main__":

    builder = build_template_default.get_builder()

    for item in copy.copy(builder.items):
        if item.settings["compiler"] == "Visual Studio" or True:
            new_options = copy.copy(item.options)
            new_options["nghttp2:with_app"] = False
            builder.add(settings=item.settings, options=new_options,
                        env_vars=item.env_vars, build_requires=item.build_requires)

    builder.run()
